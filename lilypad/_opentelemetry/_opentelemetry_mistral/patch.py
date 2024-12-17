from collections.abc import Awaitable, Callable
from typing import Any

from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.trace import Status, StatusCode, Tracer
from typing_extensions import ParamSpec

from .utils import get_mistral_llm_request_attributes, set_mistral_response_attributes

P = ParamSpec("P")


def mistral_complete(
    tracer: Tracer,
) -> Callable[[Callable[P, Any], Any, tuple[Any, ...], dict[str, Any]], Any]:
    def traced_method(
        wrapped: Callable[P, Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        span_attributes = get_mistral_llm_request_attributes(kwargs)
        span_name = f"{span_attributes.get('gen_ai.operation.name','chat')} {span_attributes.get('gen_ai.request.model','unknown')}"

        with tracer.start_as_current_span(
            name=span_name, attributes=span_attributes
        ) as span:
            try:
                result = wrapped(*args, **kwargs)
                if span.is_recording():
                    set_mistral_response_attributes(span, result)
                return result
            except Exception as error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                if span.is_recording():
                    span.set_attribute(
                        error_attributes.ERROR_TYPE, type(error).__qualname__
                    )
                raise

    return traced_method


def mistral_complete_async(
    tracer: Tracer,
) -> Callable[[Callable[P, Any], Any, tuple[Any, ...], dict[str, Any]], Awaitable[Any]]:
    async def traced_method(
        wrapped: Callable[P, Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        span_attributes = get_mistral_llm_request_attributes(kwargs)
        span_name = f"{span_attributes.get('gen_ai.operation.name','chat')} {span_attributes.get('gen_ai.request.model','unknown')}"

        with tracer.start_as_current_span(
            name=span_name, attributes=span_attributes
        ) as span:
            try:
                result = await wrapped(*args, **kwargs)
                if span.is_recording():
                    set_mistral_response_attributes(span, result)
                return result
            except Exception as error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                if span.is_recording():
                    span.set_attribute(
                        error_attributes.ERROR_TYPE, type(error).__qualname__
                    )
                raise

    return traced_method
