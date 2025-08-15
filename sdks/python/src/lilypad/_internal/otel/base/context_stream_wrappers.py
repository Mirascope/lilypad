"""Context manager-based stream wrapper factories for OpenTelemetry instrumentation."""

from __future__ import annotations

from typing import (
    Any,
    Callable,
    TypeVar,
    ContextManager,
    AsyncContextManager,
    Iterator,
    AsyncIterator,
    Protocol,
)
from contextlib import contextmanager, asynccontextmanager

from opentelemetry.trace import Span, Tracer, Status, StatusCode
from typing_extensions import ParamSpec

from .protocols import GetSpanAttributes, ProcessMessages
from ..utils import (
    BaseMetadata,
    ChunkHandler,
    StreamProtocol,
    AsyncStreamProtocol,
    ChoiceBuffer,
)

P = ParamSpec("P")
ClientT = TypeVar("ClientT")
ClientT_contra = TypeVar("ClientT_contra", contravariant=True)
StreamChunkT = TypeVar("StreamChunkT")
StreamChunkT_co = TypeVar("StreamChunkT_co", covariant=True)
MetadataT = TypeVar("MetadataT", bound=BaseMetadata, covariant=True)


class ContextStreamHandler(Protocol[P, StreamChunkT, ClientT_contra]):
    """Protocol for context manager stream handlers."""

    def __call__(
        self,
        wrapped: Callable[P, ContextManager[MessageStream[StreamChunkT]]],
        client: ClientT_contra,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ContextManager[MessageStream[StreamChunkT]]: ...


class AsyncContextStreamHandler(Protocol[P, StreamChunkT, ClientT_contra]):
    """Protocol for async context manager stream handlers."""

    def __call__(
        self,
        wrapped: Callable[P, AsyncContextManager[AsyncMessageStream[StreamChunkT]]],
        client: ClientT_contra,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> AsyncContextManager[AsyncMessageStream[StreamChunkT]]: ...


class MessageStream(StreamProtocol[StreamChunkT_co], Protocol[StreamChunkT_co]):
    """Protocol for message streams returned by context managers."""

    @property
    def text_stream(self) -> Iterator[str]: ...


class AsyncMessageStream(
    AsyncStreamProtocol[StreamChunkT_co], Protocol[StreamChunkT_co]
):
    """Protocol for async message streams returned by context managers."""

    @property
    def text_stream(self) -> AsyncIterator[str]: ...


def create_context_stream_wrapper(
    tracer: Tracer,
    get_span_attributes: GetSpanAttributes[ClientT],
    process_messages: ProcessMessages,
    metadata_factory: Callable[[], MetadataT],
    chunk_handler_factory: Callable[[], ChunkHandler[StreamChunkT, MetadataT]],
    cleanup_handler: Callable[[Span, MetadataT, list[ChoiceBuffer]], None],
    span_name_prefix: str = "llm",
) -> ContextStreamHandler[P, StreamChunkT, ClientT]:
    """Create a wrapper for stream methods that return context managers."""

    def traced_context_stream_method(
        wrapped: Callable[P, ContextManager[MessageStream[StreamChunkT]]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ContextManager[MessageStream[StreamChunkT]]:
        span_attributes = get_span_attributes(kwargs, client, "chat")
        method_name = getattr(wrapped, "__name__", "unknown")
        span_name = f"{span_name_prefix}.{method_name}"

        stream_manager = wrapped(*args, **kwargs)  # type: ignore[arg-type]

        @contextmanager
        def instrumented_stream_manager() -> Iterator[MessageStream[StreamChunkT]]:
            span = tracer.start_span(span_name, attributes=span_attributes)
            try:
                process_messages(span, kwargs)
                with stream_manager as stream:
                    metadata = metadata_factory()
                    chunk_handler = chunk_handler_factory()
                    choice_buffers: list[ChoiceBuffer] = []
                    events_cache: list[StreamChunkT] = []

                    class MessageStreamWrapper:
                        def __init__(
                            self, stream_obj: MessageStream[StreamChunkT]
                        ) -> None:
                            self._stream = stream_obj
                            self._text_stream_wrapper: Iterator[str] | None = None

                        def __iter__(self) -> Iterator[StreamChunkT]:
                            for event in self._stream:
                                chunk_handler.extract_metadata(event, metadata)
                                chunk_handler.process_chunk(event, choice_buffers)
                                events_cache.append(event)
                                yield event

                        def __next__(self) -> StreamChunkT:
                            event = next(iter(self._stream))
                            chunk_handler.extract_metadata(event, metadata)
                            chunk_handler.process_chunk(event, choice_buffers)
                            events_cache.append(event)
                            return event

                        def close(self) -> None:
                            close_fn = getattr(self._stream, "close", None)
                            if close_fn:
                                close_fn()

                        @property
                        def text_stream(self) -> Iterator[str]:
                            if self._text_stream_wrapper is None:

                                def wrapped_text_stream() -> Iterator[str]:
                                    for event in self:
                                        if (
                                            getattr(event, "type", None)
                                            == "content_block_delta"
                                        ):
                                            delta = getattr(event, "delta", None)
                                            if delta and hasattr(delta, "text"):
                                                text = delta.text  # type: ignore[arg-type]
                                                if text:
                                                    yield text

                                self._text_stream_wrapper = wrapped_text_stream()
                            return self._text_stream_wrapper

                        def __getattr__(self, name: str) -> Any:
                            return getattr(self._stream, name)

                        def finalize(self) -> None:
                            if not events_cache:
                                try:
                                    for event in self._stream:
                                        chunk_handler.extract_metadata(event, metadata)
                                        chunk_handler.process_chunk(
                                            event, choice_buffers
                                        )
                                        events_cache.append(event)
                                except (StopIteration, RuntimeError):
                                    ...

                            if cleanup_handler:
                                cleanup_handler(span, metadata, choice_buffers)

                    wrapper = MessageStreamWrapper(stream)
                    try:
                        yield wrapper  # type: ignore[misc]
                    finally:
                        wrapper.finalize()
                        span.end()
            except Exception as error:
                span.record_exception(error)
                span.set_status(Status(StatusCode.ERROR, str(error)))
                span.end()
                raise

        return instrumented_stream_manager()

    return traced_context_stream_method


def create_async_context_stream_wrapper(
    tracer: Tracer,
    get_span_attributes: GetSpanAttributes[ClientT],
    process_messages: ProcessMessages,
    metadata_factory: Callable[[], MetadataT],
    chunk_handler_factory: Callable[[], ChunkHandler[StreamChunkT, MetadataT]],
    cleanup_handler: Callable[[Span, MetadataT, list[ChoiceBuffer]], None],
    span_name_prefix: str = "llm",
) -> AsyncContextStreamHandler[P, StreamChunkT, ClientT]:
    """Create a wrapper for async stream methods that return context managers."""

    def traced_async_context_stream_method(
        wrapped: Callable[P, AsyncContextManager[AsyncMessageStream[StreamChunkT]]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> AsyncContextManager[AsyncMessageStream[StreamChunkT]]:
        span_attributes = get_span_attributes(kwargs, client, "chat")
        method_name = getattr(wrapped, "__name__", "unknown")
        span_name = f"{span_name_prefix}.{method_name}"

        stream_manager = wrapped(*args, **kwargs)  # type: ignore[arg-type]

        @asynccontextmanager
        async def instrumented_stream_manager() -> AsyncIterator[
            AsyncMessageStream[StreamChunkT]
        ]:
            span = tracer.start_span(span_name, attributes=span_attributes)
            try:
                process_messages(span, kwargs)
                async with stream_manager as stream:
                    metadata = metadata_factory()
                    chunk_handler = chunk_handler_factory()
                    choice_buffers: list[ChoiceBuffer] = []
                    events_cache: list[StreamChunkT] = []

                    class AsyncMessageStreamWrapper:
                        def __init__(
                            self, stream_obj: AsyncMessageStream[StreamChunkT]
                        ) -> None:
                            self._stream = stream_obj
                            self._text_stream_wrapper: AsyncIterator[str] | None = None
                            self._iterator: AsyncIterator[StreamChunkT] | None = None

                        def __aiter__(self) -> AsyncMessageStreamWrapper:
                            return self

                        async def __anext__(self) -> StreamChunkT:
                            if self._iterator is None:
                                self._iterator = self._stream.__aiter__()
                            event = await self._iterator.__anext__()
                            chunk_handler.extract_metadata(event, metadata)
                            chunk_handler.process_chunk(event, choice_buffers)
                            events_cache.append(event)
                            return event

                        async def aclose(self) -> None:
                            aclose_fn = getattr(self._stream, "aclose", None)
                            if aclose_fn:
                                await aclose_fn()

                        @property
                        def text_stream(self) -> AsyncIterator[str]:
                            if self._text_stream_wrapper is None:

                                async def wrapped_text_stream() -> AsyncIterator[str]:
                                    async for event in self:
                                        if (
                                            getattr(event, "type", None)
                                            == "content_block_delta"
                                        ):
                                            delta = getattr(event, "delta", None)
                                            if delta and hasattr(delta, "text"):
                                                text = delta.text  # type: ignore[arg-type]
                                                if text:
                                                    yield text

                                self._text_stream_wrapper = wrapped_text_stream()
                            return self._text_stream_wrapper

                        def __getattr__(self, name: str) -> Any:
                            return getattr(self._stream, name)

                        async def finalize(self) -> None:
                            if not events_cache:
                                try:
                                    async for event in self._stream:
                                        chunk_handler.extract_metadata(event, metadata)
                                        chunk_handler.process_chunk(
                                            event, choice_buffers
                                        )
                                        events_cache.append(event)
                                except (StopAsyncIteration, RuntimeError):
                                    ...

                            if cleanup_handler:
                                cleanup_handler(span, metadata, choice_buffers)

                    wrapper = AsyncMessageStreamWrapper(stream)
                    try:
                        yield wrapper  # type: ignore[misc]
                    finally:
                        await wrapper.finalize()
                        span.end()
            except Exception as error:
                span.record_exception(error)
                span.set_status(Status(StatusCode.ERROR, str(error)))
                span.end()
                raise

        return instrumented_stream_manager()

    return traced_async_context_stream_method
