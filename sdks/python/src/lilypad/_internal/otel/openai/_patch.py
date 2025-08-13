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

from typing import Any, ParamSpec

from openai import OpenAI, AsyncOpenAI
from openai.types.chat import ChatCompletion, ChatCompletionChunk
from opentelemetry.trace import Span, Tracer

from . import _utils
from ..base import (
    create_sync_wrapper,
    create_async_wrapper,
)
from ..utils import (
    StreamWrapper,
    StreamProtocol,
    AsyncStreamWrapper,
    AsyncStreamProtocol,
)
from ..base.protocols import (
    SyncStreamHandler,
    AsyncStreamHandler,
    SyncCompletionHandler,
    AsyncCompletionHandler,
)

P = ParamSpec("P")


def _process_messages(span: Span, kwargs: dict[str, Any]) -> None:
    """Process and record input messages."""
    for message in kwargs.get("messages", []):
        _utils.set_message_event(span, message)


def _create_stream_wrapper(
    span: Span, stream: StreamProtocol[ChatCompletionChunk]
) -> StreamWrapper[ChatCompletionChunk, _utils.OpenAIMetadata]:
    """Create OpenAI-specific stream wrapper."""
    return StreamWrapper(
        span=span,
        stream=stream,
        metadata=_utils.OpenAIMetadata(),
        chunk_handler=_utils.OpenAIChunkHandler(),
        cleanup_handler=_utils.default_openai_cleanup,
    )


async def _create_async_stream_wrapper(
    span: Span, stream: AsyncStreamProtocol[ChatCompletionChunk]
) -> AsyncStreamWrapper[ChatCompletionChunk, _utils.OpenAIMetadata]:
    """Create OpenAI-specific async stream wrapper."""
    return AsyncStreamWrapper(
        span=span,
        stream=stream,
        metadata=_utils.OpenAIMetadata(),
        chunk_handler=_utils.OpenAIChunkHandler(),
        cleanup_handler=_utils.default_openai_cleanup,
    )


def chat_completions_create_patch_factory(
    tracer: Tracer,
) -> SyncStreamHandler[P, ChatCompletionChunk, _utils.OpenAIMetadata, OpenAI]:
    """Returns a patch factory for sync chat completions create method."""
    return create_sync_wrapper(
        tracer=tracer,
        get_span_attributes=_utils.get_llm_request_attributes,
        process_messages=_process_messages,
        process_response=_utils.set_response_attributes,
        create_stream_wrapper=_create_stream_wrapper,
        handle_stream=True,
    )


def chat_completions_create_async_patch_factory(
    tracer: Tracer,
) -> AsyncStreamHandler[P, ChatCompletionChunk, _utils.OpenAIMetadata, AsyncOpenAI]:
    """Returns a patch factory for async chat completions create method."""
    return create_async_wrapper(
        tracer=tracer,
        get_span_attributes=_utils.get_llm_request_attributes,
        process_messages=_process_messages,
        process_response=_utils.set_response_attributes,
        create_async_stream_wrapper=_create_async_stream_wrapper,
        handle_stream=True,
    )


def chat_completions_parse_patch_factory(
    tracer: Tracer,
) -> SyncCompletionHandler[P, ChatCompletion, OpenAI]:
    """Returns a patch factory for sync chat completions parse method."""
    return create_sync_wrapper(
        tracer=tracer,
        get_span_attributes=_utils.get_llm_request_attributes,
        process_messages=_process_messages,
        process_response=_utils.set_response_attributes,
        create_stream_wrapper=_create_stream_wrapper,
        handle_stream=False,
    )


def chat_completions_parse_async_patch_factory(
    tracer: Tracer,
) -> AsyncCompletionHandler[P, ChatCompletion, AsyncOpenAI]:
    """Returns a patch factory for async chat completions parse method."""
    return create_async_wrapper(
        tracer=tracer,
        get_span_attributes=_utils.get_llm_request_attributes,
        process_messages=_process_messages,
        process_response=_utils.set_response_attributes,
        create_async_stream_wrapper=_create_async_stream_wrapper,
        handle_stream=False,
    )
