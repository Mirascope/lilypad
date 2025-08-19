"""Common wrapper utilities for LLM provider instrumentation."""

from abc import ABC, abstractmethod
from typing import Any, Generic, Protocol, NamedTuple, TypeVar
from contextlib import contextmanager
from dataclasses import dataclass, field
from collections.abc import Callable, Iterator, Awaitable
from typing_extensions import Self

from opentelemetry.trace import Span, Status, Tracer, SpanKind, StatusCode
from opentelemetry.util.types import AttributeValue
from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
import logging
from importlib.metadata import PackageNotFoundError, version

from wrapt import FunctionWrapper
from openai import OpenAI, AsyncOpenAI
from opentelemetry.trace import get_tracer
from opentelemetry.semconv.schemas import Schemas

from ..utils import (
    StreamWrapper,
    StreamProtocol,
    AsyncStreamWrapper,
    AsyncStreamProtocol,
    ChoiceBuffer,
)
from .protocols import (
    P,
    ClientT,
    MetadataT,
    ResponseT,
    StreamChunkT,
)

logger = logging.getLogger(__name__)


class _Method(Protocol[P, ResponseT]):
    __self__: Self

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> ResponseT: ...


MethodT = TypeVar("MethodT", bound=Callable)
ChunkT = TypeVar("ChunkT")
ChunkCovariantT = TypeVar("ChunkCovariantT", covariant=True)


class WrapTarget(NamedTuple):
    """Simple generic wrap target"""

    method: Callable
    wrapper: Callable


@dataclass(kw_only=True)
class TraceContext:
    """Simple sync context holder for trace execution"""

    span: Span
    result: Any = None

    def set_result(self, result: Any) -> None:
        self.result = result


@dataclass(kw_only=True)
class BaseInstrumentor(Generic[ClientT, ResponseT, ChunkCovariantT, MetadataT], ABC):
    """The base class for wrapper utilities that each provider must implement."""

    tracer: Tracer = field(init=False)
    """The tracer to user when wrapping methods."""

    def __post_init__(self) -> None:
        try:
            lilypad_version = version("lilypad-sdk")
        except PackageNotFoundError:
            lilypad_version = "unknown"
            logger.debug("Could not determine lilypad-sdk version")

        self.tracer = get_tracer(
            __name__,
            lilypad_version,
            schema_url=Schemas.V1_28_0.value,
        )

    @staticmethod
    def _wrap_method(
        method: _Method[P, ResponseT], wrapper: Callable[P, ResponseT]
    ) -> None:
        """Wrap a method with error handling and logging."""
        if not (hasattr(method, "__self__") and hasattr(method, "__name__")):
            logger.error(f"Cannot wrap non-bound method: {method}")
            return

        parent = method.__self__
        name = method.__name__
        target = f"{parent.__class__.__name__}.{name}"

        try:
            setattr(parent, name, FunctionWrapper(method, wrapper))
            logger.debug(f"Successfully wrapped {target}")
        except Exception as e:
            logger.warning(f"Failed to wrap {target}: {type(e).__name__}: {e}")

    @abstractmethod
    def _get_async_targets(self, client: AsyncOpenAI) -> list[WrapTarget]:
        """Type-preserving wrap targets"""
        raise NotImplementedError()

    @abstractmethod
    def _get_sync_targets(self, client: OpenAI) -> list[WrapTarget]:
        """Type-preserving wrap targets"""
        raise NotImplementedError()

    @abstractmethod
    def _is_async_client(self, client: ClientT) -> bool:
        """Type-preserving wrap targets"""
        raise NotImplementedError()

    @classmethod
    def instrument(cls, client: ClientT) -> None:
        """
        Instrument the OpenAI client with OpenTelemetry tracing.

        Args:
            client: The OpenAI client instance to instrument.
        """
        if hasattr(client, "_lilypad_instrumented"):
            logger.debug(f"{type(client).__name__} already instrumented, skipping")
            return

        instrumentor = cls()

        if instrumentor._is_async_client(client):
            for target in instrumentor._get_async_targets(client):
                instrumentor._wrap_method(target.method, target.wrapper)
        else:
            for target in instrumentor._get_sync_targets(client):
                instrumentor._wrap_method(target.method, target.wrapper)

        client._lilypad_instrumented = True  # pyright: ignore[reportAttributeAccessIssue]

    @contextmanager
    def _span(
        self,
        span_attributes: dict[str, AttributeValue],
    ) -> Iterator[Span]:
        """Yields an OpenTelemertry span for LLM operations."""
        operation_name = span_attributes.get(
            gen_ai_attributes.GEN_AI_OPERATION_NAME, "unknown"
        )
        model_name = span_attributes.get(
            gen_ai_attributes.GEN_AI_REQUEST_MODEL, "unknown"
        )
        span_name = f"{operation_name} {model_name}"

        with self.tracer.start_as_current_span(
            name=span_name,
            kind=SpanKind.CLIENT,
            attributes=span_attributes,
            end_on_exit=False,
        ) as span:
            yield span

    @staticmethod
    @abstractmethod
    def _get_span_attributes(
        kwargs: dict[str, Any],
        client: ClientT,
        operation_name: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
    ) -> dict[str, AttributeValue]:
        """The method for extracting OpenTelemetry span attributes from a request."""
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def _process_messages(span: Span, kwargs: dict[str, Any]) -> None:
        """Adds the OpenTelemetry events processed from the request to the span."""
        raise NotImplementedError()

    @staticmethod
    @abstractmethod
    def _process_response(span: Span, response: ResponseT) -> None:
        """Adds the OpenTelemetry attributes procesed from the response to the span."""
        raise NotImplementedError()

    @abstractmethod
    def extract_metadata(self, chunk: ChunkT, metadata: MetadataT) -> None:
        """Extract metadata from chunk and update StreamMetadata"""
        raise NotImplementedError()

    @abstractmethod
    def process_chunk(self, chunk: ChunkT, buffers: list[ChoiceBuffer]) -> None:
        """Process chunk and update choice buffers"""
        raise NotImplementedError()

    @abstractmethod
    def create_metadata(self) -> MetadataT:
        """Return metadata for the stream"""
        raise NotImplementedError()

    @abstractmethod
    def cleanup_stream_handler(
        self, span: Span, metadata: MetadataT, choice_buffers: list[ChoiceBuffer]
    ) -> None:
        """Cleanup handler for the stream"""
        raise NotImplementedError()

    def create_stream_wrapper(
        self, span: Span, stream: StreamProtocol[ChunkCovariantT]
    ) -> StreamWrapper[ChunkCovariantT, MetadataT]:
        """Create a stream wrapper."""
        return StreamWrapper(
            span=span,
            stream=stream,
            extract_metadata=self.extract_metadata,
            process_chunk=self.process_chunk,
            metadata=self.create_metadata(),
            cleanup_handler=self.cleanup_stream_handler,
        )

    def create_async_stream_wrapper(
        self, span: Span, stream: AsyncStreamProtocol[ChunkCovariantT]
    ) -> AsyncStreamWrapper[ChunkCovariantT, MetadataT]:
        """Create a stream wrapper."""
        return AsyncStreamWrapper(
            span=span,
            stream=stream,
            extract_metadata=self.extract_metadata,
            process_chunk=self.process_chunk,
            metadata=self.create_metadata(),
            cleanup_handler=self.cleanup_stream_handler,
        )

    @contextmanager
    def _trace_context(
        self,
        client: ClientT,
        kwargs: dict[str, Any],
        is_streaming: bool = False,
    ) -> Iterator[TraceContext]:
        """Context manager that processes result on exit"""
        span_attributes = self._get_span_attributes(kwargs, client)

        with self._span(span_attributes) as span:
            is_recording = span.is_recording()

            if is_recording:
                self._process_messages(span, kwargs)

            ctx = TraceContext(span=span)

            try:
                yield ctx
                if is_streaming:
                    return
                if ctx.result is not None:
                    if is_streaming:
                        return
                    if is_recording:
                        self._process_response(span, ctx.result)
                span.end()

            except Exception as error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                if is_recording:
                    span.set_attribute(
                        error_attributes.ERROR_TYPE, type(error).__qualname__
                    )
                span.end()
                raise

    def traced_create(
        self,
        wrapped: Callable[P, ResponseT],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ResponseT:
        """Wrapper for synchronous LLM API calls."""
        is_streaming = kwargs.get("stream", False)
        with self._trace_context(client, kwargs, is_streaming) as ctx:
            result = wrapped(*args, **kwargs)
            if is_streaming:
                return self.create_stream_wrapper(ctx.span, result)
            ctx.set_result(result)
            return result

    async def traced_async_create(
        self,
        wrapped: Callable[P, Awaitable[ResponseT]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ResponseT:
        is_streaming = kwargs.get("stream", False)
        with self._trace_context(client, kwargs, is_streaming) as ctx:
            result = await wrapped(*args, **kwargs)
            if is_streaming:
                return self.create_async_stream_wrapper(ctx.span, result)
            ctx.set_result(result)
            return result

    def traced_stream(
        self,
        wrapped: Callable[P, StreamProtocol[StreamChunkT]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> StreamWrapper[StreamChunkT, MetadataT]:
        with self._trace_context(client, kwargs, is_streaming=True) as ctx:
            result = wrapped(*args, **kwargs)
            return self.create_stream_wrapper(ctx.span, result)

    async def traced_async_stream(
        self,
        wrapped: Callable[P, Awaitable[AsyncStreamProtocol[StreamChunkT]]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> AsyncStreamWrapper[StreamChunkT, MetadataT]:
        with self._trace_context(client, kwargs, is_streaming=True) as ctx:
            result = await wrapped(*args, **kwargs)
            return self.create_async_stream_wrapper(ctx.span, result)
