from typing import Any
from collections.abc import Collection

from wrapt import wrap_function_wrapper
from opentelemetry.trace import get_tracer
from opentelemetry.semconv.schemas import Schemas
from opentelemetry.instrumentation.utils import unwrap
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor

from .patch import make_api_call_patch, make_api_call_async_patch


class BedrockInstrumentor(BaseInstrumentor):
    def instrumentation_dependencies(self) -> Collection[str]:
        return (
            "aioboto3>=13.2.0,<15",
            "boto3>=1.35.36,<2",
        )

    def _instrument(self, **kwargs: Any) -> None:
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(
            __name__,
            "0.1.0",
            tracer_provider,
            schema_url=Schemas.V1_28_0.value,
        )

        # Patch _make_api_call of BaseClient
        wrap_function_wrapper("botocore.client", "BaseClient._make_api_call", make_api_call_patch(tracer))
        wrap_function_wrapper(
            "aiobotocore.client",
            "AioBaseClient._make_api_call",
            make_api_call_async_patch(tracer),
        )

    def _uninstrument(self, **kwargs: Any) -> None:
        import botocore.client
        import aiobotocore.client

        unwrap(botocore.client.BaseClient, "_make_api_call")
        unwrap(aiobotocore.client.AioBaseClient, "_make_api_call")
