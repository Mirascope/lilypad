"""Patching utilities for Azure AI Inference client methods to add OpenTelemetry instrumentation.

This module contains the core logic for wrapping Azure AI Inference API calls with telemetry spans.
"""

from typing import Any, ParamSpec

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

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.aio import ChatCompletionsClient as AsyncChatCompletionsClient
from azure.ai.inference.models import StreamingChatCompletionsUpdate

P = ParamSpec("P")


def _process_messages(span: Span, kwargs: dict[str, Any]) -> None:
    """Process and record input messages."""
    for message in kwargs.get("messages", []):
        _utils.set_message_event(span, message)


def _create_stream_wrapper(
    span: Span, stream: StreamProtocol[StreamingChatCompletionsUpdate]
) -> StreamWrapper[StreamingChatCompletionsUpdate, _utils.AzureMetadata]:
    """Create Azure-specific stream wrapper."""
    return StreamWrapper(
        span=span,
        stream=stream,
        metadata=_utils.AzureMetadata(),
        chunk_handler=_utils.AzureChunkHandler(),
        cleanup_handler=_utils.default_azure_cleanup,
    )


async def _create_async_stream_wrapper(
    span: Span, stream: AsyncStreamProtocol[StreamingChatCompletionsUpdate]
) -> AsyncStreamWrapper[StreamingChatCompletionsUpdate, _utils.AzureMetadata]:
    """Create Azure-specific async stream wrapper."""
    return AsyncStreamWrapper(
        span=span,
        stream=stream,
        metadata=_utils.AzureMetadata(),
        chunk_handler=_utils.AzureChunkHandler(),
        cleanup_handler=_utils.default_azure_cleanup,
    )


def chat_completions_complete_patch_factory(
    tracer: Tracer,
) -> SyncStreamHandler[
    P, StreamingChatCompletionsUpdate, _utils.AzureMetadata, ChatCompletionsClient
]:
    """Returns a patch factory for sync chat completions complete method."""
    return create_sync_wrapper(
        tracer=tracer,
        get_span_attributes=_utils.get_llm_request_attributes,
        process_messages=_process_messages,
        process_response=_utils.set_response_attributes,
        create_stream_wrapper=_create_stream_wrapper,
        handle_stream=True,
    )


def chat_completions_complete_async_patch_factory(
    tracer: Tracer,
) -> AsyncStreamHandler[
    P, StreamingChatCompletionsUpdate, _utils.AzureMetadata, AsyncChatCompletionsClient
]:
    """Returns a patch factory for async chat completions complete method."""
    return create_async_wrapper(
        tracer=tracer,
        get_span_attributes=_utils.get_llm_request_attributes,
        process_messages=_process_messages,
        process_response=_utils.set_response_attributes,
        create_async_stream_wrapper=_create_async_stream_wrapper,
        handle_stream=True,
    )
