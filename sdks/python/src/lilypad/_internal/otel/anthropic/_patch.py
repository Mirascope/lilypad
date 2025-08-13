"""Patching utilities for Anthropic client methods to add OpenTelemetry instrumentation.

This module contains the core logic for wrapping Anthropic API calls with telemetry spans.
"""

from typing import (
    Any,
    Literal,
    Protocol,
    ParamSpec,
    cast,
    overload,
)
from contextlib import contextmanager
from collections.abc import Callable, Iterator, Awaitable

from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import Message, MessageStreamEvent
from opentelemetry.trace import Span, Status, Tracer, SpanKind, StatusCode
from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.semconv._incubating.attributes import (
    gen_ai_attributes,
)

from . import _utils
from ..utils import (
    StreamWrapper,
    StreamProtocol,
    AsyncStreamWrapper,
    AsyncStreamProtocol,
)

P = ParamSpec("P")


class SyncCompletionHandler(Protocol[P]):
    """Protocol for sync non-streaming handler."""

    def __call__(
        self,
        wrapped: Callable[P, Message],
        client: Anthropic,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Message: ...


class SyncStreamHandler(Protocol[P]):
    """Protocol for sync streaming handler."""

    def __call__(
        self,
        wrapped: Callable[P, StreamProtocol[MessageStreamEvent]],
        client: Anthropic,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> StreamWrapper[MessageStreamEvent, _utils.AnthropicMetadata]: ...


class AsyncCompletionHandler(Protocol[P]):
    """Protocol for async non-streaming handler."""

    async def __call__(
        self,
        wrapped: Callable[P, Awaitable[Message]],
        client: AsyncAnthropic,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> Message: ...


class AsyncStreamHandler(Protocol[P]):
    """Protocol for async streaming handler."""

    async def __call__(
        self,
        wrapped: Callable[P, Awaitable[AsyncStreamProtocol[MessageStreamEvent]]],
        client: AsyncAnthropic,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> AsyncStreamWrapper[MessageStreamEvent, _utils.AnthropicMetadata]: ...


@contextmanager
def _span(
    tracer: Tracer, kwargs: dict[str, Any], client: Anthropic | AsyncAnthropic
) -> Iterator[Span]:
    """Context manager for creating and managing OpenTelemetry spans."""
    span_attributes = {**_utils.get_llm_request_attributes(kwargs, client)}
    span_name = f"{span_attributes[gen_ai_attributes.GEN_AI_OPERATION_NAME]} {span_attributes.get(gen_ai_attributes.GEN_AI_REQUEST_MODEL, 'unknown')}"

    with tracer.start_as_current_span(
        name=span_name,
        kind=SpanKind.CLIENT,
        attributes=span_attributes,
        end_on_exit=False,
    ) as span:
        yield span


@overload
def _sync_wrapper(
    tracer: Tracer, handle_stream: Literal[False]
) -> SyncCompletionHandler[P]: ...


@overload
def _sync_wrapper(
    tracer: Tracer, handle_stream: Literal[True]
) -> SyncStreamHandler[P]: ...


def _sync_wrapper(
    tracer: Tracer, handle_stream: bool
) -> SyncCompletionHandler[P] | SyncStreamHandler[P]:
    """Internal sync wrapper for Anthropic API calls."""

    if not handle_stream:

        def traced_method_completion(
            wrapped: Callable[P, Message],
            client: Anthropic,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Message:
            with _span(tracer, kwargs, client) as span:
                if span.is_recording():
                    for message in kwargs.get("messages", []):
                        _utils.set_message_event(span, message)
                    if system := kwargs.get("system"):
                        _utils.set_message_event(
                            span,
                            _utils.SystemMessageParam(role="system", content=system),
                        )
                try:
                    result = wrapped(*args, **kwargs)
                    if span.is_recording():
                        _utils.set_response_attributes(span, result)
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
    else:

        def traced_method_stream(
            wrapped: Callable[P, StreamProtocol[MessageStreamEvent]],
            client: Anthropic,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> StreamWrapper[MessageStreamEvent, _utils.AnthropicMetadata]:
            with _span(tracer, kwargs, client) as span:
                if span.is_recording():
                    for message in kwargs.get("messages", []):
                        _utils.set_message_event(span, message)
                    if system := kwargs.get("system"):
                        _utils.set_message_event(
                            span,
                            _utils.SystemMessageParam(role="system", content=system),
                        )
                try:
                    if kwargs.get("stream", False):
                        return StreamWrapper(
                            span=span,
                            stream=wrapped(*args, **kwargs),
                            metadata=_utils.AnthropicMetadata(),
                            chunk_handler=_utils.AnthropicChunkHandler(),
                            cleanup_handler=_utils.default_anthropic_cleanup,
                        )
                    result = cast(Message, wrapped(*args, **kwargs))
                    if span.is_recording():
                        _utils.set_response_attributes(span, result)
                    span.end()
                    return cast(
                        StreamWrapper[MessageStreamEvent, _utils.AnthropicMetadata],
                        result,
                    )
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
def _async_wrapper(
    tracer: Tracer, handle_stream: Literal[False]
) -> AsyncCompletionHandler[P]: ...


@overload
def _async_wrapper(
    tracer: Tracer, handle_stream: Literal[True]
) -> AsyncStreamHandler[P]: ...


def _async_wrapper(
    tracer: Tracer, handle_stream: bool
) -> AsyncCompletionHandler[P] | AsyncStreamHandler[P]:
    """Internal async wrapper for Anthropic API calls."""

    if not handle_stream:

        async def traced_method_completion(
            wrapped: Callable[P, Awaitable[Message]],
            client: AsyncAnthropic,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> Message:
            with _span(tracer, kwargs, client) as span:
                if span.is_recording():
                    for message in kwargs.get("messages", []):
                        _utils.set_message_event(span, message)
                    if system := kwargs.get("system"):
                        _utils.set_message_event(
                            span,
                            _utils.SystemMessageParam(role="system", content=system),
                        )
                try:
                    result = await wrapped(*args, **kwargs)
                    if span.is_recording():
                        _utils.set_response_attributes(span, result)
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
    else:

        async def traced_method_stream(
            wrapped: Callable[P, Awaitable[AsyncStreamProtocol[MessageStreamEvent]]],
            client: AsyncAnthropic,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> AsyncStreamWrapper[MessageStreamEvent, _utils.AnthropicMetadata]:
            with _span(tracer, kwargs, client) as span:
                if span.is_recording():
                    for message in kwargs.get("messages", []):
                        _utils.set_message_event(span, message)
                    if system := kwargs.get("system"):
                        _utils.set_message_event(
                            span,
                            _utils.SystemMessageParam(role="system", content=system),
                        )
                try:
                    if kwargs.get("stream", False):
                        return AsyncStreamWrapper(
                            span=span,
                            stream=await wrapped(*args, **kwargs),
                            metadata=_utils.AnthropicMetadata(),
                            chunk_handler=_utils.AnthropicChunkHandler(),
                            cleanup_handler=_utils.default_anthropic_cleanup,
                        )
                    result = cast(Message, await wrapped(*args, **kwargs))
                    if span.is_recording():
                        _utils.set_response_attributes(span, result)
                    span.end()
                    return cast(
                        AsyncStreamWrapper[
                            MessageStreamEvent, _utils.AnthropicMetadata
                        ],
                        result,
                    )
                except Exception as error:
                    span.set_status(Status(StatusCode.ERROR, str(error)))
                    if span.is_recording():
                        span.set_attribute(
                            error_attributes.ERROR_TYPE, type(error).__qualname__
                        )
                    span.end()
                    raise

        return traced_method_stream


def messages_create_patch_factory(
    tracer: Tracer,
) -> SyncStreamHandler[P]:
    """Returns a patch factory for sync messages create method."""
    return _sync_wrapper(tracer, handle_stream=True)


def messages_create_async_patch_factory(
    tracer: Tracer,
) -> AsyncStreamHandler[P]:
    """Returns a patch factory for async messages create method."""
    return _async_wrapper(tracer, handle_stream=True)
