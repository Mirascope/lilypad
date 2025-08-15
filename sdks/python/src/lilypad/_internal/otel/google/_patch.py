"""Patching utilities for Google client methods to add OpenTelemetry instrumentation.

This module contains the core logic for wrapping Google AI calls with telemetry spans.
"""

from __future__ import annotations

import json
from typing import Any, cast

from opentelemetry.trace import Span, Tracer
from opentelemetry.util.types import AttributeValue
from typing_extensions import ParamSpec

from ..base.protocols import (
    AsyncCompletionHandler,
    SyncCompletionHandler,
    SyncStreamHandler,
    AsyncStreamHandler,
)
from ..base.wrappers import (
    create_async_wrapper,
    create_sync_wrapper,
)
from ..base.stream_wrappers import (
    create_stream_method_wrapper,
    create_async_stream_method_wrapper,
)
from ..utils import (
    StreamWrapper,
    AsyncStreamWrapper,
)
from . import _utils
from google.genai.types import (
    GenerateContentConfig,
    GenerateContentConfigDict,
    ContentListUnionDict,
    ContentUnionDict,
)
from google.genai.models import AsyncModels, Models
from google.genai.types import GenerateContentResponse

P = ParamSpec("P")


def _create_stream_wrapper(
    span: Span,
    stream: Any,
    metadata: _utils.GoogleMetadata,
) -> StreamWrapper[GenerateContentResponse, _utils.GoogleMetadata]:
    """Create a synchronous stream wrapper for Google AI streaming responses."""
    return StreamWrapper(
        span=span,
        stream=stream,
        metadata=metadata,
        chunk_handler=_utils.GoogleChunkHandler(),
        cleanup_handler=_utils.default_google_cleanup,
    )


def _create_async_stream_wrapper(
    span: Span,
    stream: Any,
    metadata: _utils.GoogleMetadata,
) -> AsyncStreamWrapper[GenerateContentResponse, _utils.GoogleMetadata]:
    """Create an asynchronous stream wrapper for Google AI streaming responses."""
    return AsyncStreamWrapper(
        span=span,
        stream=stream,
        metadata=metadata,
        chunk_handler=_utils.GoogleChunkHandler(),
        cleanup_handler=_utils.default_google_cleanup,
    )


def _process_messages(
    span: Span,
    kwargs: dict[str, Any],
) -> None:
    """Process and record input messages."""
    config = cast(
        GenerateContentConfig | GenerateContentConfigDict | None, kwargs.get("config")
    )
    if config:
        if isinstance(config, dict):
            system_instruction = config.get("system_instruction")
        else:
            system_instruction = config.system_instruction

        if system_instruction:
            span.add_event(
                "gen_ai.system.message",
                attributes={
                    "gen_ai.system": "google_genai",
                    "gen_ai.content": str(system_instruction),
                },
            )

    contents = cast(ContentListUnionDict | None, kwargs.get("contents"))
    if not contents:
        return

    if not isinstance(contents, list):
        contents = [contents]

    messages = _utils._convert_content_to_messages(
        cast(list[ContentUnionDict], contents)
    )

    for message in messages:
        role = message.get("role", "user")
        event_name = f"gen_ai.{role}.message"
        attributes: dict[str, AttributeValue] = {
            "gen_ai.system": "google_genai",
        }

        content = message.get("content")
        if content:
            attributes["gen_ai.content"] = content

        tool_calls = message.get("tool_calls")
        if tool_calls:
            attributes["gen_ai.tool_calls"] = json.dumps(tool_calls)

        span.add_event(event_name, attributes=attributes)


def generate_content_patch_factory(
    tracer: Tracer,
) -> SyncCompletionHandler[P, GenerateContentResponse, Models]:
    return create_sync_wrapper(
        tracer=tracer,
        get_span_attributes=_utils.get_llm_request_attributes,
        process_messages=_process_messages,
        create_stream_wrapper=None,
        process_response=_utils.process_response,
        handle_stream=False,
    )


def _create_google_metadata() -> _utils.GoogleMetadata:
    """Factory function to create Google metadata."""
    return _utils.GoogleMetadata()


def _get_stream_span_attributes(
    kwargs: dict[str, Any], client: Models | AsyncModels, operation_name: str = "chat"
) -> dict[str, AttributeValue]:
    """Get span attributes for streaming operations."""
    return _utils.get_llm_request_attributes(
        kwargs, client, operation_name, stream=True
    )


def generate_content_stream_patch_factory(
    tracer: Tracer,
) -> SyncStreamHandler[P, GenerateContentResponse, _utils.GoogleMetadata, Models]:
    return create_stream_method_wrapper(
        tracer=tracer,
        get_span_attributes=_get_stream_span_attributes,
        process_messages=_process_messages,
        metadata_factory=_create_google_metadata,
        chunk_handler_factory=_utils.GoogleChunkHandler,
        cleanup_handler=_utils.default_google_cleanup,
        span_name_prefix="google_genai",
    )


def async_generate_content_patch_factory(
    tracer: Tracer,
) -> AsyncCompletionHandler[P, GenerateContentResponse, AsyncModels]:
    return create_async_wrapper(
        tracer=tracer,
        get_span_attributes=_utils.get_llm_request_attributes,
        process_messages=_process_messages,
        process_response=_utils.process_response,
        create_async_stream_wrapper=None,
        handle_stream=False,
    )


def async_generate_content_stream_patch_factory(
    tracer: Tracer,
) -> AsyncStreamHandler[P, GenerateContentResponse, _utils.GoogleMetadata, AsyncModels]:
    return create_async_stream_method_wrapper(
        tracer=tracer,
        get_span_attributes=_get_stream_span_attributes,
        process_messages=_process_messages,
        metadata_factory=_create_google_metadata,
        chunk_handler_factory=_utils.GoogleChunkHandler,
        cleanup_handler=_utils.default_google_cleanup,
        span_name_prefix="google_genai",
    )
