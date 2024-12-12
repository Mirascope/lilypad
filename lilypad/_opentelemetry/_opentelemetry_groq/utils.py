"""OpenTelemetry utilities for Groq."""

from typing import Any

from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from opentelemetry.trace import Span
from opentelemetry.util.types import AttributeValue


class GroqMetadata:
    """Metadata for Groq chat completions."""

    def __init__(self) -> None:
        """Initialize Groq metadata."""
        self.total_tokens = 0
        self.completion_tokens = 0
        self.prompt_tokens = 0


class GroqChunkHandler:
    """Handler for Groq chat completion chunks."""

    def __call__(self, chunk: Any) -> str | None:
        """Handle a chunk from a Groq chat completion.

        Args:
            chunk: The chunk to handle.

        Returns:
            The content of the chunk, or None if there is no content.
        """
        if not chunk.choices:
            return None
        if hasattr(chunk.choices[0], "delta"):
            content = chunk.choices[0].delta.content
        else:
            content = chunk.choices[0].text
        return content


def set_message_event(span: Span, message: dict[str, Any]) -> None:
    """Set a message event on a span.

    Args:
        span: The span to set the event on.
        message: The message to set as an event.
    """
    if not span.is_recording():
        return

    attributes: dict[str, AttributeValue] = {
        gen_ai_attributes.GEN_AI_REQUEST_MESSAGE_ROLE: message.get("role", "unknown"),
    }
    content = message.get("content")
    if isinstance(content, str):
        attributes[gen_ai_attributes.GEN_AI_REQUEST_MESSAGE_CONTENT] = content

    span.add_event(
        name=gen_ai_attributes.GEN_AI_REQUEST_MESSAGE,
        attributes=attributes,
    )


def set_response_attributes(span: Span, response: Any) -> None:
    """Set response attributes on a span.

    Args:
        span: The span to set the attributes on.
        response: The response to get the attributes from.
    """
    if not span.is_recording():
        return

    if hasattr(response, "usage"):
        span.set_attribute(
            gen_ai_attributes.GEN_AI_RESPONSE_COMPLETION_TOKENS,
            response.usage.completion_tokens,
        )
        span.set_attribute(
            gen_ai_attributes.GEN_AI_RESPONSE_PROMPT_TOKENS,
            response.usage.prompt_tokens,
        )
        span.set_attribute(
            gen_ai_attributes.GEN_AI_RESPONSE_TOTAL_TOKENS,
            response.usage.total_tokens,
        )

    if hasattr(response, "choices") and response.choices:
        choice = response.choices[0]
        if hasattr(choice, "message"):
            span.set_attribute(
                gen_ai_attributes.GEN_AI_RESPONSE_MODEL_RESPONSE,
                choice.message.content,
            )
        elif hasattr(choice, "text"):
            span.set_attribute(
                gen_ai_attributes.GEN_AI_RESPONSE_MODEL_RESPONSE,
                choice.text,
            )


def default_groq_cleanup(metadata: GroqMetadata, response: Any) -> None:
    """Clean up Groq metadata after a response.

    Args:
        metadata: The metadata to update.
        response: The response to get the metadata from.
    """
    if hasattr(response, "usage"):
        metadata.completion_tokens = response.usage.completion_tokens
        metadata.prompt_tokens = response.usage.prompt_tokens
        metadata.total_tokens = response.usage.total_tokens
