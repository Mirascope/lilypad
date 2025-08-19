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
ContravariantStreamChunkT = TypeVar("ContravariantStreamChunkT", contravariant=True)
MetadataT = TypeVar("MetadataT", bound=BaseMetadata)
ContravariantMetadataT = TypeVar(
    "ContravariantMetadataT", bound=BaseMetadata, contravariant=True
)
ClientT = TypeVar("ClientT")
ContravariantClientT = TypeVar("ContravariantClientT", contravariant=True)


class SyncCompletionHandler(Protocol[P, ResponseT, ContravariantClientT]):
    """Protocol for synchronous non-streaming completion handlers."""

    def __call__(
        self,
        wrapped: Callable[P, ResponseT],
        client: ContravariantClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ResponseT: ...


class SyncStreamHandler(Protocol[P, StreamChunkT, MetadataT, ContravariantClientT]):
    """Protocol for synchronous streaming handlers."""

    def __call__(
        self,
        wrapped: Callable[P, StreamProtocol[StreamChunkT]],
        client: ContravariantClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> StreamWrapper[StreamChunkT, MetadataT]: ...


class AsyncCompletionHandler(Protocol[P, ResponseT, ContravariantClientT]):
    """Protocol for asynchronous non-streaming completion handlers."""

    async def __call__(
        self,
        wrapped: Callable[P, Awaitable[ResponseT]],
        client: ContravariantClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ResponseT: ...


class AsyncStreamHandler(Protocol[P, StreamChunkT, MetadataT, ContravariantClientT]):
    """Protocol for asynchronous streaming handlers."""

    async def __call__(
        self,
        wrapped: Callable[P, Awaitable[AsyncStreamProtocol[StreamChunkT]]],
        client: ContravariantClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> AsyncStreamWrapper[StreamChunkT, MetadataT]: ...


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


class ProviderUtilities(Protocol[ClientT, ResponseT, StreamChunkT, MetadataT]):
    """Protocol for provider-specific utilities necessary for method wrapping."""

    def get_span_attributes(
        self,
        kwargs: dict[str, Any],
        client: ClientT,
        operation_name: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
    ) -> dict[str, AttributeValue]:
        """The method for retrieving the span attributes."""
        ...

    def process_messages(
        self,
        span: Span,
        kwargs: dict[str, Any],
    ) -> None:
        """The method for processing provider-specific messages."""
        ...

    def process_response(
        self,
        span: Span,
        response: ResponseT,
    ) -> None:
        """The method for processing a provider-specific response."""
        ...

    def create_stream_wrapper()
