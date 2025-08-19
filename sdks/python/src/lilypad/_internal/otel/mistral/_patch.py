"""Patching utilities for Mistral client methods to add OpenTelemetry instrumentation.

This module contains the core logic for wrapping Mistral API calls with telemetry spans.
"""

from typing import Any, ParamSpec

from mistralai import Mistral
from mistralai.models import CompletionEvent
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
)

P = ParamSpec("P")


def _process_messages(span: Span, kwargs: dict[str, Any]) -> None:
    """Process and record input messages."""
    for message in kwargs.get("messages", []):
        _utils.set_message_event(span, message)


def _create_stream_wrapper(
    span: Span, stream: StreamProtocol[CompletionEvent]
) -> StreamWrapper[CompletionEvent, _utils.MistralMetadata]:
    """Create Mistral-specific stream wrapper."""
    return StreamWrapper(
        span=span,
        stream=stream,
        metadata=_utils.MistralMetadata(),
        chunk_handler=_utils.MistralChunkHandler(),
        cleanup_handler=_utils.default_mistral_cleanup,
    )


async def _create_async_stream_wrapper(
    span: Span, stream: AsyncStreamProtocol[CompletionEvent]
) -> AsyncStreamWrapper[CompletionEvent, _utils.MistralMetadata]:
    """Create Mistral-specific async stream wrapper."""
    return AsyncStreamWrapper(
        span=span,
        stream=stream,
        metadata=_utils.MistralMetadata(),
        chunk_handler=_utils.MistralChunkHandler(),
        cleanup_handler=_utils.default_mistral_cleanup,
    )


def chat_complete_patch_factory(
    tracer: Tracer,
) -> SyncStreamHandler[P, CompletionEvent, _utils.MistralMetadata, Mistral]:
    """Returns a patch factory for sync chat complete method."""
    return create_sync_wrapper(
        tracer=tracer,
        get_span_attributes=_utils.get_llm_request_attributes,
        process_messages=_process_messages,
        process_response=_utils.set_response_attributes,
        create_stream_wrapper=_create_stream_wrapper,
        handle_stream=True,
    )


def chat_complete_async_patch_factory(
    tracer: Tracer,
) -> AsyncStreamHandler[P, CompletionEvent, _utils.MistralMetadata, Mistral]:
    """Returns a patch factory for async chat complete method."""
    return create_async_wrapper(
        tracer=tracer,
        get_span_attributes=_utils.get_llm_request_attributes,
        process_messages=_process_messages,
        process_response=_utils.set_response_attributes,
        create_async_stream_wrapper=_create_async_stream_wrapper,
        handle_stream=True,
    )
