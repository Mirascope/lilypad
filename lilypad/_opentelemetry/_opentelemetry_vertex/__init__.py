from collections.abc import Collection
from typing import Any

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.utils import unwrap
from opentelemetry.semconv.schemas import Schemas
from opentelemetry.trace import get_tracer
from typing_extensions import ParamSpec, TypedDict
from wrapt import wrap_function_wrapper

from lilypad._opentelemetry._opentelemetry_vertex.patch import (
    vertex_generate_content,
    vertex_generate_content_async,
)

P = ParamSpec("P")


class VertexAIInstrumentor(BaseInstrumentor):
    def instrumentation_dependencies(self) -> Collection[str]:
        # The version range may be adjusted as necessary.
        return ("google-cloud-aiplatform>=1.74.0,<2",)

    def _instrument(self, **kwargs: Any) -> None:
        """Enable Vertex AI instrumentation."""
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(
            __name__,
            "0.1.0",  # Lilypad version
            tracer_provider,
            schema_url=Schemas.V1_28_0.value,
        )
        wrap_function_wrapper(
            module="vertexai.generative_models._generative_models",
            name="GenerativeModel.generate_content",
            wrapper=vertex_generate_content(tracer),
        )
        wrap_function_wrapper(
            module="vertexai.generative_models._generative_models",
            name="GenerativeModel.generate_content_async",
            wrapper=vertex_generate_content_async(tracer),
        )

    def _uninstrument(self, **kwargs: Any) -> None:
        import vertexai.generative_models._generative_models

        unwrap(
            vertexai.generative_models._generative_models.GenerativeModel,
            "generate_content",
        )
        unwrap(
            vertexai.generative_models._generative_models.GenerativeModel,
            "generate_content_async",
        )
