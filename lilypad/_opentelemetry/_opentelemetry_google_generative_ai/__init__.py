from collections.abc import Collection
from typing import Any

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.utils import unwrap
from opentelemetry.semconv.schemas import Schemas
from opentelemetry.trace import get_tracer
from wrapt import wrap_function_wrapper

from .patch import generate_content, generate_content_async


class GoogleGenerativeAIInstrumentor(BaseInstrumentor):
    def instrumentation_dependencies(self) -> Collection[str]:
        return ("google-generativeai>=0.4.0,<1",)

    def _instrument(self, **kwargs: Any) -> None:
        """Enable OpenAI instrumentation."""
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(
            __name__,
            "0.1.0",  # Lilypad version
            tracer_provider,
            schema_url=Schemas.V1_28_0.value,
        )
        wrap_function_wrapper(
            module="google.generativeai.generative_models",
            name="GenerativeModel.generate_content",
            wrapper=generate_content(tracer),
        )
        wrap_function_wrapper(
            module="google.generativeai.generative_models",
            name="GenerativeModel.generate_content_async",
            wrapper=generate_content_async(tracer),
        )

    def _uninstrument(self, **kwargs: Any) -> None:
        import google.generativeai

        unwrap(
            google.generativeai.generative_models.GenerativeModel, "generate_content"
        )
        unwrap(
            google.generativeai.generative_models.GenerativeModel,
            "generate_content_async",
        )
