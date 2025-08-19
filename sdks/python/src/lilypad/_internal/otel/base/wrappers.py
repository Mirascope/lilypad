"""Common wrapper utilities for LLM provider instrumentation."""

from abc import ABC, abstractmethod
from typing import Any, Generic
from contextlib import contextmanager
from dataclasses import dataclass
from collections.abc import Callable, Iterator, Awaitable
from typing_extensions import Required, TypedDict

from opentelemetry.trace import Span, Status, Tracer, SpanKind, StatusCode
from opentelemetry.util.types import Attributes, AttributeValue
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


@dataclass(kw_only=True)
class BaseWrappers(Generic[ClientT, ResponseT], ABC):
    """The base class for wrapper utilities that each provider must implement."""

    tracer: Tracer
    """The tracer to user when wrapping methods."""

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

    @abstractmethod
    @staticmethod
    def _get_span_attributes(
        kwargs: dict[str, Any],
        client: ClientT,
        operation_name: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
    ) -> dict[str, AttributeValue]:
        """The method for extracting OpenTelemetry span attributes from a request."""
        raise NotImplementedError()

    @abstractmethod
    @staticmethod
    def _process_messages(span: Span, kwargs: dict[str, Any]) -> None:
        """Adds the OpenTelemetry events processed from the request to the span."""
        raise NotImplementedError()

    @abstractmethod
    @staticmethod
    def _process_response(span: Span, response: ResponseT) -> None:
        """Adds the OpenTelemetry attributes procesed from the response to the span."""
        raise NotImplementedError()

    # TODO: this shoudl likely handle streaming for clients that have `stream=True`?
    def traced_create(
        self,
        wrapped: Callable[P, ResponseT],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ResponseT:
        """Wrapper for syncrhonous LLM API calls."""
        span_attributes = self._get_span_attributes(kwargs, client)
        with self._span(span_attributes) as span:
            if span.is_recording():
                self._process_messages(span, kwargs)
            try:
                if create_stream_wrapper and kwargs.get("stream", False):
                    return create_stream_wrapper(span, wrapped(*args, **kwargs))
                result = wrapped(*args, **kwargs)
                if span.is_recording():
                    self._process_response(span, result)
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

    # TODO: this should likely handle streaming for clients that have `stream=True`?
    async def traced_async_create(
        self,
        wrapped: Callable[P, Awaitable[ResponseT]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ResponseT:
        span_attributes = self._get_span_attributes(kwargs, client)
        with self._span(span_attributes) as span:
            if span.is_recording():
                self._process_messages(span, kwargs)
            try:
                result = await wrapped(*args, **kwargs)
                if span.is_recording():
                    self._process_response(span, result)
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

    # TODO: update to properly handle clients with a `.stream` or equivalent method
    def traced_stream(
        self,
        wrapped: Callable[P, StreamProtocol[StreamChunkT]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> StreamWrapper[StreamChunkT, MetadataT]:
        raise NotImplementedError()

    # TODO: update to properly handle clients with a `.stream` or equivalent method
    async def traced_async_stream(
        self,
        wrapped: Callable[P, Awaitable[AsyncStreamProtocol[StreamChunkT]]],
        client: ClientT,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> AsyncStreamWrapper[StreamChunkT, MetadataT]:
        span_attributes = self._get_span_attributes(kwargs, client)
        with self._span(span_attributes) as span:
            if span.is_recording():
                self._process_messages(span, kwargs)
            try:
                if create_async_stream_wrapper and kwargs.get("stream", False):
                    stream = await wrapped(*args, **kwargs)
                    return await create_async_stream_wrapper(span, stream)
                result = await wrapped(*args, **kwargs)
                if span.is_recording():
                    self._process_response(span, result)
                span.end()
                # TODO: revisit this type error
                return result  # pyright: ignore[reportReturnType]
            except Exception as error:
                span.set_status(Status(StatusCode.ERROR, str(error)))
                if span.is_recording():
                    span.set_attribute(
                        error_attributes.ERROR_TYPE, type(error).__qualname__
                    )
                span.end()
                raise
