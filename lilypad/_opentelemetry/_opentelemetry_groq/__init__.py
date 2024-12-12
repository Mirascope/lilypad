"""OpenTelemetry instrumentation for Groq."""

from collections.abc import Collection
from typing import Any

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.semconv.schemas import Schemas
from opentelemetry.trace import get_tracer
from wrapt import wrap_function_wrapper

from .patch import chat_completions_create, chat_completions_create_async


class GroqInstrumentor(BaseInstrumentor):
    """An instrumentor for Groq's SDK."""

    def instrumentation_dependencies(self) -> Collection[str]:
        """Specify Groq SDK version requirements."""
        return ("groq>=0.1.0,<1",)

    def _instrument(self, **kwargs: Any) -> None:
        """Instrument Groq SDK.

        Args:
            **kwargs: Arbitrary keyword arguments.
                tracer_provider: The tracer provider to use.
        """
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(
            __name__,
            "0.1.0",
            tracer_provider,
            schema_url=Schemas.V1_28_0.value,
        )

        wrap_function_wrapper(
            module="groq.resources.chat.completions",
            name="Completions.create",
            wrapper=chat_completions_create(tracer),
        )
        wrap_function_wrapper(
            module="groq.resources.chat.completions",
            name="AsyncCompletions.create",
            wrapper=chat_completions_create_async(tracer),
        )

    def _uninstrument(self, **kwargs: Any) -> None:
        """Uninstrument Groq SDK."""
        pass  # No specific cleanup needed
