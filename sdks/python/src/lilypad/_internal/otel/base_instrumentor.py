"""The `BaseInstrumentor` abstract class for instrumenting provider clients."""

import logging
from abc import ABC, abstractmethod
from collections.abc import Iterator
from contextlib import contextmanager
from importlib.metadata import PackageNotFoundError, version
from typing import Any, Generic, cast, overload

from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.semconv.schemas import Schemas
from opentelemetry.trace import Span, SpanKind, Status, StatusCode, Tracer, get_tracer
from wrapt import FunctionWrapper

from .stream_wrappers import AsyncStream, AsyncStreamWrapper, Stream, StreamWrapper
from .types import (
    AsyncMethodWrapper,
    BoundAsyncMethod,
    BoundMethod,
    ChoiceDelta,
    ChoiceEvent,
    ClientT,
    GenAIRequestAttributes,
    GenAIResponseAttributes,
    KwargsT,
    MessageEvent,
    MethodWrapper,
    P,
    ResponseT,
    StreamChunkT,
)

logger = logging.getLogger(__name__)


class BaseInstrumentor(Generic[ClientT, KwargsT, ResponseT, StreamChunkT], ABC):
    """[MISSING DOCSTRING]"""

    tracer: Tracer
    """[MISSING DOCSTRING]"""

    def __init__(self) -> None:
        """[MISSING DOCSTRING]"""
        try:
            lilypad_version = version("lilypad-sdk")
        except PackageNotFoundError:  # pragma: no cover
            lilypad_version = "unknown"
            logger.debug("Could not determine lilypad-sdk version")

        self.tracer = get_tracer(
            __name__,
            lilypad_version,
            schema_url=Schemas.V1_28_0.value,
        )

    @contextmanager
    def _span(self, attributes: GenAIRequestAttributes) -> Iterator[Span]:
        """[MISSING DOCSTRING]"""
        with self.tracer.start_as_current_span(
            name=f"{attributes.GEN_AI_OPERATION_NAME} {attributes.GEN_AI_REQUEST_MODEL or 'unknown'}",
            kind=SpanKind.CLIENT,
            attributes=attributes.dump(),
            end_on_exit=False,
        ) as span:
            yield span

    @overload
    @staticmethod
    def _wrap(
        method: BoundMethod[P, ResponseT],
        wrapper: MethodWrapper[P, ResponseT, ClientT],
    ) -> None:
        """[MISSING DOCSTRING]"""
        ...

    @overload
    @staticmethod
    def _wrap(
        method: BoundAsyncMethod[P, ResponseT],
        wrapper: AsyncMethodWrapper[P, ResponseT, ClientT],
    ) -> None:
        """[MISSING DOCSTRING]"""
        ...

    @staticmethod
    def _wrap(
        method: BoundMethod[P, ResponseT] | BoundAsyncMethod[P, ResponseT],
        wrapper: MethodWrapper[P, ResponseT, ClientT]
        | AsyncMethodWrapper[P, ResponseT, ClientT],
    ) -> None:
        """[MISSING DOCSTRING]"""
        parent = method.__self__
        name = method.__name__
        target = f"{parent.__class__.__name__}.{name}"
        try:
            setattr(parent, name, FunctionWrapper(method, wrapper))
            logger.debug(f"Successfully wrapped {target}")
        except Exception as e:  # pragma: no cover
            logger.warning(f"Failed to wrap {target}. {type(e).__name__}: {e}")

    def instrument_generate(
        self,
        method: BoundMethod[P, ResponseT],
    ) -> None:
        """[MISSING DOCSTRING]"""

        def wrapper(
            wrapped: BoundMethod[P, ResponseT],
            client: ClientT,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> ResponseT:
            provider_kwargs = cast(KwargsT, kwargs)
            request_attributes = self._get_request_attributes(provider_kwargs, client)
            with self._span(request_attributes) as span:
                if span.is_recording():
                    for event in self._process_messages(provider_kwargs):
                        span.add_event(**event.dump())
                try:
                    response = wrapped(*args, **kwargs)
                    if isinstance(response, Stream):
                        stream_wrapper = StreamWrapper[StreamChunkT](
                            span, response, self._process_chunk
                        )
                        return cast(ResponseT, stream_wrapper)
                    if span.is_recording():
                        choice_events, response_attributes = self._process_response(
                            response
                        )
                        for event in choice_events:
                            span.add_event(**event.dump())
                        span.set_attributes(response_attributes.dump())
                    span.end()
                    return response
                except Exception as e:  # pragma: no cover
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    if span.is_recording():
                        span.set_attribute(
                            error_attributes.ERROR_TYPE, type(e).__qualname__
                        )
                    span.end()
                    raise

        self._wrap(method, wrapper)

    def instrument_async_generate(
        self,
        method: BoundAsyncMethod[P, ResponseT],
    ) -> None:
        """[MISSING DOCSTRING]"""

        async def wrapper(
            wrapped: BoundAsyncMethod[P, ResponseT],
            client: ClientT,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> ResponseT:
            provider_kwargs = cast(KwargsT, kwargs)
            request_attributes = self._get_request_attributes(provider_kwargs, client)
            with self._span(request_attributes) as span:
                if span.is_recording():
                    for event in self._process_messages(provider_kwargs):
                        span.add_event(**event.dump())
                try:
                    response = await wrapped(*args, **kwargs)
                    if isinstance(response, AsyncStream):
                        async_stream_wrapper = AsyncStreamWrapper[StreamChunkT](
                            span, response, self._process_chunk
                        )
                        return cast(ResponseT, async_stream_wrapper)
                    if span.is_recording():
                        choice_events, response_attributes = self._process_response(
                            response
                        )
                        for event in choice_events:
                            span.add_event(**event.dump())
                        span.set_attributes(response_attributes.dump())
                    span.end()
                    return response
                except Exception as e:  # pragma: no cover
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    if span.is_recording():
                        span.set_attribute(
                            error_attributes.ERROR_TYPE, type(e).__qualname__
                        )
                    span.end()
                    raise

        self._wrap(method, wrapper)

    @staticmethod
    @abstractmethod
    def _get_request_attributes(
        kwargs: KwargsT,
        client: ClientT,
    ) -> GenAIRequestAttributes:
        """[MISSING DOCSTRING]"""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _process_messages(
        kwargs: KwargsT,
    ) -> list[MessageEvent]:
        """[MISSING DOCSTRING]"""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _process_response(
        response: ResponseT,
    ) -> tuple[list[ChoiceEvent], GenAIResponseAttributes]:
        """[MISSING DOCSTRING]"""
        raise NotImplementedError

    @staticmethod
    @abstractmethod
    def _process_chunk(
        chunk: StreamChunkT,
    ) -> tuple[GenAIResponseAttributes, list[ChoiceDelta]]:
        """[MISSING DOCSTRING]"""
        raise NotImplementedError
