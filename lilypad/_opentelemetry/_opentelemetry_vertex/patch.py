from collections.abc import Awaitable, Callable
from typing import Any

from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.trace import SpanKind, Status, StatusCode, Tracer
from typing_extensions import ParamSpec

from .utils import (
    get_vertex_llm_request_attributes,
    set_vertex_response_attributes,
    set_vertex_stream,
    set_vertex_stream_async,
)

P = ParamSpec("P")


def vertex_generate_content(
    tracer: Tracer,
) -> Callable[[Callable[P, Any], Any, tuple[Any, ...], dict[str, Any]], Any]:
    def traced_method(
        wrapped: Callable[P, Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        span_attributes = {**get_vertex_llm_request_attributes(kwargs, instance)}

        span_name = f"{span_attributes['gen_ai.operation.name']} {span_attributes['gen_ai.request.model']}"
        with tracer.start_as_current_span(
            name=span_name,
            kind=SpanKind.CLIENT,
            attributes=span_attributes,
            end_on_exit=False,
        ) as span:
            try:
                result = wrapped(*args, **kwargs)
                if kwargs.get("stream", False):
                    set_vertex_stream(span, result, instance)
                elif span.is_recording():
                    set_vertex_response_attributes(span, result, instance)
                span.end()
                return result

            except Exception as error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                if span.is_recording():
                    span.set_attribute(
                        error_attributes.ERROR_TYPE, type(error).__qualname__
                    )
                span.end()
                raise

    return traced_method


def vertex_generate_content_async(
    tracer: Tracer,
) -> Callable[[Callable[P, Any], Any, tuple[Any, ...], dict[str, Any]], Awaitable[Any]]:
    async def traced_method(
        wrapped: Callable[P, Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Any:
        span_attributes = {**get_vertex_llm_request_attributes(kwargs, instance)}

        span_name = f"{span_attributes['gen_ai.operation.name']} {span_attributes['gen_ai.request.model']}"
        with tracer.start_as_current_span(
            name=span_name,
            kind=SpanKind.CLIENT,
            attributes=span_attributes,
            end_on_exit=False,
        ) as span:
            try:
                result = await wrapped(*args, **kwargs)
                if kwargs.get("stream", False):
                    await set_vertex_stream_async(span, result, instance)
                elif span.is_recording():
                    set_vertex_response_attributes(span, result, instance)
                span.end()
                return result

            except Exception as error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                if span.is_recording():
                    span.set_attribute(
                        error_attributes.ERROR_TYPE, type(error).__qualname__
                    )
                span.end()
                raise

    return traced_method
