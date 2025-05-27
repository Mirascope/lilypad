"""Tests for OpenTelemetry utility classes and functions."""

from unittest.mock import Mock, AsyncMock, create_autospec

import pytest
from opentelemetry.trace import StatusCode

from lilypad.lib._opentelemetry._utils import (
    ChoiceBuffer,
    StreamWrapper,
    ToolCallBuffer,
    AsyncStreamWrapper,
)


# Define concrete protocol implementations for mocking
class MockStreamProtocol:
    def __iter__(self):
        return self

    def __next__(self):
        raise NotImplementedError()

    def close(self):
        pass


class MockAsyncStreamProtocol:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        pass

    def __aiter__(self):
        return self

    async def __anext__(self):
        raise NotImplementedError

    async def aclose(self):
        pass


@pytest.fixture
def mock_span():
    return Mock()


@pytest.fixture
def mock_stream():
    # Create a stream mock that implements the iterator protocol
    stream = create_autospec(MockStreamProtocol)

    chunks = ["chunk1", "chunk2"]
    iter_obj = iter(chunks)

    stream.__iter__ = Mock(return_value=iter_obj)
    stream.__next__ = Mock(side_effect=iter_obj.__next__)
    stream.close = Mock()

    return stream


@pytest.fixture
def mock_async_stream():
    stream = create_autospec(MockAsyncStreamProtocol)
    chunks = ["chunk1", "chunk2"]
    index = 0

    # Mock __aiter__ to return self
    stream.__aiter__ = AsyncMock(return_value=stream)

    # Mock __anext__ to return chunks and eventually raise StopAsyncIteration
    async def async_next():
        nonlocal index
        if index >= len(chunks):
            raise StopAsyncIteration
        chunk = chunks[index]
        index += 1
        return chunk

    stream.__anext__ = AsyncMock(side_effect=async_next)
    stream.__aenter__ = AsyncMock(return_value=stream)
    stream.__aexit__ = AsyncMock(return_value=None)
    stream.aclose = AsyncMock()

    return stream


@pytest.fixture
def mock_metadata():
    return Mock()


@pytest.fixture
def mock_chunk_handler():
    handler = Mock()
    handler.extract_metadata = Mock()
    handler.process_chunk = Mock()
    return handler


def test_choice_buffer():
    buffer = ChoiceBuffer(0)
    assert buffer.index == 0
    assert buffer.finish_reason is None
    assert buffer.text_content == []
    assert buffer.tool_calls_buffers == []

    buffer.append_text_content("test")
    assert buffer.text_content == ["test"]


def test_tool_call_buffer():
    buffer = ToolCallBuffer(0, "test-id", "test-function")
    assert buffer.index == 0
    assert buffer.tool_call_id == "test-id"
    assert buffer.function_name == "test-function"
    assert buffer.arguments == []

    buffer.append_arguments({"arg": "value"})
    assert buffer.arguments == [{"arg": "value"}]


def test_stream_wrapper(mock_span, mock_stream, mock_metadata, mock_chunk_handler):
    wrapper = StreamWrapper(mock_span, mock_stream, mock_metadata, mock_chunk_handler)
    wrapper.setup()

    assert wrapper._span_started
    wrapper.cleanup()
    assert not wrapper._span_started
    mock_span.end.assert_called_once()


def test_stream_wrapper_iterator(mock_span, mock_stream, mock_metadata, mock_chunk_handler):
    wrapper = StreamWrapper(mock_span, mock_stream, mock_metadata, mock_chunk_handler)
    chunks = list(wrapper)

    assert chunks == ["chunk1", "chunk2"]
    assert mock_chunk_handler.process_chunk.call_count == 2


def test_stream_error_handling(mock_span, mock_stream, mock_metadata, mock_chunk_handler):
    error = Exception("Test error")
    stream = create_autospec(MockStreamProtocol)
    stream.__next__.side_effect = error

    wrapper = StreamWrapper(mock_span, stream, mock_metadata, mock_chunk_handler)

    with pytest.raises(Exception):  # noqa: B017
        list(wrapper)

    mock_span.set_status.assert_called_once()
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_async_stream_wrapper(mock_span, mock_async_stream, mock_metadata, mock_chunk_handler):
    wrapper = AsyncStreamWrapper(mock_span, mock_async_stream, mock_metadata, mock_chunk_handler)

    chunks = []
    async with wrapper as w:
        assert w._span_started
        async for chunk in w:
            chunks.append(chunk)

    assert not wrapper._span_started
    assert chunks == ["chunk1", "chunk2"]
    assert mock_chunk_handler.process_chunk.call_count == 2
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_async_stream_error_handling(mock_span, mock_async_stream, mock_metadata, mock_chunk_handler):
    """Test that errors during iteration are handled correctly"""
    error = Exception("Test error")
    stream = create_autospec(MockAsyncStreamProtocol)

    # Setup async mock behavior
    stream.__anext__ = AsyncMock(side_effect=error)
    stream.__aiter__ = AsyncMock(return_value=stream)
    stream.__aenter__ = AsyncMock(return_value=stream)
    stream.__aexit__ = AsyncMock(return_value=None)

    wrapper = AsyncStreamWrapper(mock_span, stream, mock_metadata, mock_chunk_handler)

    with pytest.raises(Exception) as exc_info:
        async with wrapper as w:
            await anext(w)

    # Verify the error handling
    assert exc_info.value is error
    assert mock_span.set_status.called
    status_call = mock_span.set_status.call_args[0][0]
    assert status_call.status_code == StatusCode.ERROR
    assert status_call.description == str(error)
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_async_stream_normal_case(mock_span, mock_async_stream, mock_metadata, mock_chunk_handler):
    """Test normal async stream operation"""
    stream = create_autospec(MockAsyncStreamProtocol)

    stream.__aenter__ = AsyncMock(return_value=stream)
    stream.__aexit__ = AsyncMock()
    stream.__aiter__ = AsyncMock(return_value=stream)
    stream.__anext__ = AsyncMock(side_effect=StopAsyncIteration)
    stream.aclose = AsyncMock()

    wrapper = AsyncStreamWrapper(mock_span, stream, mock_metadata, mock_chunk_handler)

    async with wrapper as w:
        async for _ in w:
            pass  # Normal operation, no items

    # Verify normal cleanup
    mock_span.end.assert_called_once()
