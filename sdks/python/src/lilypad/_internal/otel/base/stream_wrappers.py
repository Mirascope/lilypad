"""Stream-specific wrapper factories for OpenTelemetry instrumentation.

This module provides dedicated wrapper factories for stream-only methods that don't
mix streaming and non-streaming logic.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar, Awaitable, cast

from opentelemetry.trace import Span, Tracer, Status, StatusCode
from typing_extensions import ParamSpec

from .protocols import (
    GetSpanAttributes,
    ProcessMessages,
    SyncStreamHandler,
    AsyncStreamHandler,
)
from ..utils import (
    StreamWrapper,
    AsyncStreamWrapper,
    BaseMetadata,
    ChunkHandler,
    StreamProtocol,
    AsyncStreamProtocol,
)

P = ParamSpec("P")
ClientT = TypeVar("ClientT")
StreamChunkT = TypeVar("StreamChunkT")
MetadataT = TypeVar("MetadataT", bound=BaseMetadata)


def create_stream_method_wrapper(
    tracer: Tracer,
    get_span_attributes: GetSpanAttributes[ClientT],
    process_messages: ProcessMessages,
    metadata_factory: Callable[[], MetadataT],
    chunk_handler_factory: Callable[[], ChunkHandler[StreamChunkT, MetadataT]],
    cleanup_handler: Callable[[Span, MetadataT, list[Any]], None],
    span_name_prefix: str = "llm",
) -> SyncStreamHandler[P, StreamChunkT, MetadataT, ClientT]:
    """Create a synchronous stream method wrapper."""

    def traced_stream_method(
        wrapped: Callable[P, StreamProtocol[StreamChunkT]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> StreamWrapper[StreamChunkT, MetadataT]:
        span_attributes = get_span_attributes(kwargs, client, "chat")

        method_name = getattr(wrapped, "__name__", "unknown")
        span_name = f"{span_name_prefix}.{method_name}"
        span = tracer.start_span(span_name, attributes=span_attributes)
        try:
            process_messages(span, kwargs)

            stream = wrapped(*args, **kwargs)

            return StreamWrapper(
                span=span,
                stream=stream,
                metadata=metadata_factory(),
                chunk_handler=chunk_handler_factory(),
                cleanup_handler=cleanup_handler,
            )
        except Exception as error:
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.end()
            raise

    return cast(
        SyncStreamHandler[P, StreamChunkT, MetadataT, ClientT], traced_stream_method
    )


def create_async_stream_method_wrapper(
    tracer: Tracer,
    get_span_attributes: GetSpanAttributes[ClientT],
    process_messages: ProcessMessages,
    metadata_factory: Callable[[], MetadataT],
    chunk_handler_factory: Callable[[], ChunkHandler[StreamChunkT, MetadataT]],
    cleanup_handler: Callable[[Span, MetadataT, list[Any]], None],
    span_name_prefix: str = "llm",
) -> AsyncStreamHandler[P, StreamChunkT, MetadataT, ClientT]:
    """Create an asynchronous stream method wrapper."""

    async def traced_async_stream_method(
        wrapped: Callable[P, Awaitable[AsyncStreamProtocol[StreamChunkT]]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> AsyncStreamWrapper[StreamChunkT, MetadataT]:
        span_attributes = get_span_attributes(kwargs, client, "chat")

        method_name = getattr(wrapped, "__name__", "unknown")
        span_name = f"{span_name_prefix}.{method_name}"
        span = tracer.start_span(span_name, attributes=span_attributes)
        try:
            process_messages(span, kwargs)

            stream = await wrapped(*args, **kwargs)

            return AsyncStreamWrapper(
                span=span,
                stream=stream,
                metadata=metadata_factory(),
                chunk_handler=chunk_handler_factory(),
                cleanup_handler=cleanup_handler,
            )
        except Exception as error:
            span.record_exception(error)
            span.set_status(Status(StatusCode.ERROR, str(error)))
            span.end()
            raise

    return cast(
        AsyncStreamHandler[P, StreamChunkT, MetadataT, ClientT],
        traced_async_stream_method,
    )
