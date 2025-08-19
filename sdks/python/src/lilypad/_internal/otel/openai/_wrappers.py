"""The `OpenAIWrapper` implementation."""

from typing import Any

from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletionMessage
from opentelemetry.trace import Span
from opentelemetry.util.types import AttributeValue
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from ..base import BaseWrappers


class OpenAIWrappers(BaseWrappers[OpenAI | AsyncOpenAI, ChatCompletionMessage]):
    """The OpenAI Wrapper class implementation."""

    @staticmethod
    def _get_span_attributes(
        kwargs: dict[str, Any],
        client: OpenAI | AsyncOpenAI,
        operation_name: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
    ) -> dict[str, AttributeValue]:
        """The method for extracting OpenTelemetry span attributes from a request."""
        raise NotImplementedError()

    @staticmethod
    def _process_messages(span: Span, kwargs: dict[str, Any]) -> None:
        """Adds the OpenTelemetry events processed from the request to the span."""
        raise NotImplementedError()

    @staticmethod
    def _process_response(span: Span, response: ChatCompletionMessage) -> None:
        """Adds the OpenTelemetry attributes procesed from the response to the span."""
        raise NotImplementedError()
