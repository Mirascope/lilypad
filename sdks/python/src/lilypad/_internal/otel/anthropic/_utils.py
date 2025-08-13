"""Utility functions for Anthropic OpenTelemetry instrumentation.

This module provides helper functions for extracting and formatting Anthropic API
response data for telemetry purposes.
"""

import json
from typing import Any, Literal, Iterable, TypedDict

from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import (
    Message,
    TextBlock,
    ContentBlock,
    MessageParam,
    ToolUseBlock,
    TextBlockParam,
    MessageStreamEvent,
    RawMessageDeltaEvent,
    RawMessageStartEvent,
    RawContentBlockDeltaEvent,
    RawContentBlockStartEvent,
)
from opentelemetry.trace import Span
from opentelemetry.util.types import AttributeValue
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from ..types import LLMOpenTelemetryMessage, LLMOpenTelemetryToolCall
from ..utils import (
    BaseMetadata,
    ChoiceBuffer,
    ChunkHandler,
    ToolCallBuffer,
    set_server_address_and_port,
)
from ...utils import json_dumps


class AnthropicMetadata(BaseMetadata, total=False):
    """Anthropic-specific metadata extending BaseMetadata."""

    stop_reason: str | None


class AnthropicChunkHandler(ChunkHandler[MessageStreamEvent, AnthropicMetadata]):
    def extract_metadata(
        self, chunk: MessageStreamEvent, metadata: AnthropicMetadata
    ) -> None:
        """Extract metadata from a streaming chunk and update the metadata dictionary."""
        if isinstance(chunk, RawMessageStartEvent):
            message = chunk.message
            if not metadata.get("response_model"):
                metadata["response_model"] = message.model
            if not metadata.get("response_id"):
                metadata["response_id"] = message.id
            if message.usage:
                metadata["prompt_tokens"] = message.usage.input_tokens
                metadata["completion_tokens"] = message.usage.output_tokens

        elif isinstance(chunk, RawMessageDeltaEvent):
            if chunk.delta.stop_reason:
                metadata["stop_reason"] = chunk.delta.stop_reason
            if chunk.usage:
                metadata["completion_tokens"] = chunk.usage.output_tokens

    def process_chunk(
        self, chunk: MessageStreamEvent, buffers: list[ChoiceBuffer]
    ) -> None:
        """Process a streaming chunk and update the choice buffers with content."""

        if isinstance(chunk, RawContentBlockStartEvent):
            while len(buffers) <= chunk.index:
                buffers.append(ChoiceBuffer(len(buffers)))

            content_block = chunk.content_block
            if isinstance(content_block, ToolUseBlock):
                buffer = buffers[chunk.index]

                if not buffer.tool_calls_buffers:
                    buffer.tool_calls_buffers.append(
                        ToolCallBuffer(
                            chunk.index,
                            content_block.id,
                            content_block.name,
                        )
                    )

        elif isinstance(chunk, RawContentBlockDeltaEvent):
            while len(buffers) <= chunk.index:
                buffers.append(ChoiceBuffer(len(buffers)))

            if chunk.delta.type == "text_delta":
                buffers[chunk.index].append_text_content(chunk.delta.text)
            elif chunk.delta.type == "input_json_delta":
                if chunk.index < len(buffers):
                    buffer = buffers[chunk.index]
                    if not buffer.tool_calls_buffers:
                        buffer.tool_calls_buffers.append(None)
                    if buffer.tool_calls_buffers[0]:
                        buffer.tool_calls_buffers[0].append_arguments(
                            chunk.delta.partial_json
                        )
                    else:
                        buffer.tool_calls_buffers[0] = ToolCallBuffer(
                            chunk.index, "", ""
                        )

        elif isinstance(chunk, RawMessageDeltaEvent):
            if chunk.delta.stop_reason:
                for buffer in buffers:
                    buffer.finish_reason = chunk.delta.stop_reason


def default_anthropic_cleanup(
    span: Span, metadata: AnthropicMetadata, buffers: list[ChoiceBuffer]
) -> None:
    """Set final span attributes and events from accumulated metadata and buffers."""
    attributes = {}
    if response_model := metadata.get("response_model"):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_MODEL] = response_model
    if response_id := metadata.get("response_id"):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_ID] = response_id
    if prompt_tokens := metadata.get("prompt_tokens"):
        attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = prompt_tokens
    if completion_tokens := metadata.get("completion_tokens"):
        attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = completion_tokens

    if stop_reason := metadata.get("stop_reason"):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = [stop_reason]
    elif finish_reasons := tuple(
        buffer.finish_reason for buffer in buffers if buffer.finish_reason is not None
    ):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons

    span.set_attributes(attributes)
    for index, choice in enumerate(buffers):
        message: LLMOpenTelemetryMessage = {"role": "assistant"}
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

        event_attributes = {
            gen_ai_attributes.GEN_AI_SYSTEM: gen_ai_attributes.GenAiSystemValues.ANTHROPIC.value,
            "index": index,
            "finish_reason": choice.finish_reason or "none",
            "message": json.dumps(message),
        }
        span.add_event("gen_ai.choice", attributes=event_attributes)


class SystemMessageParam(TypedDict):
    role: Literal["system"]
    content: str | Iterable[TextBlockParam]


def set_message_event(span: Span, message: MessageParam | SystemMessageParam) -> None:
    """Add a message event to the span with appropriate attributes."""
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_SYSTEM: gen_ai_attributes.GenAiSystemValues.ANTHROPIC.value
    }

    role = message["role"]

    if content := message.get("content"):
        if isinstance(content, str):
            attributes["content"] = content
        elif isinstance(content, list):
            text_parts = []
            tool_calls: list[LLMOpenTelemetryToolCall] = []
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        tool_calls.append(
                            {
                                "id": block.get("id", ""),
                                "type": "function",
                                "function": {
                                    "name": block.get("name", ""),
                                    "arguments": json_dumps(block.get("input", {})),
                                },
                            }
                        )

            if text_parts:
                attributes["content"] = "\n".join(text_parts)
            if tool_calls:
                attributes["tool_calls"] = json_dumps(tool_calls)
        else:
            attributes["content"] = json_dumps(content)

    span.add_event(
        f"gen_ai.{role}.message",
        attributes=attributes,
    )


def get_choice_event(
    content_block: ContentBlock, role: Literal["assistant"], stop_reason: str | None
) -> dict[str, AttributeValue]:
    """Returns event attributes extracted from a content block."""
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_SYSTEM: gen_ai_attributes.GenAiSystemValues.ANTHROPIC.value
    }

    message: LLMOpenTelemetryMessage = {"role": role}

    if isinstance(content_block, TextBlock):
        message["content"] = content_block.text
    elif isinstance(content_block, ToolUseBlock):
        message["tool_calls"] = [
            {
                "id": content_block.id,
                "type": "function",
                "function": {
                    "name": content_block.name,
                    "arguments": json_dumps(content_block.input)
                    if content_block.input
                    else "{}",
                },
            }
        ]

    attributes["message"] = json_dumps(message)
    attributes["finish_reason"] = stop_reason or "error"
    return attributes


def set_response_attributes(span: Span, response: Message) -> None:
    """Set span attributes from a Message response object."""
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_RESPONSE_MODEL: response.model
    }

    if content := response.content:
        for index, content_block in enumerate(content):
            choice_attributes = get_choice_event(
                content_block, response.role, response.stop_reason
            )
            choice_attributes["index"] = index
            span.add_event(
                "gen_ai.choice",
                attributes=choice_attributes,
            )
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = [
            response.stop_reason or "error"
        ]

    if response.id:
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_ID] = response.id

    if usage := response.usage:
        attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = usage.input_tokens
        attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = usage.output_tokens

    span.set_attributes(attributes)


def get_llm_request_attributes(
    kwargs: dict[str, Any],
    client: Anthropic | AsyncAnthropic,
    operation_name: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
) -> dict[str, AttributeValue]:
    """Extract OpenTelemetry attributes from Anthropic API request parameters."""
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_OPERATION_NAME: operation_name,
        gen_ai_attributes.GEN_AI_SYSTEM: gen_ai_attributes.GenAiSystemValues.ANTHROPIC.value,
    }

    if model := kwargs.get("model"):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_MODEL] = model
    if temperature := kwargs.get("temperature"):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] = temperature
    if top_p := kwargs.get("top_p"):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] = top_p
    if top_k := kwargs.get("top_k"):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_TOP_K] = top_k
    if max_tokens := kwargs.get("max_tokens"):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] = max_tokens
    if stop_sequences := kwargs.get("stop_sequences"):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_STOP_SEQUENCES] = stop_sequences

    set_server_address_and_port(client, attributes)
    return {k: v for k, v in attributes.items() if v is not None}
