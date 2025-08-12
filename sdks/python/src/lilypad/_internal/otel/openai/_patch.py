"""Patching utilities for OpenAI client methods to add OpenTelemetry instrumentation.

This module contains the core logic for wrapping OpenAI API calls with telemetry spans.
"""

# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Modifications copyright (C) 2025 Mirascope

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

from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from opentelemetry.trace import Span, Status, Tracer, SpanKind, StatusCode
from opentelemetry.util.types import AttributeValue
from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.semconv._incubating.attributes import (
    gen_ai_attributes,
)

from .utils import (
    OpenAIMetadata,
    OpenAIChunkHandler,
    set_message_event,
    default_openai_cleanup,
    set_response_attributes,
)
from ..utils import (
    StreamWrapper,
    StreamProtocol,
    AsyncStreamWrapper,
    AsyncStreamProtocol,
    set_server_address_and_port,
)

P = ParamSpec("P")


# Protocols for sync wrapper return types
class SyncCompletionHandler(Protocol[P]):
    """Protocol for sync non-streaming handler."""

    def __call__(
        self,
        wrapped: Callable[P, ChatCompletion],
        client: OpenAI,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ChatCompletion: ...


class SyncStreamHandler(Protocol[P]):
    """Protocol for sync streaming handler."""

    def __call__(
        self,
        wrapped: Callable[P, StreamProtocol[ChatCompletionChunk]],
        client: OpenAI,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> StreamWrapper[ChatCompletionChunk, OpenAIMetadata]: ...


class AsyncCompletionHandler(Protocol[P]):
    """Protocol for async non-streaming handler."""

    async def __call__(
        self,
        wrapped: Callable[P, Awaitable[ChatCompletion]],
        client: AsyncOpenAI,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> ChatCompletion: ...


class AsyncStreamHandler(Protocol[P]):
    """Protocol for async streaming handler."""

    async def __call__(
        self,
        wrapped: Callable[P, Awaitable[AsyncStreamProtocol[ChatCompletionChunk]]],
        client: AsyncOpenAI,
        args: tuple[Any, ...],
        kwargs: dict[str, Any],
    ) -> AsyncStreamWrapper[ChatCompletionChunk, OpenAIMetadata]: ...


def get_llm_request_attributes(
    kwargs: dict[str, Any],
    client: OpenAI | AsyncOpenAI,
    operation_name: str = gen_ai_attributes.GenAiOperationNameValues.CHAT.value,
) -> dict[str, AttributeValue]:
    """Extract OpenTelemetry attributes from OpenAI API request parameters."""
    response_format = kwargs.get("response_format", {})
    response_format = (
        response_format.get("type")
        if isinstance(response_format, dict)
        else response_format.__name__
    )
    attributes = {
        gen_ai_attributes.GEN_AI_OPERATION_NAME: operation_name,
        gen_ai_attributes.GEN_AI_REQUEST_MODEL: kwargs.get("model"),
        gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE: kwargs.get("temperature"),
        gen_ai_attributes.GEN_AI_REQUEST_TOP_P: kwargs.get("p") or kwargs.get("top_p"),
        gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS: kwargs.get("max_tokens"),
        gen_ai_attributes.GEN_AI_REQUEST_PRESENCE_PENALTY: kwargs.get(
            "presence_penalty"
        ),
        gen_ai_attributes.GEN_AI_REQUEST_FREQUENCY_PENALTY: kwargs.get(
            "frequency_penalty"
        ),
        gen_ai_attributes.GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT: response_format,
        gen_ai_attributes.GEN_AI_OPENAI_REQUEST_SEED: kwargs.get("seed"),
    }
    set_server_address_and_port(client, attributes)
    attributes[gen_ai_attributes.GEN_AI_SYSTEM] = (
        gen_ai_attributes.GenAiSystemValues.OPENAI.value
    )

    service_tier = kwargs.get("service_tier")
    attributes[gen_ai_attributes.GEN_AI_OPENAI_RESPONSE_SERVICE_TIER] = (
        service_tier if service_tier != "auto" else None
    )

    # filter out None values
    return {k: v for k, v in attributes.items() if v is not None}


@contextmanager
def _span(
    tracer: Tracer, kwargs: dict[str, Any], client: OpenAI | AsyncOpenAI
) -> Iterator[Span]:
    """Context manager for creating and managing OpenTelemetry spans."""
    span_attributes = {**get_llm_request_attributes(kwargs, client)}
    span_name = f"{span_attributes[gen_ai_attributes.GEN_AI_OPERATION_NAME]} {span_attributes[gen_ai_attributes.GEN_AI_REQUEST_MODEL]}"

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
    """Internal sync wrapper for OpenAI API calls."""

    if not handle_stream:

        def traced_method_completion(
            wrapped: Callable[P, ChatCompletion],
            client: OpenAI,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> ChatCompletion:
            with _span(tracer, kwargs, client) as span:
                if span.is_recording():
                    for message in kwargs.get("messages", []):
                        set_message_event(span, message)
                try:
                    result = wrapped(*args, **kwargs)
                    if span.is_recording():
                        set_response_attributes(span, result)
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
            wrapped: Callable[P, StreamProtocol[ChatCompletionChunk]],
            client: OpenAI,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> StreamWrapper[ChatCompletionChunk, OpenAIMetadata]:
            with _span(tracer, kwargs, client) as span:
                if span.is_recording():
                    for message in kwargs.get("messages", []):
                        set_message_event(span, message)
                try:
                    if kwargs.get("stream", False):
                        return StreamWrapper(
                            span=span,
                            stream=wrapped(*args, **kwargs),
                            metadata=OpenAIMetadata(),
                            chunk_handler=OpenAIChunkHandler(),
                            cleanup_handler=default_openai_cleanup,
                        )
                    result = cast(ChatCompletion, wrapped(*args, **kwargs))
                    if span.is_recording():
                        set_response_attributes(span, result)
                    span.end()
                    return cast(
                        StreamWrapper[ChatCompletionChunk, OpenAIMetadata], result
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
    """Internal async wrapper for OpenAI API calls."""

    if not handle_stream:

        async def traced_method_completion(
            wrapped: Callable[P, Awaitable[ChatCompletion]],
            client: AsyncOpenAI,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> ChatCompletion:
            with _span(tracer, kwargs, client) as span:
                if span.is_recording():
                    for message in kwargs.get("messages", []):
                        set_message_event(span, message)
                try:
                    result = await wrapped(*args, **kwargs)
                    if span.is_recording():
                        set_response_attributes(span, result)
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
            wrapped: Callable[P, Awaitable[AsyncStreamProtocol[ChatCompletionChunk]]],
            client: AsyncOpenAI,
            args: tuple[Any, ...],
            kwargs: dict[str, Any],
        ) -> AsyncStreamWrapper[ChatCompletionChunk, OpenAIMetadata]:
            with _span(tracer, kwargs, client) as span:
                if span.is_recording():
                    for message in kwargs.get("messages", []):
                        set_message_event(span, message)
                try:
                    if kwargs.get("stream", False):
                        return AsyncStreamWrapper(
                            span=span,
                            stream=await wrapped(*args, **kwargs),
                            metadata=OpenAIMetadata(),
                            chunk_handler=OpenAIChunkHandler(),
                            cleanup_handler=default_openai_cleanup,
                        )
                    result = cast(ChatCompletion, await wrapped(*args, **kwargs))
                    if span.is_recording():
                        set_response_attributes(span, result)
                    span.end()
                    return cast(
                        AsyncStreamWrapper[ChatCompletionChunk, OpenAIMetadata], result
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


def chat_completions_create_patch_factory(
    tracer: Tracer,
) -> SyncStreamHandler[P]:
    """Returns a patch factory for sync chat completions create method."""
    return _sync_wrapper(tracer, handle_stream=True)


def chat_completions_create_async_patch_factory(
    tracer: Tracer,
) -> AsyncStreamHandler[P]:
    """Returns a patch factory for async chat completions create method."""
    return _async_wrapper(tracer, handle_stream=True)


def chat_completions_parse_patch_factory(
    tracer: Tracer,
) -> SyncCompletionHandler[P]:
    """Returns a patch factory for sync chat completions parse method."""
    # Stream is not handled in .parse method
    # https://platform.openai.com/docs/guides/structured-outputs/structured-outputs#streaming
    return _sync_wrapper(tracer, handle_stream=False)


def chat_completions_parse_async_patch_factory(
    tracer: Tracer,
) -> AsyncCompletionHandler[P]:
    """Returns a patch factory for async chat completions parse method."""
    # Stream is not handled in .parse method
    # https://platform.openai.com/docs/guides/structured-outputs/structured-outputs#streaming
    return _async_wrapper(tracer, handle_stream=False)
