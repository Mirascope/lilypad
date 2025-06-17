"""Tests for OpenTelemetry utility classes and functions."""

from unittest.mock import Mock, AsyncMock, create_autospec

import pytest
from httpx import URL
from opentelemetry.trace import StatusCode

from lilypad._opentelemetry._utils import (
    ChoiceBuffer,
    StreamWrapper,
    ToolCallBuffer,
    AsyncStreamWrapper,
    set_server_address_and_port,
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


# Additional tests for improved coverage


def test_choice_buffer_tool_call_handling():
    """Test tool call handling in ChoiceBuffer (lines 63-70)"""
    buffer = ChoiceBuffer(0)

    # Mock tool call object
    mock_tool_call = Mock()
    mock_tool_call.index = 0
    mock_tool_call.id = "test-id"
    mock_tool_call.function.name = "test_function"
    mock_tool_call.function.arguments = {"arg1": "value1"}

    # Test appending tool call - this will hit lines 63-70
    buffer.append_tool_call(mock_tool_call)

    assert len(buffer.tool_calls_buffers) == 1
    assert buffer.tool_calls_buffers[0] is not None
    assert buffer.tool_calls_buffers[0].tool_call_id == "test-id"
    assert buffer.tool_calls_buffers[0].function_name == "test_function"

    # Test appending another tool call with higher index
    mock_tool_call2 = Mock()
    mock_tool_call2.index = 2
    mock_tool_call2.id = "test-id-2"
    mock_tool_call2.function.name = "test_function_2"
    mock_tool_call2.function.arguments = {"arg2": "value2"}

    buffer.append_tool_call(mock_tool_call2)

    # Should have 3 slots (0, 1, 2) with slot 1 being None
    assert len(buffer.tool_calls_buffers) == 3
    assert buffer.tool_calls_buffers[0] is not None
    assert buffer.tool_calls_buffers[1] is None
    assert buffer.tool_calls_buffers[2] is not None


def test_stream_wrapper_with_cleanup_handler(mock_span, mock_stream, mock_metadata, mock_chunk_handler):
    """Test StreamWrapper with cleanup handler (line 115)"""
    cleanup_handler = Mock()

    wrapper = StreamWrapper(mock_span, mock_stream, mock_metadata, mock_chunk_handler, cleanup_handler)

    # Test cleanup with handler
    wrapper.setup()
    wrapper.cleanup()

    cleanup_handler.assert_called_once_with(mock_span, mock_metadata, wrapper.choice_buffers)
    mock_span.end.assert_called_once()


def test_stream_wrapper_context_manager(mock_span, mock_stream, mock_metadata, mock_chunk_handler):
    """Test StreamWrapper context manager (lines 126-127)"""
    wrapper = StreamWrapper(mock_span, mock_stream, mock_metadata, mock_chunk_handler)

    # Test context manager entry - this hits lines 126-127
    with wrapper as w:
        assert w is wrapper
        assert w._span_started


def test_stream_wrapper_context_manager_exception_handling(mock_span, mock_stream, mock_metadata, mock_chunk_handler):
    """Test StreamWrapper context manager exception handling (lines 130-136)"""
    wrapper = StreamWrapper(mock_span, mock_stream, mock_metadata, mock_chunk_handler)

    test_exception = ValueError("Test exception")

    # Test exception handling in context manager - this hits lines 130-136
    with pytest.raises(ValueError), wrapper:
        raise test_exception

    # Verify exception was handled properly
    mock_span.set_status.assert_called_once()
    status_call = mock_span.set_status.call_args[0][0]
    assert status_call.status_code == StatusCode.ERROR
    assert status_call.description == str(test_exception)

    mock_span.set_attribute.assert_called_once()
    attr_call = mock_span.set_attribute.call_args
    assert "error.type" in attr_call[0][0]
    assert attr_call[0][1] == "ValueError"

    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_stream_wrapper_async_close(mock_span, mock_metadata, mock_chunk_handler):
    """Test StreamWrapper async close method (lines 139-140)"""
    mock_stream = Mock()
    mock_stream.close = Mock()

    wrapper = StreamWrapper(mock_span, mock_stream, mock_metadata, mock_chunk_handler)
    wrapper.setup()

    # Test async close - this hits lines 139-140
    await wrapper.close()

    mock_stream.close.assert_called_once()
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_async_stream_wrapper_close_method(mock_span, mock_metadata, mock_chunk_handler):
    """Test AsyncStreamWrapper close method (lines 175-176)"""
    mock_stream = Mock()
    mock_stream.aclose = AsyncMock()

    wrapper = AsyncStreamWrapper(mock_span, mock_stream, mock_metadata, mock_chunk_handler)
    wrapper.setup()

    # Test async close - this hits lines 175-176
    await wrapper.close()

    mock_stream.aclose.assert_called_once()
    mock_span.end.assert_called_once()


def test_set_server_address_and_port_no_client():
    """Test set_server_address_and_port with no client (line 211)"""
    client_instance = Mock()
    client_instance._client = None
    attributes = {}

    # This should return early (line 211)
    set_server_address_and_port(client_instance, attributes)

    assert attributes == {}


def test_set_server_address_and_port_no_base_url():
    """Test set_server_address_and_port with no base_url (line 211)"""
    client_instance = Mock()
    base_client = Mock()
    base_client.base_url = None
    client_instance._client = base_client
    attributes = {}

    # This should return early (line 211)
    set_server_address_and_port(client_instance, attributes)

    assert attributes == {}


def test_set_server_address_and_port_with_httpx_url():
    """Test set_server_address_and_port with httpx URL (lines 215-216)"""
    client_instance = Mock()
    base_client = Mock()
    base_client.base_url = URL("https://api.example.com:8080/v1")
    client_instance._client = base_client
    attributes = {}

    set_server_address_and_port(client_instance, attributes)

    assert "server.address" in attributes
    assert attributes["server.address"] == "api.example.com"
    assert "server.port" in attributes
    assert attributes["server.port"] == 8080


def test_set_server_address_and_port_with_string_url():
    """Test set_server_address_and_port with string URL (lines 218-220)"""
    client_instance = Mock()
    base_client = Mock()
    base_client.base_url = "https://api.example.com:9000/v1"
    client_instance._client = base_client
    attributes = {}

    set_server_address_and_port(client_instance, attributes)

    assert "server.address" in attributes
    assert attributes["server.address"] == "api.example.com"
    assert "server.port" in attributes
    assert attributes["server.port"] == 9000


def test_set_server_address_and_port_default_https_port():
    """Test set_server_address_and_port with default HTTPS port (line 223)"""
    client_instance = Mock()
    base_client = Mock()
    base_client.base_url = URL("https://api.example.com/v1")  # No explicit port, defaults to 443
    client_instance._client = base_client
    attributes = {}

    set_server_address_and_port(client_instance, attributes)

    assert "server.address" in attributes
    assert attributes["server.address"] == "api.example.com"
    # Port 443 should not be added (line 223 condition)
    assert "server.port" not in attributes


def test_set_server_address_and_port_with_none_port():
    """Test set_server_address_and_port with None port (line 223)"""
    client_instance = Mock()
    base_client = Mock()
    base_client.base_url = "https://api.example.com"  # URL without port
    client_instance._client = base_client
    attributes = {}

    set_server_address_and_port(client_instance, attributes)

    assert "server.address" in attributes
    assert attributes["server.address"] == "api.example.com"
    # No port should be added when port is None
    assert "server.port" not in attributes
