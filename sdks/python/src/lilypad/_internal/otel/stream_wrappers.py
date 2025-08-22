"""Utility classes and functions for OpenTelemetry streaming instrumentation."""
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

import logging
from abc import ABC
from collections.abc import AsyncIterator, Iterator
from types import TracebackType
from typing import Generic, Protocol

from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.trace import Span, Status, StatusCode

from .types import (
    AsyncStream,
    ChoiceDelta,
    ChoiceEvent,
    ChunkT,
    ContravariantChunkT,
    FunctionCall,
    GenAIResponseAttributes,
    Message,
    SpanEvent,
    Stream,
    StreamT,
    ToolCall,
    ToolCallDelta,
    ToolCallDeltaProtocol,
)

logger = logging.getLogger(__name__)


class _ToolCallBuffer:
    """Buffer for accumulating tool call information."""

    def __init__(self, index: int, tool_call_id: str, function_name: str) -> None:
        """Initialize a tool call buffer."""
        self.index = index
        self.function_name = function_name
        self.tool_call_id = tool_call_id
        self.arguments: str = ""

    def append_arguments(self, arguments: str) -> None:
        """Append arguments to the tool call buffer."""
        self.arguments += arguments

    def dump(self) -> ToolCall:
        """Returns the accumulated tool call data as a `ToolCall`."""
        return ToolCall(
            id=self.tool_call_id,
            type="function",
            function=FunctionCall(name=self.function_name, arguments=self.arguments),
        )


class _ChoiceBuffer:
    """Buffer for accumulating streaming choice content."""

    __slots__ = (
        "system",
        "index",
        "finish_reason",
        "content",
        "tool_calls_buffers",
    )

    def __init__(self, system: str, index: int) -> None:
        """Initialize a choice buffer with the given index."""
        self.system = system
        self.index = index
        self.finish_reason: str | None = None
        self.content: str = ""
        self.tool_calls_buffers: list[_ToolCallBuffer | None] = []

    def append_content(self, content: str) -> None:
        """Append text content to the buffer."""
        self.content += content

    def append_tool_call(
        self, tool_call: ToolCallDelta | ToolCallDeltaProtocol
    ) -> None:
        """Append a tool call to the buffer.

        Note: This accepts any object to support multiple providers.
        Each provider should ensure the tool_call has the expected structure.
        """
        index = getattr(tool_call, "index", 0)

        # make sure we have enough tool call buffers
        for _ in range(len(self.tool_calls_buffers), index + 1):
            self.tool_calls_buffers.append(None)

        if not tool_call.function:  # pragma: no cover
            return

        if not (buffer := self.tool_calls_buffers[index]):
            buffer = _ToolCallBuffer(
                self.index, tool_call.id or "", tool_call.function.name or ""
            )
            self.tool_calls_buffers[index] = buffer

        buffer.append_arguments(tool_call.function.arguments or "")

    def dump(self) -> SpanEvent:
        """Returns the accumulated choice data as a span event."""
        message: Message = {"role": "assistant"}
        if self.content:
            message["content"] = self.content
        tool_calls = [
            buffer.dump() for buffer in self.tool_calls_buffers if buffer
        ] or None
        choice_event = ChoiceEvent(
            system=self.system,
            index=self.index,
            message=message,
            finish_reason=self.finish_reason,
            tool_calls=tool_calls,
        )
        return choice_event.dump()


class _ProcessChunk(Protocol[ContravariantChunkT]):
    """Protocol for processing streaming chunks into attributes and deltas."""

    def __call__(
        self,
        chunk: ContravariantChunkT,
    ) -> tuple[GenAIResponseAttributes, list[ChoiceDelta]]:
        """Returns response attributes and choice deltas from the chunk."""
        raise NotImplementedError


class _BaseStreamWrapper(ABC, Generic[ChunkT, StreamT]):
    """Base wrapper for handling streaming responses with telemetry."""

    span: Span
    """The OpenTelemetry span for this stream."""

    response_attributes: GenAIResponseAttributes
    """Accumulated response attributes from the stream."""

    process_chunk: _ProcessChunk[ChunkT]
    """Function to process individual chunks."""

    choice_buffers: list[_ChoiceBuffer]
    """Buffers for accumulating streaming choice data."""

    stream: StreamT
    """The underlying stream being wrapped."""

    _span_started: bool

    def __init__(
        self,
        span: Span,
        stream: StreamT,
        process_chunk: _ProcessChunk[ChunkT],
    ) -> None:
        """Initialize the stream wrapper with telemetry components."""
        self.span = span
        self.stream = stream
        # NOTE: this is for OpenAI stream context manager support
        if response := getattr(stream, "response", None):
            self.response = response
        self.process_chunk = process_chunk
        self.response_attributes = GenAIResponseAttributes()
        self.choice_buffers: list[_ChoiceBuffer] = []
        self._span_started = False
        self._setup()

    def _setup(self) -> None:
        """Set up the stream wrapper for processing."""
        if not self._span_started:
            self._span_started = True

    def _update(
        self,
        response_attributes: GenAIResponseAttributes,
        choice_deltas: list[ChoiceDelta],
    ) -> None:
        """Updates response attributes with new chunk data."""
        self.response_attributes.update(response_attributes)
        for delta in choice_deltas:
            while len(self.choice_buffers) <= delta.index:
                self.choice_buffers.append(
                    _ChoiceBuffer(delta.system, len(self.choice_buffers))
                )

            if delta.finish_reason:
                self.choice_buffers[delta.index].finish_reason = delta.finish_reason
            if delta.content:
                self.choice_buffers[delta.index].append_content(delta.content)
            for tool_call in delta.tool_calls or []:
                self.choice_buffers[delta.index].append_tool_call(tool_call)

    def _cleanup(self) -> None:
        """Clean up resources and finalize the span."""
        if self._span_started:
            self.span.set_attributes(self.response_attributes.dump())
            for buffer in self.choice_buffers:
                self.span.add_event(**buffer.dump())
            self.span.end()
            self._span_started = False


class StreamWrapper(_BaseStreamWrapper[ChunkT, Stream[ChunkT]], Generic[ChunkT]):
    """Synchronous stream wrapper with context manager support."""

    def __enter__(self) -> "StreamWrapper[ChunkT]":  # pragma: no cover
        """Enter the context manager."""
        self._setup()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:  # pragma: no cover
        """Exit the context manager and handle exceptions."""
        try:
            if exc_type is not None:
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self.span.set_attribute(
                    error_attributes.ERROR_TYPE, exc_type.__qualname__
                )
        finally:
            self._cleanup()
        return False

    def close(self) -> None:  # pragma: no cover
        """Close the stream and perform cleanup."""
        self.stream.close()
        self._cleanup()

    def __iter__(self) -> Iterator[ChunkT]:
        """Returns self as an iterator."""
        return self

    def __next__(self) -> ChunkT:
        """Get and process the next chunk from the stream."""
        try:
            chunk = next(self.stream)
            metadata, choice_deltas = self.process_chunk(chunk)
            self._update(metadata, choice_deltas)
            return chunk
        except StopIteration:
            self._cleanup()
            raise
        except Exception as error:  # pragma: no cover
            self.span.set_status(Status(StatusCode.ERROR, str(error)))
            self.span.set_attribute(
                error_attributes.ERROR_TYPE, type(error).__qualname__
            )
            self._cleanup()
            raise


class AsyncStreamWrapper(
    _BaseStreamWrapper[ChunkT, AsyncStream[ChunkT]], Generic[ChunkT]
):
    """Asynchronous stream wrapper with async context manager support."""

    async def __aenter__(self) -> "AsyncStreamWrapper[ChunkT]":  # pragma: no cover
        """Enter the async context manager."""
        self._setup()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:  # pragma: no cover
        """Exit the async context manager and handle exceptions."""
        try:
            if exc_type is not None:
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self.span.set_attribute(
                    error_attributes.ERROR_TYPE, exc_type.__qualname__
                )
        finally:
            self._cleanup()
        return False

    async def close(self) -> None:  # pragma: no cover
        """Close the async stream and perform cleanup."""
        await self.stream.close()
        self._cleanup()

    def __aiter__(self) -> AsyncIterator[ChunkT]:
        """Returns self as an async iterator."""
        return self

    async def __anext__(self) -> ChunkT:
        """Get and process the next chunk from the async stream."""
        try:
            chunk = await self.stream.__anext__()
            metadata, choice_deltas = self.process_chunk(chunk)
            self._update(metadata, choice_deltas)
            return chunk
        except StopAsyncIteration:
            self._cleanup()
            raise
        except Exception as error:  # pragma: no cover
            self.span.set_status(Status(StatusCode.ERROR, str(error)))
            self.span.set_attribute(
                error_attributes.ERROR_TYPE, type(error).__qualname__
            )
            self._cleanup()
            raise
