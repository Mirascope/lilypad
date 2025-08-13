from typing import Any, Iterator, AsyncIterator
from unittest.mock import Mock

import httpx
import pytest
from inline_snapshot import snapshot
from opentelemetry.trace import Span, Status, StatusCode

from lilypad._internal.otel.utils import (
    BaseMetadata,
    ChoiceBuffer,
    ChunkHandler,
    StreamWrapper,
    StreamProtocol,
    ToolCallBuffer,
    AsyncStreamWrapper,
    AsyncStreamProtocol,
    set_server_address_and_port,
)


class MockMetadata(BaseMetadata): ...


class MockChunk:
    def __init__(self, content: str, finish_reason: str | None = None) -> None:
        self.content = content
        self.finish_reason = finish_reason
        self.usage = (
            {"prompt_tokens": 10, "completion_tokens": 5} if finish_reason else None
        )


class MockChunkHandler(ChunkHandler[MockChunk, MockMetadata]):
    def extract_metadata(self, chunk: MockChunk, metadata: MockMetadata) -> None:
        if chunk.usage:
            metadata["prompt_tokens"] = chunk.usage.get("prompt_tokens")
            metadata["completion_tokens"] = chunk.usage.get("completion_tokens")

    def process_chunk(self, chunk: MockChunk, buffers: list[ChoiceBuffer]) -> None:
        if not buffers:
            buffers.append(ChoiceBuffer(0))

        buffer = buffers[0]
        if chunk.content:
            buffer.append_text_content(chunk.content)
        if chunk.finish_reason:
            buffer.finish_reason = chunk.finish_reason


class MockStream(StreamProtocol[MockChunk]):
    def __init__(self, chunks: list[MockChunk]) -> None:
        self.chunks = chunks
        self.index = 0
        self.closed = False

    def __iter__(self) -> Iterator[MockChunk]:
        return self  # pragma: no cover

    def __next__(self) -> MockChunk:
        if self.index >= len(self.chunks):
            raise StopIteration
        chunk = self.chunks[self.index]
        self.index += 1
        return chunk

    def close(self) -> None:
        self.closed = True


class MockAsyncStream(AsyncStreamProtocol[MockChunk]):
    def __init__(self, chunks: list[MockChunk]) -> None:
        self.chunks = chunks
        self.index = 0
        self.closed = False

    def __aiter__(self) -> AsyncIterator[MockChunk]:
        return self  # pragma: no cover

    async def __anext__(self) -> MockChunk:
        if self.index >= len(self.chunks):
            raise StopAsyncIteration
        chunk = self.chunks[self.index]
        self.index += 1
        return chunk

    async def aclose(self) -> None:
        self.closed = True  # pragma: no cover


def test_choice_buffer_init() -> None:
    buffer = ChoiceBuffer(0)
    assert (
        buffer.index,
        buffer.finish_reason,
        buffer.text_content,
        buffer.tool_calls_buffers,
    ) == snapshot((0, None, [], []))


def test_append_text_content() -> None:
    buffer = ChoiceBuffer(0)
    buffer.append_text_content("Hello")
    buffer.append_text_content(" World")

    assert buffer.text_content == snapshot(["Hello", " World"])


def test_append_tool_call() -> None:
    buffer = ChoiceBuffer(0)

    tool_call = Mock()
    tool_call.index = 0
    tool_call.id = "call_123"
    tool_call.function = Mock()
    tool_call.function.name = "test_func"
    tool_call.function.arguments = '{"arg": "value"}'

    buffer.append_tool_call(tool_call)

    assert len(buffer.tool_calls_buffers) == 1
    assert vars(buffer.tool_calls_buffers[0]) == snapshot(
        {
            "index": 0,
            "tool_call_id": "call_123",
            "function_name": "test_func",
            "arguments": ['{"arg": "value"}'],
        }
    )


def test_append_multiple_tool_calls() -> None:
    buffer = ChoiceBuffer(0)

    tool_call1 = Mock(index=0, id="call_1")
    tool_call1.function = Mock(name="func1", arguments='{"a": 1}')
    tool_call2 = Mock(index=1, id="call_2")
    tool_call2.function = Mock(name="func2", arguments='{"b": 2}')
    tool_call3 = Mock(index=0, id="call_1")
    tool_call3.function = Mock(name="func1", arguments='{"c": 3}')

    buffer.append_tool_call(tool_call1)
    buffer.append_tool_call(tool_call2)
    buffer.append_tool_call(tool_call3)

    assert len(buffer.tool_calls_buffers) == 2
    tool_call_buffer_0 = buffer.tool_calls_buffers[0]
    assert tool_call_buffer_0 is not None
    assert tool_call_buffer_0.arguments == snapshot(['{"a": 1}', '{"c": 3}'])
    tool_call_buffer_1 = buffer.tool_calls_buffers[1]
    assert tool_call_buffer_1 is not None
    assert tool_call_buffer_1.arguments == snapshot(['{"b": 2}'])


def test_tool_call_buffer_init() -> None:
    buffer = ToolCallBuffer(0, "call_123", "test_func")

    assert vars(buffer) == snapshot(
        {
            "index": 0,
            "tool_call_id": "call_123",
            "function_name": "test_func",
            "arguments": [],
        }
    )


def test_append_arguments() -> None:
    buffer = ToolCallBuffer(0, "call_123", "test_func")

    buffer.append_arguments('{"part1": ')
    buffer.append_arguments('"value",')
    buffer.append_arguments(' "part2": "value2"}')

    assert buffer.arguments == snapshot(
        ['{"part1": ', '"value",', ' "part2": "value2"}']
    )


def test_set_server_address_from_base_url() -> None:
    attributes: dict[str, Any] = {}
    client_instance = Mock()
    client_instance._client = httpx.Client(base_url="https://api.openai.com:443")

    set_server_address_and_port(client_instance, attributes)

    assert attributes == {"server.address": "api.openai.com"}


def test_set_server_address_no_port() -> None:
    attributes: dict[str, Any] = {}
    client_instance = Mock()
    client_instance._client = httpx.Client(base_url="https://api.example.com")

    set_server_address_and_port(client_instance, attributes)

    assert attributes == {"server.address": "api.example.com"}


def test_set_server_address_http() -> None:
    attributes: dict[str, Any] = {}
    client_instance = Mock()
    client_instance._client = httpx.Client(base_url="http://localhost:8080")

    set_server_address_and_port(client_instance, attributes)

    assert attributes == {"server.address": "localhost", "server.port": 8080}


def test_set_server_address_no_base_url() -> None:
    attributes: dict[str, Any] = {}
    client_instance = Mock()
    client_instance._client = Mock()
    client_instance._client.base_url = None

    set_server_address_and_port(client_instance, attributes)

    assert attributes == {}


def test_stream_wrapper_context_manager_with_exception() -> None:
    span = Mock(spec=Span)
    stream = MockStream([MockChunk("Hello")])
    metadata = MockMetadata()
    chunk_handler = MockChunkHandler()
    cleanup_handler = Mock()

    wrapper = StreamWrapper(span, stream, metadata, chunk_handler, cleanup_handler)

    with pytest.raises(ValueError), wrapper:
        raise ValueError("Test error")

    span.set_status.assert_called_once()
    status_call_args = span.set_status.call_args[0][0]
    assert isinstance(status_call_args, Status)
    assert status_call_args.status_code == StatusCode.ERROR
    assert "Test error" in str(status_call_args.description)

    span.set_attribute.assert_called_once_with("error.type", "ValueError")
    cleanup_handler.assert_called_once()
    span.end.assert_called_once()


def test_stream_wrapper_iteration() -> None:
    span = Mock(spec=Span)
    chunks = [MockChunk("Hello "), MockChunk("World"), MockChunk("!", "stop")]
    stream = MockStream(chunks)
    metadata = MockMetadata()
    chunk_handler = MockChunkHandler()

    processed_buffers: list[ChoiceBuffer] = []

    def cleanup(
        _span: Span, metadata_arg: MockMetadata, buffers: list[ChoiceBuffer]
    ) -> None:
        processed_buffers.extend(buffers)
        assert metadata_arg == {"prompt_tokens": 10, "completion_tokens": 5}

    cleanup_handler = Mock(side_effect=cleanup)

    wrapper = StreamWrapper(span, stream, metadata, chunk_handler, cleanup_handler)

    collected_chunks = list(wrapper)

    assert collected_chunks == chunks
    assert len(processed_buffers) == 1
    buffer = processed_buffers[0]
    assert (
        buffer.index,
        buffer.finish_reason,
        buffer.text_content,
        len(buffer.tool_calls_buffers),
    ) == snapshot((0, "stop", ["Hello ", "World", "!"], 0))
    assert metadata == {"prompt_tokens": 10, "completion_tokens": 5}

    cleanup_handler.assert_called_once()
    span.end.assert_called_once()


def test_stream_wrapper_iteration_with_exception() -> None:
    span = Mock(spec=Span)

    class ErrorStream(StreamProtocol[MockChunk]):
        def __init__(self) -> None:
            self.index = 0

        def __iter__(self) -> Iterator[MockChunk]:
            return self  # pragma: no cover

        def __next__(self) -> MockChunk:
            if self.index == 0:
                self.index += 1
                return MockChunk("chunk1")
            raise RuntimeError("Stream error")

        def close(self) -> None: ...

    stream = ErrorStream()
    metadata = MockMetadata()
    chunk_handler = MockChunkHandler()
    cleanup_handler = Mock()

    wrapper = StreamWrapper(span, stream, metadata, chunk_handler, cleanup_handler)

    with pytest.raises(RuntimeError, match="Stream error"):
        list(wrapper)

    span.set_status.assert_called_once()
    status_call_args = span.set_status.call_args[0][0]
    assert isinstance(status_call_args, Status)
    assert (status_call_args.status_code, status_call_args.description) == snapshot(
        (StatusCode.ERROR, "Stream error")
    )

    span.set_attribute.assert_called_once_with("error.type", "RuntimeError")
    cleanup_handler.assert_called_once()
    span.end.assert_called_once()

    assert len(wrapper.choice_buffers) == 1
    assert wrapper.choice_buffers[0].text_content == snapshot(["chunk1"])


def test_stream_wrapper_close() -> None:
    span = Mock(spec=Span)
    stream = MockStream([MockChunk("Hello")])
    metadata = MockMetadata()
    chunk_handler = MockChunkHandler()
    cleanup_handler = Mock()

    wrapper = StreamWrapper(span, stream, metadata, chunk_handler, cleanup_handler)

    assert not stream.closed

    wrapper.close()

    assert stream.closed

    cleanup_handler.assert_called_once()
    span.end.assert_called_once()


@pytest.mark.asyncio
async def test_async_stream_wrapper_context_manager_with_exception() -> None:
    span = Mock(spec=Span)
    stream = Mock(spec=AsyncStreamProtocol)
    metadata = MockMetadata()
    chunk_handler = Mock(spec=ChunkHandler)
    cleanup_handler = Mock()

    wrapper = AsyncStreamWrapper(span, stream, metadata, chunk_handler, cleanup_handler)

    with pytest.raises(ValueError):
        async with wrapper:
            raise ValueError("Test error")

    span.set_status.assert_called_once()
    status_call_args = span.set_status.call_args[0][0]
    assert isinstance(status_call_args, Status)
    assert status_call_args.status_code == StatusCode.ERROR
    span.set_attribute.assert_called_once_with("error.type", "ValueError")
    cleanup_handler.assert_called_once()
    span.end.assert_called_once()


@pytest.mark.asyncio
async def test_async_stream_wrapper_iteration() -> None:
    span = Mock(spec=Span)
    chunks = [MockChunk("Hello "), MockChunk("async"), MockChunk("!", "stop")]
    stream = MockAsyncStream(chunks)
    metadata = MockMetadata()
    chunk_handler = MockChunkHandler()

    processed_buffers: list[ChoiceBuffer] = []

    def cleanup(
        _span: Span, metadata_arg: MockMetadata, buffers: list[ChoiceBuffer]
    ) -> None:
        processed_buffers.extend(buffers)
        assert metadata_arg == {"prompt_tokens": 10, "completion_tokens": 5}

    cleanup_handler = Mock(side_effect=cleanup)

    wrapper = AsyncStreamWrapper(span, stream, metadata, chunk_handler, cleanup_handler)

    collected_chunks = []
    async for chunk in wrapper:
        collected_chunks.append(chunk)

    assert collected_chunks == chunks
    assert len(processed_buffers) == 1
    buffer = processed_buffers[0]
    assert (
        buffer.index,
        buffer.finish_reason,
        buffer.text_content,
        len(buffer.tool_calls_buffers),
    ) == snapshot((0, "stop", ["Hello ", "async", "!"], 0))
    assert metadata == {"prompt_tokens": 10, "completion_tokens": 5}

    cleanup_handler.assert_called_once()
    span.end.assert_called_once()


@pytest.mark.asyncio
async def test_async_stream_wrapper_iteration_with_exception() -> None:
    span = Mock(spec=Span)

    class AsyncStreamWithError(AsyncStreamProtocol[MockChunk]):
        def __init__(self) -> None:
            self._count = 0

        def __aiter__(self) -> AsyncIterator[MockChunk]:
            return self  # pragma: no cover

        async def __anext__(self) -> MockChunk:
            self._count += 1
            if self._count == 1:
                return MockChunk("chunk1")
            else:
                raise RuntimeError("Stream error")

        async def aclose(self) -> None:
            pass  # pragma: no cover

    stream = AsyncStreamWithError()

    metadata = MockMetadata()
    chunk_handler = Mock(spec=ChunkHandler)
    cleanup_handler = Mock()

    wrapper = AsyncStreamWrapper(span, stream, metadata, chunk_handler, cleanup_handler)

    with pytest.raises(RuntimeError):
        chunks = []
        async for chunk in wrapper:
            chunks.append(chunk)

    span.set_status.assert_called_once()
    status_call_args = span.set_status.call_args[0][0]
    assert isinstance(status_call_args, Status)
    assert status_call_args.status_code == StatusCode.ERROR
    span.set_attribute.assert_called_once_with("error.type", "RuntimeError")
    cleanup_handler.assert_called_once()
    span.end.assert_called_once()


@pytest.mark.asyncio
async def test_async_stream_wrapper_close() -> None:
    span = Mock(spec=Span)
    stream = Mock(spec=AsyncStreamProtocol)

    metadata = MockMetadata()
    chunk_handler = Mock(spec=ChunkHandler)
    cleanup_handler = Mock()

    wrapper = AsyncStreamWrapper(span, stream, metadata, chunk_handler, cleanup_handler)
    await wrapper.close()

    stream.aclose.assert_called_once()
    cleanup_handler.assert_called_once()
    span.end.assert_called_once()
