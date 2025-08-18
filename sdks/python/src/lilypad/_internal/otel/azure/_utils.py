"""Utility functions for Azure AI Inference OpenTelemetry instrumentation.

This module provides helper functions for extracting and formatting Azure AI Inference API
response data for telemetry purposes.
"""

import json
from typing import Any, Protocol, TypedDict, Literal

from opentelemetry.trace import Span
from opentelemetry.util.types import AttributeValue
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from ..utils import (
    BaseMetadata,
    ChoiceBuffer,
    ChunkHandler,
    set_server_address_and_port,
)
from ...utils import json_dumps

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.aio import ChatCompletionsClient as AsyncChatCompletionsClient
from azure.ai.inference.models import (
    ChatCompletions,
    StreamingChatCompletionsUpdate,
    ChatResponseMessage,
    ChatRequestMessage,
    ChatCompletionsToolCall,
    CompletionsUsage,
    StreamingChatChoiceUpdate,
    ChatChoice,
    StreamingChatResponseToolCallUpdate,
    FunctionCall,
)


class FunctionCallDict(TypedDict):
    """TypedDict for function call structure."""

    name: str
    arguments: str


class ToolCallDict(TypedDict):
    """TypedDict for tool call structure."""

    id: str
    type: Literal["function"]
    function: FunctionCallDict


class MessageDict(TypedDict, total=False):
    """TypedDict for message structure."""

    role: str
    content: str
    tool_calls: list[ToolCallDict]


class IndexedToolCall:
    """Wrapper to add index property to Azure streaming tool calls."""

    def __init__(
        self,
        tool_call: StreamingChatResponseToolCallUpdate,
        index: int,
    ):
        self._tool_call = tool_call
        self._index = index

    @property
    def index(self) -> int:
        return self._index

    @property
    def id(self) -> str | None:
        return self._tool_call.id if self._tool_call.id else None

    @property
    def function(self) -> FunctionCall | None:
        return self._tool_call.function if self._tool_call.function else None


class AzureMetadata(BaseMetadata, total=False):
    """Azure-specific metadata extending BaseMetadata."""

    finish_reasons: list[str]


class AzureMessageProtocol(Protocol):
    """Protocol for Azure chat messages."""

    role: str
    content: str | None
    tool_calls: list[ChatCompletionsToolCall] | None


class AzureChoiceProtocol(Protocol):
    """Protocol for Azure chat choices."""

    index: int
    message: ChatResponseMessage
    finish_reason: str | None


class AzureCompletionProtocol(Protocol):
    """Protocol for Azure chat completions."""

    id: str
    model: str
    choices: list[ChatChoice]
    usage: CompletionsUsage | None


class AzureStreamChunkProtocol(Protocol):
    """Protocol for Azure streaming chunks."""

    id: str | None
    model: str | None
    choices: list[StreamingChatChoiceUpdate]
    usage: CompletionsUsage | None


class AzureChunkHandler(ChunkHandler[StreamingChatCompletionsUpdate, AzureMetadata]):
    def extract_metadata(
        self, chunk: StreamingChatCompletionsUpdate, metadata: AzureMetadata
    ) -> None:
        """Extract metadata from a streaming chunk and update the metadata dictionary."""
        if not metadata.get("response_model") and chunk.model:
            metadata["response_model"] = chunk.model
        if not metadata.get("response_id") and chunk.id:
            metadata["response_id"] = chunk.id
        if usage := chunk.usage:
            if completion_tokens := usage.completion_tokens:
                metadata["completion_tokens"] = completion_tokens
            if prompt_tokens := usage.prompt_tokens:
                metadata["prompt_tokens"] = prompt_tokens

    def process_chunk(
        self, chunk: StreamingChatCompletionsUpdate, buffers: list[ChoiceBuffer]
    ) -> None:
        """Process a streaming chunk and update the choice buffers with content."""
        for choice in chunk.choices:
            while len(buffers) <= choice.index:
                buffers.append(ChoiceBuffer(len(buffers)))

            if finish_reason := choice.finish_reason:
                buffers[choice.index].finish_reason = str(finish_reason)

            if delta := choice.delta:
                if delta.content is not None:
                    buffers[choice.index].append_text_content(delta.content)

                if tool_calls := delta.tool_calls:
                    for index, tool_call in enumerate(tool_calls):
                        indexed_tool_call = IndexedToolCall(tool_call, index)
                        buffers[choice.index].append_tool_call(indexed_tool_call)


def default_azure_cleanup(
    span: Span, metadata: AzureMetadata, buffers: list[ChoiceBuffer]
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

    if finish_reasons := tuple(
        str(buffer.finish_reason)
        for buffer in buffers
        if buffer.finish_reason is not None
    ):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons

    span.set_attributes(attributes)
    for index, choice in enumerate(buffers):
        message: MessageDict = {"role": "assistant"}
        if text_content := choice.text_content:
            message["content"] = "".join(text_content)
        if tool_calls_buffers := choice.tool_calls_buffers:
            tool_calls: list[ToolCallDict] = []
            for tool_call in tool_calls_buffers:
                if tool_call:
                    function: FunctionCallDict = {
                        "name": tool_call.function_name,
                        "arguments": "".join(tool_call.arguments),
                    }
                    tool_call_dict: ToolCallDict = {
                        "id": tool_call.tool_call_id,
                        "type": "function",
                        "function": function,
                    }
                    tool_calls.append(tool_call_dict)
            message["tool_calls"] = tool_calls

        event_attributes: dict[str, AttributeValue] = {
            gen_ai_attributes.GEN_AI_SYSTEM: gen_ai_attributes.GenAiSystemValues.AZ_AI_INFERENCE.value,
            "index": index,
            "finish_reason": str(choice.finish_reason)
            if choice.finish_reason
            else "none",
            "message": json.dumps(message),
        }
        span.add_event("gen_ai.choice", attributes=event_attributes)


def get_tool_calls(
    message: ChatResponseMessage | ChatRequestMessage | dict[str, Any],
) -> list[ToolCallDict] | None:
    """Returns tool calls extracted from a message object or dictionary."""

    if isinstance(message, dict):
        tool_calls = message.get("tool_calls")
    else:
        tool_calls = getattr(message, "tool_calls", None)

    if not tool_calls:
        return None

    calls: list[ToolCallDict] = []
    for tool_call in tool_calls:
        if isinstance(tool_call, dict):
            call_id = tool_call.get("id", "")
            if func := tool_call.get("function"):
                function_dict: FunctionCallDict = {
                    "name": func.get("name", ""),
                    "arguments": func.get("arguments", ""),
                }
                tool_call_dict: ToolCallDict = {
                    "id": call_id,
                    "type": "function",
                    "function": function_dict,
                }
                calls.append(tool_call_dict)
        else:
            if function := tool_call.function:
                function_dict: FunctionCallDict = {
                    "name": function.name,
                    "arguments": function.arguments,
                }
                tool_call_dict: ToolCallDict = {
                    "id": tool_call.id,
                    "type": "function",
                    "function": function_dict,
                }
                calls.append(tool_call_dict)
    return calls


def set_message_event(span: Span, message: ChatRequestMessage | dict[str, Any]) -> None:
    """Add a message event to the span with appropriate attributes."""
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_SYSTEM: gen_ai_attributes.GenAiSystemValues.AZ_AI_INFERENCE.value
    }

    if isinstance(message, dict):
        role = message.get("role", "")
        content = message.get("content")
        tool_call_id = message.get("tool_call_id")
    else:
        role = getattr(message, "role", "")
        content = getattr(message, "content", None)
        tool_call_id = getattr(message, "tool_call_id", None)

    if role == "assistant" and (tool_calls := get_tool_calls(message)):
        attributes["tool_calls"] = json_dumps(tool_calls)

    if role == "tool" and tool_call_id:
        attributes["id"] = tool_call_id

    if content is not None:
        if not isinstance(content, str):
            content = json_dumps(content)
        attributes["content"] = content

    span.add_event(
        f"gen_ai.{role}.message",
        attributes=attributes,
    )


def get_choice_event(choice: ChatChoice) -> dict[str, AttributeValue]:
    """Extract event attributes from a choice object."""
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_SYSTEM: gen_ai_attributes.GenAiSystemValues.AZ_AI_INFERENCE.value
    }

    message_dict: MessageDict = {"role": choice.message.role}
    if content := choice.message.content:
        message_dict["content"] = content
    if tool_calls := get_tool_calls(choice.message):
        message_dict["tool_calls"] = tool_calls

    attributes["message"] = json.dumps(message_dict)
    attributes["index"] = choice.index
    attributes["finish_reason"] = (
        str(choice.finish_reason) if choice.finish_reason else "none"
    )
    return attributes


def set_response_attributes(span: Span, response: ChatCompletions) -> None:
    """Set span attributes from non-streaming response."""
    attributes: dict[str, AttributeValue] = {}

    if model := response.model:
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_MODEL] = model

    if choices := response.choices:
        finish_reasons = []
        for choice in choices:
            choice_attributes = get_choice_event(choice)
            span.add_event(
                "gen_ai.choice",
                attributes=choice_attributes,
            )
            if finish_reason := choice.finish_reason:
                finish_reasons.append(str(finish_reason))
        if finish_reasons:
            attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = tuple(
                finish_reasons
            )

    if response_id := response.id:
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_ID] = response_id

    if usage := response.usage:
        if prompt_tokens := usage.prompt_tokens:
            attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = prompt_tokens
        if completion_tokens := usage.completion_tokens:
            attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = completion_tokens

    span.set_attributes(attributes)


def get_llm_request_attributes(
    kwargs: dict[str, Any],
    client: ChatCompletionsClient | AsyncChatCompletionsClient,
    operation_name: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
) -> dict[str, AttributeValue]:
    """Extract span attributes from request kwargs and client."""
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_OPERATION_NAME: operation_name,
        gen_ai_attributes.GEN_AI_SYSTEM: gen_ai_attributes.GenAiSystemValues.AZ_AI_INFERENCE.value,
    }

    if model := kwargs.get("model"):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_MODEL] = model

    if temperature := kwargs.get("temperature"):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] = temperature

    if max_tokens := kwargs.get("max_tokens"):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] = max_tokens

    if top_p := kwargs.get("top_p"):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] = top_p

    if frequency_penalty := kwargs.get("frequency_penalty"):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_FREQUENCY_PENALTY] = (
            frequency_penalty
        )

    if presence_penalty := kwargs.get("presence_penalty"):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_PRESENCE_PENALTY] = presence_penalty

    set_server_address_and_port(client, attributes)

    return attributes
