"""Utility classes and functions for Lilypad OpenTelemetry instrumentation."""
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

from abc import ABC, abstractmethod
from types import TracebackType
from typing import Any, Generic, TypeVar, Protocol, TypedDict
from collections.abc import Callable, Iterator, AsyncIterator

from httpx import URL
from opentelemetry.trace import Span, Status, StatusCode
from opentelemetry.semconv.attributes import error_attributes
from opentelemetry.semconv._incubating.attributes import (
    server_attributes,
)

T = TypeVar("T")
ChunkType = TypeVar("ChunkType")
MetadataType = TypeVar("MetadataType", bound="BaseMetadata")


class BaseMetadata(TypedDict, total=False):
    """Base metadata for all providers."""

    response_id: str | None
    response_model: str | None
    prompt_tokens: int | None
    completion_tokens: int | None


class StreamProtocol(Generic[ChunkType], ABC):
    """Protocol for synchronous stream objects."""

    @abstractmethod
    def __iter__(self) -> Iterator[ChunkType]:
        """Returns an iterator for the stream."""
        ...

    @abstractmethod
    def __next__(self) -> ChunkType:
        """Get the next item from the stream."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the stream and release resources."""
        ...


class AsyncStreamProtocol(ABC, Generic[ChunkType]):
    """Protocol for asynchronous stream objects."""

    @abstractmethod
    def __aiter__(self) -> AsyncIterator[ChunkType]:
        """Returns an async iterator for the stream."""
        ...

    @abstractmethod
    async def __anext__(self) -> ChunkType:
        """Get the next item from the async stream."""
        ...

    @abstractmethod
    async def aclose(self) -> None:
        """Close the async stream and release resources."""
        ...


SyncAsyncStreamProtocol = TypeVar(
    "SyncAsyncStreamProtocol", bound=StreamProtocol | AsyncStreamProtocol
)


class ToolCallFunctionProtocol(Protocol):
    """Protocol for tool call function objects."""

    @property
    def name(self) -> str | None: ...

    @property
    def arguments(self) -> str | None: ...


class ToolCallProtocol(Protocol):
    """Protocol for tool call objects."""

    @property
    def id(self) -> str | None: ...

    @property
    def index(self) -> int: ...

    @property
    def function(self) -> ToolCallFunctionProtocol | None: ...


class ChoiceBuffer:
    """Buffer for accumulating streaming choice content."""

    __slots__ = ("index", "finish_reason", "text_content", "tool_calls_buffers")

    def __init__(self, index: int) -> None:
        """Initialize a choice buffer with the given index."""
        self.index = index
        self.finish_reason: str | None = None
        self.text_content: list[str] = []
        self.tool_calls_buffers: list[ToolCallBuffer | None] = []

    def append_text_content(self, content: str) -> None:
        """Append text content to the buffer."""
        self.text_content.append(content)

    def append_tool_call(self, tool_call: ToolCallProtocol) -> None:
        """Append a tool call to the buffer.

        Note: This accepts any object to support multiple providers.
        Each provider should ensure the tool_call has the expected structure.
        """
        # Get index attribute, default to 0 if not present
        index = getattr(tool_call, "index", 0)

        # make sure we have enough tool call buffers
        for _ in range(len(self.tool_calls_buffers), index + 1):
            self.tool_calls_buffers.append(None)

        # Check if tool_call has a function attribute
        if not self.tool_calls_buffers[index] and hasattr(tool_call, "function"):
            function = tool_call.function
            tool_call_id = getattr(tool_call, "id", None) or ""
            function_name = getattr(function, "name", None) or ""

            self.tool_calls_buffers[index] = ToolCallBuffer(
                self.index, tool_call_id, function_name
            )

        buffer = self.tool_calls_buffers[index]
        if buffer is not None and hasattr(tool_call, "function"):
            function = tool_call.function
            arguments = getattr(function, "arguments", None)
            if arguments:
                buffer.append_arguments(arguments)


class ChunkHandler(ABC, Generic[ChunkType, MetadataType]):
    @abstractmethod
    def extract_metadata(self, chunk: ChunkType, metadata: MetadataType) -> None:
        """Extract metadata from chunk and update StreamMetadata"""
        ...

    @abstractmethod
    def process_chunk(self, chunk: ChunkType, buffers: list[ChoiceBuffer]) -> None:
        """Process chunk and update choice buffers"""
        ...


class BaseStreamWrapper(ABC, Generic[ChunkType, MetadataType]):
    """Base wrapper for handling streaming responses with telemetry."""

    span: Span
    metadata: MetadataType
    chunk_handler: ChunkHandler[ChunkType, MetadataType]
    cleanup_handler: Callable[[Span, MetadataType, list[ChoiceBuffer]], None] | None
    choice_buffers: list[ChoiceBuffer]
    _span_started: bool

    def setup(self) -> None:
        """Set up the stream wrapper for processing."""
        if not self._span_started:
            self._span_started = True

    def process_chunk(self, chunk: ChunkType) -> None:
        """Process a single chunk from the stream."""
        self.chunk_handler.extract_metadata(chunk, self.metadata)
        self.chunk_handler.process_chunk(chunk, self.choice_buffers)

    def cleanup(self) -> None:
        """Clean up resources and finalize the span."""
        if self._span_started:
            if self.cleanup_handler:
                self.cleanup_handler(self.span, self.metadata, self.choice_buffers)
            self.span.end()
            self._span_started = False


class StreamWrapper(
    BaseStreamWrapper[ChunkType, MetadataType], Generic[ChunkType, MetadataType]
):
    """Synchronous stream wrapper with context manager support."""

    stream: StreamProtocol[ChunkType]

    def __init__(
        self,
        span: Span,
        stream: StreamProtocol[ChunkType],
        metadata: MetadataType,
        chunk_handler: ChunkHandler[ChunkType, MetadataType],
        cleanup_handler: Callable[[Span, MetadataType, list[ChoiceBuffer]], None]
        | None = None,
    ) -> None:
        """Initialize the stream wrapper with telemetry components."""
        self.span = span
        self.stream = stream
        self.chunk_handler = chunk_handler
        self.cleanup_handler = cleanup_handler
        self.metadata = metadata
        self.choice_buffers: list[ChoiceBuffer] = []
        self._span_started = False
        self.setup()

    def __enter__(self) -> "StreamWrapper[ChunkType, MetadataType]":
        """Enter the context manager."""
        self.setup()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Exit the context manager and handle exceptions."""
        try:
            if exc_type is not None:
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self.span.set_attribute(
                    error_attributes.ERROR_TYPE, exc_type.__qualname__
                )
        finally:
            self.cleanup()
        return False

    def close(self) -> None:
        """Close the stream and perform cleanup."""
        self.stream.close()
        self.cleanup()

    def __iter__(self) -> Iterator[ChunkType]:
        """Returns self as an iterator."""
        return self

    def __next__(self) -> ChunkType:
        """Get and process the next chunk from the stream."""
        try:
            chunk = next(self.stream)
            self.process_chunk(chunk)
            return chunk
        except StopIteration:
            self.cleanup()
            raise
        except Exception as error:
            self.span.set_status(Status(StatusCode.ERROR, str(error)))
            self.span.set_attribute(
                error_attributes.ERROR_TYPE, type(error).__qualname__
            )
            self.cleanup()
            raise


class AsyncStreamWrapper(
    BaseStreamWrapper[ChunkType, MetadataType], Generic[ChunkType, MetadataType]
):
    """Asynchronous stream wrapper with async context manager support."""

    stream: AsyncStreamProtocol[ChunkType]

    def __init__(
        self,
        span: Span,
        stream: AsyncStreamProtocol[ChunkType],
        metadata: MetadataType,
        chunk_handler: ChunkHandler[ChunkType, MetadataType],
        cleanup_handler: Callable[[Span, MetadataType, list[ChoiceBuffer]], None]
        | None = None,
    ) -> None:
        """Initialize the stream wrapper with telemetry components."""
        self.span = span
        self.stream = stream
        self.chunk_handler = chunk_handler
        self.cleanup_handler = cleanup_handler
        self.metadata = metadata
        self.choice_buffers: list[ChoiceBuffer] = []
        self._span_started = False
        self.setup()

    async def __aenter__(self) -> "AsyncStreamWrapper[ChunkType, MetadataType]":
        """Enter the async context manager."""
        self.setup()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> bool:
        """Exit the async context manager and handle exceptions."""
        try:
            if exc_type is not None:
                self.span.set_status(Status(StatusCode.ERROR, str(exc_val)))
                self.span.set_attribute(
                    error_attributes.ERROR_TYPE, exc_type.__qualname__
                )
        finally:
            self.cleanup()
        return False

    async def close(self) -> None:
        """Close the async stream and perform cleanup."""
        await self.stream.aclose()
        self.cleanup()

    def __aiter__(self) -> "AsyncStreamWrapper[ChunkType, MetadataType]":
        """Returns self as an async iterator."""
        return self

    async def __anext__(self) -> ChunkType:
        """Get and process the next chunk from the async stream."""
        try:
            chunk = await self.stream.__anext__()
            self.process_chunk(chunk)
            return chunk
        except StopAsyncIteration:
            self.cleanup()
            raise
        except Exception as error:
            self.span.set_status(Status(StatusCode.ERROR, str(error)))
            self.span.set_attribute(
                error_attributes.ERROR_TYPE, type(error).__qualname__
            )
            self.cleanup()
            raise


class ToolCallBuffer:
    """Buffer for accumulating tool call information."""

    def __init__(self, index: int, tool_call_id: str, function_name: str) -> None:
        """Initialize a tool call buffer."""
        self.index = index
        self.function_name = function_name
        self.tool_call_id = tool_call_id
        self.arguments: list[str] = []

    def append_arguments(self, arguments: str) -> None:
        """Append arguments to the tool call buffer."""
        self.arguments.append(arguments)


def set_server_address_and_port(
    client: Any,  # NOTE: we do not know what type the client will be across providers
    attributes: dict[str, Any],
) -> None:
    """Extract and set server address and port attributes from client instance."""
    base_client = getattr(client, "_client", None)
    base_url = getattr(base_client, "base_url", None)
    if not isinstance(base_url, URL):
        return

    attributes[server_attributes.SERVER_ADDRESS] = base_url.host
    port = base_url.port

    if port and port != 443 and port > 0:
        attributes[server_attributes.SERVER_PORT] = port
