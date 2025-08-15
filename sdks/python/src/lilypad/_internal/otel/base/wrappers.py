"""Common wrapper utilities for LLM provider instrumentation."""

from typing import Any, Literal, overload
from contextlib import contextmanager
from collections.abc import Callable, Iterator, Awaitable

from opentelemetry.trace import Span, Status, Tracer, SpanKind, StatusCode
from opentelemetry.util.types import AttributeValue
from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from ..utils import (
    StreamWrapper,
    StreamProtocol,
    AsyncStreamWrapper,
    AsyncStreamProtocol,
)
from .protocols import (
    P,
    ClientT,
    MetadataT,
    ResponseT,
    StreamChunkT,
    ProcessMessages,
    ProcessResponse,
    GetSpanAttributes,
    SyncStreamHandler,
    AsyncStreamHandler,
    CreateStreamWrapper,
    SyncCompletionHandler,
    AsyncCompletionHandler,
    CreateAsyncStreamWrapper,
)


@contextmanager
def _span(
    tracer: Tracer,
    span_attributes: dict[str, AttributeValue],
) -> Iterator[Span]:
    """Yields an OpenTelemertry span for LLM operations."""
    operation_name = span_attributes.get(
        gen_ai_attributes.GEN_AI_OPERATION_NAME, "unknown"
    )
    model_name = span_attributes.get(gen_ai_attributes.GEN_AI_REQUEST_MODEL, "unknown")
    span_name = f"{operation_name} {model_name}"

    with tracer.start_as_current_span(
        name=span_name,
        kind=SpanKind.CLIENT,
        attributes=span_attributes,
        end_on_exit=False,
    ) as span:
        yield span


def _create_sync_completion_wrapper(
    tracer: Tracer,
    get_span_attributes: GetSpanAttributes[ClientT],
    process_messages: ProcessMessages,
    process_response: ProcessResponse[ResponseT],
) -> SyncCompletionHandler[P, ResponseT, ClientT]:
    """Returns a synchronous completion wrapper for LLM API calls."""

    def traced_method_completion(
        wrapped: Callable[P, ResponseT],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ResponseT:
        span_attributes = get_span_attributes(kwargs, client)
        with _span(tracer, span_attributes) as span:
            if span.is_recording():
                process_messages(span, kwargs)
            try:
                result = wrapped(*args, **kwargs)
                if span.is_recording():
                    process_response(span, result)
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

    return traced_method_completion


def _create_sync_stream_wrapper(
    tracer: Tracer,
    get_span_attributes: GetSpanAttributes[ClientT],
    process_messages: ProcessMessages,
    process_response: ProcessResponse[Any],
    create_stream_wrapper: CreateStreamWrapper[StreamChunkT, MetadataT] | None,
) -> SyncStreamHandler[P, StreamChunkT, MetadataT, ClientT]:
    """Returns a synchronous streaming wrapper for LLM API calls."""

    def traced_method_stream(
        wrapped: Callable[P, StreamProtocol[StreamChunkT]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> StreamWrapper[StreamChunkT, MetadataT]:
        span_attributes = get_span_attributes(kwargs, client)
        with _span(tracer, span_attributes) as span:
            if span.is_recording():
                process_messages(span, kwargs)
            try:
                if create_stream_wrapper and kwargs.get("stream", False):
                    return create_stream_wrapper(span, wrapped(*args, **kwargs))
                result = wrapped(*args, **kwargs)
                if span.is_recording():
                    process_response(span, result)
                span.end()
                return result  # type: ignore[return-value]
            except Exception as error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                if span.is_recording():
                    span.set_attribute(
                        error_attributes.ERROR_TYPE, type(error).__qualname__
                    )
                span.end()
                raise

    return traced_method_stream


def _create_async_completion_wrapper(
    tracer: Tracer,
    get_span_attributes: GetSpanAttributes[ClientT],
    process_messages: ProcessMessages,
    process_response: ProcessResponse[ResponseT],
) -> AsyncCompletionHandler[P, ResponseT, ClientT]:
    """Returns an asynchronous completion wrapper for LLM API calls."""

    async def traced_method_completion(
        wrapped: Callable[P, Awaitable[ResponseT]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ResponseT:
        span_attributes = get_span_attributes(kwargs, client)
        with _span(tracer, span_attributes) as span:
            if span.is_recording():
                process_messages(span, kwargs)
            try:
                result = await wrapped(*args, **kwargs)
                if span.is_recording():
                    process_response(span, result)
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

    return traced_method_completion


def _create_async_stream_handler(
    tracer: Tracer,
    get_span_attributes: GetSpanAttributes[ClientT],
    process_messages: ProcessMessages,
    process_response: ProcessResponse[Any],
    create_async_stream_wrapper_func: CreateAsyncStreamWrapper[StreamChunkT, MetadataT]
    | None,
) -> AsyncStreamHandler[P, StreamChunkT, MetadataT, ClientT]:
    """Returns an asynchronous streaming wrapper for LLM API calls."""

    async def traced_method_stream(
        wrapped: Callable[P, Awaitable[AsyncStreamProtocol[StreamChunkT]]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> AsyncStreamWrapper[StreamChunkT, MetadataT]:
        span_attributes = get_span_attributes(kwargs, client)
        with _span(tracer, span_attributes) as span:
            if span.is_recording():
                process_messages(span, kwargs)
            try:
                if create_async_stream_wrapper_func and kwargs.get("stream", False):
                    stream = await wrapped(*args, **kwargs)
                    return await create_async_stream_wrapper_func(span, stream)
                result = await wrapped(*args, **kwargs)
                if span.is_recording():
                    process_response(span, result)
                span.end()
                return result  # type: ignore[return-value]
            except Exception as error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                if span.is_recording():
                    span.set_attribute(
                        error_attributes.ERROR_TYPE, type(error).__qualname__
                    )
                span.end()
                raise

    return traced_method_stream


@overload
def create_sync_wrapper(
    tracer: Tracer,
    get_span_attributes: GetSpanAttributes[ClientT],
    process_messages: ProcessMessages,
    process_response: ProcessResponse[ResponseT],
    create_stream_wrapper: CreateStreamWrapper[StreamChunkT, MetadataT] | None,
    handle_stream: Literal[False],
) -> SyncCompletionHandler[P, ResponseT, ClientT]: ...


@overload
def create_sync_wrapper(
    tracer: Tracer,
    get_span_attributes: GetSpanAttributes[ClientT],
    process_messages: ProcessMessages,
    process_response: ProcessResponse[ResponseT],
    create_stream_wrapper: CreateStreamWrapper[StreamChunkT, MetadataT] | None,
    handle_stream: Literal[True],
) -> SyncStreamHandler[P, StreamChunkT, MetadataT, ClientT]: ...


def create_sync_wrapper(
    tracer: Tracer,
    get_span_attributes: GetSpanAttributes[ClientT],
    process_messages: ProcessMessages,
    process_response: ProcessResponse[ResponseT],
    create_stream_wrapper: CreateStreamWrapper[StreamChunkT, MetadataT] | None,
    handle_stream: bool,
) -> (
    SyncCompletionHandler[P, ResponseT, ClientT]
    | SyncStreamHandler[P, StreamChunkT, MetadataT, ClientT]
):
    """Returns a synchronous wrapper for LLM API calls."""
    if handle_stream:
        return _create_sync_stream_wrapper(
            tracer,
            get_span_attributes,
            process_messages,
            process_response,
            create_stream_wrapper,
        )
    else:
        return _create_sync_completion_wrapper(
            tracer, get_span_attributes, process_messages, process_response
        )


@overload
def create_async_wrapper(
    tracer: Tracer,
    get_span_attributes: GetSpanAttributes[ClientT],
    process_messages: ProcessMessages,
    process_response: ProcessResponse[ResponseT],
    create_async_stream_wrapper: CreateAsyncStreamWrapper[StreamChunkT, MetadataT]
    | None,
    handle_stream: Literal[False],
) -> AsyncCompletionHandler[P, ResponseT, ClientT]: ...


@overload
def create_async_wrapper(
    tracer: Tracer,
    get_span_attributes: GetSpanAttributes[ClientT],
    process_messages: ProcessMessages,
    process_response: ProcessResponse[ResponseT],
    create_async_stream_wrapper: CreateAsyncStreamWrapper[StreamChunkT, MetadataT]
    | None,
    handle_stream: Literal[True],
) -> AsyncStreamHandler[P, StreamChunkT, MetadataT, ClientT]: ...


def create_async_wrapper(
    tracer: Tracer,
    get_span_attributes: GetSpanAttributes[ClientT],
    process_messages: ProcessMessages,
    process_response: ProcessResponse[ResponseT],
    create_async_stream_wrapper: CreateAsyncStreamWrapper[StreamChunkT, MetadataT]
    | None,
    handle_stream: bool,
) -> (
    AsyncCompletionHandler[P, ResponseT, ClientT]
    | AsyncStreamHandler[P, StreamChunkT, MetadataT, ClientT]
):
    """Returns an asynchronous wrapper for LLM API calls."""
    if handle_stream:
        return _create_async_stream_handler(
            tracer,
            get_span_attributes,
            process_messages,
            process_response,
            create_async_stream_wrapper,
        )
    else:
        return _create_async_completion_wrapper(
            tracer, get_span_attributes, process_messages, process_response
        )
