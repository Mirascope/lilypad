"""Utility functions for OpenAI OpenTelemetry instrumentation.

This module provides helper functions for extracting and formatting OpenAI API
response data for telemetry purposes.
"""

# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Modifications copyright (C) 2025 Mirascope

import json
from typing import Any, ParamSpec

from openai import OpenAI, AsyncOpenAI
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionChunk,
    ChatCompletionMessage,
    ChatCompletionMessageParam,
    ChatCompletionMessageToolCallParam,
)
from opentelemetry.trace import Span, Tracer
from opentelemetry.util.types import AttributeValue
from openai.types.chat.chat_completion import Choice
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from . import _utils
from ..base import (
    BaseWrappers,
    create_sync_wrapper,
    create_async_wrapper,
)
from ..types import LLMOpenTelemetryMessage
from ..utils import (
    BaseMetadata,
    ChoiceBuffer,
    ChunkHandler,
    StreamWrapper,
    StreamProtocol,
    AsyncStreamWrapper,
    AsyncStreamProtocol,
    set_server_address_and_port,
)
from ...utils import json_dumps
from ..base.protocols import (
    SyncStreamHandler,
    AsyncStreamHandler,
    SyncCompletionHandler,
    AsyncCompletionHandler,
)


class OpenAIMetadata(BaseMetadata, total=False):
    """OpenAI-specific metadata extending BaseMetadata."""

    service_tier: str | None


class OpenAIChunkHandler(ChunkHandler[ChatCompletionChunk, OpenAIMetadata]):
    def extract_metadata(
        self, chunk: "ChatCompletionChunk", metadata: OpenAIMetadata
    ) -> None:
        """Extract metadata from a streaming chunk and update the metadata dictionary."""
        if not metadata.get("response_model") and hasattr(chunk, "model"):
            metadata["response_model"] = chunk.model
        if not metadata.get("response_id") and hasattr(chunk, "id"):
            metadata["response_id"] = chunk.id
        if not metadata.get("service_tier") and hasattr(chunk, "service_tier"):
            metadata["service_tier"] = chunk.service_tier
        if hasattr(chunk, "usage") and chunk.usage:
            if hasattr(chunk.usage, "completion_tokens"):
                metadata["completion_tokens"] = chunk.usage.completion_tokens
            if hasattr(chunk.usage, "prompt_tokens"):
                metadata["prompt_tokens"] = chunk.usage.prompt_tokens

    def process_chunk(
        self, chunk: ChatCompletionChunk, buffers: list[ChoiceBuffer]
    ) -> None:
        """Process a streaming chunk and update the choice buffers with content."""

        for choice in chunk.choices:
            # Ensure enough choice buffers
            while len(buffers) <= choice.index:
                buffers.append(ChoiceBuffer(len(buffers)))

            if choice.finish_reason:
                buffers[choice.index].finish_reason = choice.finish_reason

            if choice.delta.content is not None:
                buffers[choice.index].append_text_content(choice.delta.content)

            if choice.delta.tool_calls is not None:
                for tool_call in choice.delta.tool_calls:
                    buffers[choice.index].append_tool_call(tool_call)


def process_messages(span: Span, kwargs: dict[str, Any]) -> None:
    """Process and record input messages."""
    for message in kwargs.get("messages", []):
        set_message_event(span, message)


async def create_async_stream_wrapper(
    span: Span, stream: AsyncStreamProtocol[ChatCompletionChunk]
) -> AsyncStreamWrapper[ChatCompletionChunk, _utils.OpenAIMetadata]:
    """Create OpenAI-specific async stream wrapper."""
    return AsyncStreamWrapper(
        span=span,
        stream=stream,
        metadata=_utils.OpenAIMetadata(),
        chunk_handler=_utils.OpenAIChunkHandler(),
        cleanup_handler=_utils.default_openai_cleanup,
    )


def default_openai_cleanup(
    span: Span, metadata: OpenAIMetadata, buffers: list[ChoiceBuffer]
) -> None:
    """Set final span attributes and events from accumulated metadata and buffers."""
    attributes: dict[str, AttributeValue] = {}
    if response_model := metadata.get("response_model"):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_MODEL] = response_model
    if response_id := metadata.get("response_id"):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_ID] = response_id
    if prompt_tokens := metadata.get("prompt_tokens"):
        attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = prompt_tokens
    if completion_tokens := metadata.get("completion_tokens"):
        attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = completion_tokens
    if service_tier := metadata.get("service_tier"):
        attributes[gen_ai_attributes.GEN_AI_OPENAI_RESPONSE_SERVICE_TIER] = service_tier

    if finish_reasons := tuple(
        buffer.finish_reason for buffer in buffers if buffer.finish_reason is not None
    ):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons

    span.set_attributes(attributes)
    for index, choice in enumerate(buffers):
        message: dict[str, str | dict[str, str] | list[str]] = {"role": "assistant"}
        if choice.text_content:
            message["content"] = "".join(choice.text_content)
        if choice.tool_calls_buffers:
            tool_calls = []
            for tool_call in choice.tool_calls_buffers:
                if tool_call:
                    function = {
                        "name": tool_call.function_name,
                        "arguments": "".join(tool_call.arguments),
                    }
                    tool_call_dict = {
                        "id": tool_call.tool_call_id,
                        "type": "function",
                        "function": function,
                    }
                    tool_calls.append(tool_call_dict)
            message["tool_calls"] = tool_calls

        event_attributes: dict[str, AttributeValue] = {
            gen_ai_attributes.GEN_AI_SYSTEM: "openai",
            "index": index,
            "finish_reason": choice.finish_reason or "none",
            "message": json.dumps(message),
        }
        span.add_event("gen_ai.choice", attributes=event_attributes)


def get_tool_calls(
    message: ChatCompletionMessage | ChatCompletionMessageParam,
) -> list[ChatCompletionMessageToolCallParam] | None:
    """Returns tool calls extracted from a message object or dictionary."""

    if isinstance(message, dict):
        tool_calls = message.get("tool_calls")
    else:
        tool_calls = message.tool_calls

    if tool_calls is None:
        return None

    calls = []
    for tool_call in tool_calls:
        tool_call_dict = {}
        if isinstance(tool_call, dict):
            call_id = tool_call.get("id")
            tool_type = tool_call.get("type")
            if func := tool_call.get("function"):
                tool_call_dict["function"] = {}

                if name := func.get("name"):
                    tool_call_dict["function"]["name"] = name

                if arguments := func.get("arguments"):
                    tool_call_dict["function"]["arguments"] = arguments
        else:
            call_id = tool_call.id
            tool_type = tool_call.type
            if tool_type == "function" and hasattr(tool_call, "function"):
                function_attribute = getattr(tool_call, "function", None)
                if function_attribute:
                    tool_call_dict["function"] = function_attribute.model_dump(
                        mode="python"
                    )
        tool_call_dict["id"] = call_id
        tool_call_dict["type"] = tool_type
        calls.append(tool_call_dict)
    return calls


def set_message_event(span: Span, message: ChatCompletionMessageParam) -> None:
    """Add a message event to the span with appropriate attributes."""
    attributes = {
        gen_ai_attributes.GEN_AI_SYSTEM: gen_ai_attributes.GenAiSystemValues.OPENAI.value
    }
    role = message["role"]

    if role == "assistant" and (tool_calls := get_tool_calls(message)):
        attributes["tool_calls"] = json_dumps(tool_calls)

    if role == "tool" and (tool_call_id := message.get("tool_call_id")):
        attributes["id"] = tool_call_id

    if content := message.get("content"):
        if not isinstance(content, str):
            content = json_dumps(content)
        attributes["content"] = content

    span.add_event(
        f"gen_ai.{role}.message",
        attributes=attributes,
    )


def create_stream_wrapper(
    span: Span, stream: StreamProtocol[ChatCompletionChunk]
) -> StreamWrapper[ChatCompletionChunk, _utils.OpenAIMetadata]:
    """Create OpenAI-specific stream wrapper."""
    return StreamWrapper(
        span=span,
        stream=stream,
        metadata=_utils.OpenAIMetadata(),
        chunk_handler=_utils.OpenAIChunkHandler(),
        cleanup_handler=_utils.default_openai_cleanup,
    )


def get_choice_event(choice: Choice) -> dict[str, AttributeValue]:
    """Returns event attributes extracted from a completion choice."""
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_SYSTEM: gen_ai_attributes.GenAiSystemValues.OPENAI.value
    }

    if message := choice.message:
        message_dict: LLMOpenTelemetryMessage = {
            "role": message.role,
        }
        if content := message.content:
            message_dict["content"] = content
        if tool_calls := get_tool_calls(message):
            message_dict["tool_calls"] = tool_calls

        attributes["message"] = json_dumps(message_dict)
        attributes["index"] = choice.index
        attributes["finish_reason"] = choice.finish_reason or "error"
    return attributes


def set_response_attributes(span: Span, response: ChatCompletion) -> None:
    """Set span attributes from a completion response object."""
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_RESPONSE_MODEL: response.model
    }
    if choices := getattr(response, "choices", None):
        finish_reasons = []
        for choice in choices:
            choice_attributes = get_choice_event(choice)
            span.add_event(
                "gen_ai.choice",
                attributes=choice_attributes,
            )
            finish_reasons.append(choice.finish_reason)
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons
    if id := getattr(response, "id", None):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_ID] = id

    if service_tier := getattr(response, "service_tier", None):
        attributes[gen_ai_attributes.GEN_AI_OPENAI_REQUEST_SERVICE_TIER] = service_tier

    if usage := getattr(response, "usage", None):
        attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = usage.prompt_tokens
        attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = (
            usage.completion_tokens
        )
    span.set_attributes(attributes)


def get_llm_request_attributes(
    kwargs: dict[str, Any],
    client: OpenAI | AsyncOpenAI,
    operation_name: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
) -> dict[str, AttributeValue]:
    """Extract OpenTelemetry attributes from OpenAI API request parameters."""
    response_format = kwargs.get("response_format", {})
    response_format = (
        response_format.get("type")
        if isinstance(response_format, dict)
        else response_format.__name__
    )
    attributes = {
        gen_ai_attributes.GEN_AI_OPERATION_NAME: operation_name,
        gen_ai_attributes.GEN_AI_REQUEST_MODEL: kwargs.get("model"),
        gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE: kwargs.get("temperature"),
        gen_ai_attributes.GEN_AI_REQUEST_TOP_P: kwargs.get("p") or kwargs.get("top_p"),
        gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS: kwargs.get("max_tokens"),
        gen_ai_attributes.GEN_AI_REQUEST_PRESENCE_PENALTY: kwargs.get(
            "presence_penalty"
        ),
        gen_ai_attributes.GEN_AI_REQUEST_FREQUENCY_PENALTY: kwargs.get(
            "frequency_penalty"
        ),
        gen_ai_attributes.GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT: response_format,
        gen_ai_attributes.GEN_AI_OPENAI_REQUEST_SEED: kwargs.get("seed"),
    }
    set_server_address_and_port(client, attributes)
    attributes[gen_ai_attributes.GEN_AI_SYSTEM] = (
        gen_ai_attributes.GenAiSystemValues.OPENAI.value
    )

    service_tier = kwargs.get("service_tier")
    attributes[gen_ai_attributes.GEN_AI_OPENAI_RESPONSE_SERVICE_TIER] = (
        service_tier if service_tier != "auto" else None
    )

    return {k: v for k, v in attributes.items() if v is not None}
