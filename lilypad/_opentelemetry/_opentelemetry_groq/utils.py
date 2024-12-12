"""OpenTelemetry utilities for Groq."""

import json
from typing import Any, TypedDict

from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from opentelemetry.trace import Span
from opentelemetry.util.types import AttributeValue

from lilypad._opentelemetry._utils import ChoiceBuffer


class GroqMetadata(TypedDict, total=False):
    response_id: str | None
    response_model: str | None
    finish_reasons: list[str]
    prompt_tokens: int | None
    completion_tokens: int | None


class GroqChunkHandler:
    """Handler for Groq chat completion chunks."""

    def extract_metadata(self, chunk: Any, metadata: GroqMetadata) -> None:
        if not metadata.get("response_model") and hasattr(chunk, "model"):
            metadata["response_model"] = chunk.model
        if not metadata.get("response_id") and hasattr(chunk, "id"):
            metadata["response_id"] = chunk.id
        if hasattr(chunk, "usage"):
            if hasattr(chunk.usage, "completion_tokens"):
                metadata["completion_tokens"] = chunk.usage.completion_tokens
            if hasattr(chunk.usage, "prompt_tokens"):
                metadata["prompt_tokens"] = chunk.usage.prompt_tokens

        # Initialize finish_reasons if not present
        if "finish_reasons" not in metadata:
            metadata["finish_reasons"] = []

        # Add finish reason if present in chunk
        if hasattr(chunk, "choices") and chunk.choices:
            for choice in chunk.choices:
                if choice.finish_reason and choice.finish_reason not in metadata["finish_reasons"]:
                    metadata["finish_reasons"].append(choice.finish_reason)

    def process_chunk(self, chunk: Any, buffers: list[ChoiceBuffer]) -> None:
        if not hasattr(chunk, "choices"):
            return

        for choice in chunk.choices:
            if not hasattr(choice, "delta") and not hasattr(choice, "message"):
                continue

            # Ensure enough choice buffers
            while len(buffers) <= choice.index:
                buffers.append(ChoiceBuffer(len(buffers)))

            if choice.finish_reason:
                buffers[choice.index].finish_reason = choice.finish_reason

            if hasattr(choice, "delta"):
                if choice.delta.content is not None:
                    buffers[choice.index].append_text_content(choice.delta.content)
            elif hasattr(choice, "message"):
                if choice.message.content is not None:
                    buffers[choice.index].append_text_content(choice.message.content)


def default_groq_cleanup(
    span: Span, metadata: GroqMetadata, buffers: list[ChoiceBuffer]
) -> None:
    """Default Groq cleanup handler"""
    attributes: dict[str, AttributeValue] = {}
    if response_model := metadata.get("response_model"):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_MODEL] = response_model
    if response_id := metadata.get("response_id"):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_ID] = response_id
    if prompt_tokens := metadata.get("prompt_tokens"):
        attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = prompt_tokens
    if completion_tokens := metadata.get("completion_tokens"):
        attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = completion_tokens
    if finish_reasons := metadata.get("finish_reasons"):
        attributes[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] = finish_reasons

    span.set_attributes(attributes)
    for idx, choice in enumerate(buffers):
        message: dict[str, Any] = {"role": "assistant"}
        if choice.text_content:
            message["content"] = "".join(choice.text_content)

        event_attributes: dict[str, AttributeValue] = {
            gen_ai_attributes.GEN_AI_SYSTEM: "groq",
            "index": idx,
            "finish_reason": choice.finish_reason or "none",
            "message": json.dumps(message),
        }
        span.add_event("gen_ai.choice", attributes=event_attributes)


def get_choice_event(choice: Any) -> dict[str, AttributeValue]:
    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_SYSTEM: "groq"
    }

    if message := choice.message:
        message_dict = {
            "role": message.role,
        }
        if content := message.content:
            message_dict["content"] = content

        attributes["message"] = json.dumps(message_dict)
        attributes["index"] = choice.index
        attributes["finish_reason"] = choice.finish_reason or "error"
    return attributes


def set_message_event(span: Span, message: dict) -> None:
    attributes = {
        gen_ai_attributes.GEN_AI_SYSTEM: "groq"
    }
    role = message.get("role", "")
    if content := message.get("content"):
        if not isinstance(content, str):
            content = json.dumps(content)
        attributes["content"] = content

    span.add_event(
        f"gen_ai.{role}.message",
        attributes=attributes,
    )


def set_response_attributes(span: Span, response: Any) -> None:
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

    if usage := getattr(response, "usage", None):
        attributes[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] = usage.prompt_tokens
        attributes[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] = (
            usage.completion_tokens
        )
    span.set_attributes(attributes)
