"""Utility functions for Mistral OpenTelemetry instrumentation.

This module provides helper functions for extracting and formatting Mistral API
response data for telemetry purposes.
"""

import json
from typing import Any, Protocol

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

from mistralai import Mistral
from mistralai.models import (
    ChatCompletionResponse,
    CompletionEvent,
    CompletionChunk,
    ChatCompletionChoice,
    CompletionResponseStreamChoice,
    UsageInfo,
    AssistantMessage,
    DeltaMessage,
)


class MistralMetadata(BaseMetadata, total=False):
    """Mistral-specific metadata extending BaseMetadata."""

    finish_reasons: list[str]


class MistralMessageProtocol(Protocol):
    """Protocol for Mistral chat messages."""

    role: str
    content: str | None


class MistralChoiceProtocol(Protocol):
    """Protocol for Mistral chat choices."""

    index: int
    message: AssistantMessage
    finish_reason: str | None


class MistralCompletionProtocol(Protocol):
    """Protocol for Mistral chat completions."""

    id: str
    model: str
    choices: list[ChatCompletionChoice]
    usage: UsageInfo | None


class MistralStreamChoiceProtocol(Protocol):
    """Protocol for Mistral streaming choices."""

    index: int
    delta: DeltaMessage
    finish_reason: str | None


class MistralStreamChunkProtocol(Protocol):
    """Protocol for Mistral streaming chunks."""

    id: str
    model: str
    choices: list[CompletionResponseStreamChoice]
    usage: UsageInfo | None


class MistralChunkHandler(ChunkHandler[CompletionEvent, MistralMetadata]):
    """Handler for processing Mistral streaming chunks."""

    def extract_metadata(
        self, chunk: CompletionEvent, metadata: MistralMetadata
    ) -> None:
        """Extract metadata from a streaming chunk and update the metadata dictionary."""
        data: CompletionChunk = chunk.data
        if not metadata.get("response_model") and data.model:
            metadata["response_model"] = data.model
        if not metadata.get("response_id") and data.id:
            metadata["response_id"] = data.id
        if usage := data.usage:
            if completion_tokens := usage.completion_tokens:
                metadata["completion_tokens"] = completion_tokens
            if prompt_tokens := usage.prompt_tokens:
                metadata["prompt_tokens"] = prompt_tokens

    def process_chunk(
        self, chunk: CompletionEvent, buffers: list[ChoiceBuffer]
    ) -> None:
        """Process a streaming chunk and update the choice buffers with content."""
        data: CompletionChunk = chunk.data
        for choice in data.choices:
            while len(buffers) <= choice.index:
                buffers.append(ChoiceBuffer(len(buffers)))

            if finish_reason := choice.finish_reason:
                buffers[choice.index].finish_reason = str(finish_reason)

            if delta := choice.delta:
                if delta.content is not None and isinstance(delta.content, str):
                    buffers[choice.index].append_text_content(delta.content)


def default_mistral_cleanup(
    span: Span, metadata: MistralMetadata, buffers: list[ChoiceBuffer]
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
        message: dict[str, Any] = {"role": "assistant"}
        if text_content := choice.text_content:
            message["content"] = "".join(text_content)

        event_attributes: dict[str, AttributeValue] = {
            gen_ai_attributes.GEN_AI_SYSTEM: "mistral",
            "index": index,
            "finish_reason": str(choice.finish_reason)
            if choice.finish_reason
            else "none",
            "message": json.dumps(message),
        }
        span.add_event("gen_ai.choice", attributes=event_attributes)


def set_message_event(span: Span, message: dict[str, Any]) -> None:
    """Add a message event to the span with appropriate attributes."""
    attributes: dict[str, AttributeValue] = {gen_ai_attributes.GEN_AI_SYSTEM: "mistral"}

    role = message.get("role", "")
    content = message.get("content")

    if content is not None:
        if not isinstance(content, str):
            content = json_dumps(content)
        attributes["content"] = content

    span.add_event(
        f"gen_ai.{role}.message",
        attributes=attributes,
    )


def get_choice_event(choice: ChatCompletionChoice) -> dict[str, AttributeValue]:
    """Extract event attributes from a choice object."""
    attributes: dict[str, AttributeValue] = {gen_ai_attributes.GEN_AI_SYSTEM: "mistral"}

    message_dict: dict[str, Any] = {"role": choice.message.role}
    if content := choice.message.content:
        message_dict["content"] = content

    attributes["message"] = json.dumps(message_dict)
    attributes["index"] = choice.index
    attributes["finish_reason"] = (
        str(choice.finish_reason) if choice.finish_reason else "none"
    )
    return attributes


def set_response_attributes(span: Span, response: ChatCompletionResponse) -> None:
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
    client: Mistral,
    operation_name: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
) -> dict[str, AttributeValue]:
    """Extract span attributes from request kwargs and client."""
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_OPERATION_NAME: operation_name,
        gen_ai_attributes.GEN_AI_SYSTEM: "mistral",
    }

    if model := kwargs.get("model"):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_MODEL] = model

    if "temperature" in kwargs:
        attributes[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] = kwargs["temperature"]

    if max_tokens := kwargs.get("max_tokens"):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] = max_tokens

    if "top_p" in kwargs:
        attributes[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] = kwargs["top_p"]

    set_server_address_and_port(client, attributes)

    return attributes
