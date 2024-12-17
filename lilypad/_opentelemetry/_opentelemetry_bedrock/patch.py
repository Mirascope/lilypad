from collections.abc import Awaitable, Callable
from typing import Any

from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.trace import Status, StatusCode, Tracer
from typing_extensions import ParamSpec

from lilypad._opentelemetry._opentelemetry_bedrock.utils import (
    get_bedrock_llm_request_attributes,
    set_bedrock_response_attributes,
)

P = ParamSpec("P")


def make_api_call_patch(
    tracer: Tracer,
) -> Callable[[Callable[P, Any], Any, tuple[Any, ...], dict[str, Any]], Any]:
    """Return a wrapper function for BaseClient._make_api_call to handle bedrock-runtime Converse calls."""

    def wrapper(
        wrapped: Callable[P, Any],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> dict:
        # args: (operation_name, params)
        operation_name, params = args
        service_name = instance.meta.service_model.service_name  # "bedrock-runtime"

        if service_name != "bedrock-runtime" or operation_name != "Converse":
            return wrapped(*args, **kwargs)

        span_attributes = get_bedrock_llm_request_attributes(params)
        span_name = f"{span_attributes.get('gen_ai.operation.name','chat')} {span_attributes.get('gen_ai.request.model','unknown')}"

        with tracer.start_as_current_span(
            name=span_name, attributes=span_attributes
        ) as span:
            try:
                response = wrapped(*args, **kwargs)
                # Set response attributes on the span if recording
                if span.is_recording():
                    set_bedrock_response_attributes(span, response)
                return response
            except Exception as error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                if span.is_recording():
                    span.set_attribute(
                        error_attributes.ERROR_TYPE, type(error).__qualname__
                    )
                raise

    return wrapper


def async_make_api_call_patch(
    tracer: Tracer,
) -> Callable[[Callable[P, Any], Any, tuple[Any, ...], dict[str, Any]], Awaitable[Any]]:
    """Return an async wrapper for AioBaseClient._make_api_call to handle bedrock-runtime Converse calls asynchronously."""

    async def async_wrapper(
        wrapped: Callable[P, Awaitable[Any]],
        instance: Any,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> dict:
        operation_name, params = args
        service_name = instance.meta.service_model.service_name  # "bedrock-runtime"

        if service_name != "bedrock-runtime" or operation_name != "Converse":
            return await wrapped(*args, **kwargs)

        span_attributes = get_bedrock_llm_request_attributes(params)
        span_name = f"{span_attributes.get('gen_ai.operation.name','chat')} {span_attributes.get('gen_ai.request.model','unknown')}"

        with tracer.start_as_current_span(
            name=span_name, attributes=span_attributes
        ) as span:
            try:
                response = await wrapped(*args, **kwargs)
                if span.is_recording():
                    set_bedrock_response_attributes(span, response)
                return response
            except Exception as error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                if span.is_recording():
                    span.set_attribute(
                        error_attributes.ERROR_TYPE, type(error).__qualname__
                    )
                raise

    return async_wrapper
