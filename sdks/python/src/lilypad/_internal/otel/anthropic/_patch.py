"""Patching utilities for Anthropic client methods to add OpenTelemetry instrumentation.

This module contains the core logic for wrapping Anthropic API calls with telemetry spans.
"""

from typing import Any, ParamSpec

from anthropic import Anthropic, AsyncAnthropic
from anthropic.types import MessageStreamEvent
from opentelemetry.trace import Span, Tracer

from . import _utils
from ..base import (
    SyncStreamHandler,
    AsyncStreamHandler,
    create_sync_wrapper,
    create_async_wrapper,
)
from ..utils import (
    StreamWrapper,
    StreamProtocol,
    AsyncStreamWrapper,
    AsyncStreamProtocol,
)

P = ParamSpec("P")


def _process_messages(span: Span, kwargs: dict[str, Any]) -> None:
    """Process and record input messages."""
    if system := kwargs.get("system"):
        _utils.set_message_event(
            span,
            _utils.SystemMessageParam(role="system", content=system),
        )
    for message in kwargs.get("messages", []):
        _utils.set_message_event(span, message)


def _create_stream_wrapper(
    span: Span, stream: StreamProtocol[MessageStreamEvent]
) -> StreamWrapper[MessageStreamEvent, _utils.AnthropicMetadata]:
    """Create Anthropic-specific stream wrapper."""
    return StreamWrapper(
        span=span,
        stream=stream,
        metadata=_utils.AnthropicMetadata(),
        chunk_handler=_utils.AnthropicChunkHandler(),
        cleanup_handler=_utils.default_anthropic_cleanup,
    )


async def _create_async_stream_wrapper(
    span: Span, stream: AsyncStreamProtocol[MessageStreamEvent]
) -> AsyncStreamWrapper[MessageStreamEvent, _utils.AnthropicMetadata]:
    """Create Anthropic-specific async stream wrapper."""
    return AsyncStreamWrapper(
        span=span,
        stream=stream,
        metadata=_utils.AnthropicMetadata(),
        chunk_handler=_utils.AnthropicChunkHandler(),
        cleanup_handler=_utils.default_anthropic_cleanup,
    )


def messages_create_patch_factory(
    tracer: Tracer,
) -> SyncStreamHandler[P, MessageStreamEvent, _utils.AnthropicMetadata, Anthropic]:
    """Returns a patch factory for sync messages create method."""
    return create_sync_wrapper(
        tracer=tracer,
        get_span_attributes=_utils.get_llm_request_attributes,
        process_messages=_process_messages,
        process_response=_utils.set_response_attributes,
        create_stream_wrapper=_create_stream_wrapper,
        handle_stream=True,
    )


def messages_create_async_patch_factory(
    tracer: Tracer,
) -> AsyncStreamHandler[
    P, MessageStreamEvent, _utils.AnthropicMetadata, AsyncAnthropic
]:
    """Returns a patch factory for async messages create method."""
    return create_async_wrapper(
        tracer=tracer,
        get_span_attributes=_utils.get_llm_request_attributes,
        process_messages=_process_messages,
        process_response=_utils.set_response_attributes,
        create_async_stream_wrapper=_create_async_stream_wrapper,
        handle_stream=True,
    )
