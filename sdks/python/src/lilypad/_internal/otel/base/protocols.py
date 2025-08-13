"""Common protocol definitions for LLM provider instrumentation."""

from typing import Any, TypeVar, Protocol, ParamSpec
from collections.abc import Callable, Awaitable

from opentelemetry.trace import Span
from opentelemetry.util.types import AttributeValue
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from ..utils import (
    BaseMetadata,
    StreamWrapper,
    StreamProtocol,
    AsyncStreamWrapper,
    AsyncStreamProtocol,
)

P = ParamSpec("P")
ResponseT = TypeVar("ResponseT")
ContravariantResponseT = TypeVar("ContravariantResponseT", contravariant=True)
StreamChunkT = TypeVar("StreamChunkT")
MetadataT = TypeVar("MetadataT", bound=BaseMetadata)
ClientT = TypeVar("ClientT", contravariant=True)


class SyncCompletionHandler(Protocol[P, ResponseT, ClientT]):
    """Protocol for synchronous non-streaming completion handlers."""

    def __call__(
        self,
        wrapped: Callable[P, ResponseT],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ResponseT: ...


class SyncStreamHandler(Protocol[P, StreamChunkT, MetadataT, ClientT]):
    """Protocol for synchronous streaming handlers."""

    def __call__(
        self,
        wrapped: Callable[P, StreamProtocol[StreamChunkT]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> StreamWrapper[StreamChunkT, MetadataT]: ...


class AsyncCompletionHandler(Protocol[P, ResponseT, ClientT]):
    """Protocol for asynchronous non-streaming completion handlers."""

    async def __call__(
        self,
        wrapped: Callable[P, Awaitable[ResponseT]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ResponseT: ...


class AsyncStreamHandler(Protocol[P, StreamChunkT, MetadataT, ClientT]):
    """Protocol for asynchronous streaming handlers."""

    async def __call__(
        self,
        wrapped: Callable[P, Awaitable[AsyncStreamProtocol[StreamChunkT]]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> AsyncStreamWrapper[StreamChunkT, MetadataT]: ...


class GetSpanAttributes(Protocol[ClientT]):
    """Protocol for the `get_span_attributes` method."""

    def __call__(
        self,
        kwargs: dict[str, Any],
        client: ClientT,
        operation_name: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
    ) -> dict[str, AttributeValue]: ...


class ProcessMessages(Protocol):
    """Protocol for the `process_messages` method."""

    def __call__(
        self,
        span: Span,
        kwargs: dict[str, Any],
    ) -> None: ...


class ProcessResponse(Protocol[ContravariantResponseT]):
    """Protocol for the `process_response` method."""

    def __call__(
        self,
        span: Span,
        response: ContravariantResponseT,
    ) -> None: ...


class CreateStreamWrapper(Protocol[StreamChunkT, MetadataT]):
    """Protocol for the `create_stream_wrapper` method."""

    def __call__(
        self, span: Span, stream: StreamProtocol[StreamChunkT]
    ) -> StreamWrapper[StreamChunkT, MetadataT]: ...


class CreateAsyncStreamWrapper(Protocol[StreamChunkT, MetadataT]):
    """Protocol for the `create_async_stream_wrapper` method."""

    def __call__(
        self, span: Span, stream: AsyncStreamProtocol[StreamChunkT]
    ) -> Awaitable[AsyncStreamWrapper[StreamChunkT, MetadataT]]: ...
