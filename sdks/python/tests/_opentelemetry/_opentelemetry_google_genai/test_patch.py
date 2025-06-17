from contextlib import contextmanager
from unittest.mock import Mock, AsyncMock, patch

import pytest
from opentelemetry.trace import StatusCode

from lilypad._opentelemetry._opentelemetry_google_genai.patch import (
    generate_content,
    generate_content_async,
)


@pytest.fixture
def mock_span():
    span = Mock()
    span.is_recording.return_value = True
    return span


@pytest.fixture
def mock_tracer(mock_span):
    tracer = Mock()

    @contextmanager
    def start_span(*args, **kwargs):
        yield mock_span

    tracer.start_as_current_span.side_effect = start_span
    return tracer


def test_generate_content_success(mock_tracer, mock_span):
    wrapped = Mock()
    wrapped.return_value = "sync_result"
    instance = Mock(_model_name="google-genai-model")
    kwargs = {"contents": [{"role": "user", "parts": ["Hello"]}], "stream": False}
    decorator = generate_content(mock_tracer)
    result = decorator(wrapped, instance, (), kwargs)
    assert result == "sync_result"
    mock_tracer.start_as_current_span.assert_called_once()


def test_generate_content_error(mock_tracer, mock_span):
    error = Exception("Sync error")
    wrapped = Mock(side_effect=error)
    instance = Mock(_model_name="google-genai-model")
    kwargs = {}
    decorator = generate_content(mock_tracer)
    with pytest.raises(Exception) as exc_info:
        decorator(wrapped, instance, (), kwargs)
    assert exc_info.value is error
    mock_span.set_status.assert_called_once()
    status = mock_span.set_status.call_args[0][0]
    assert status.status_code == StatusCode.ERROR
    assert status.description == "Sync error"
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_generate_content_async_success(mock_tracer, mock_span):
    wrapped = AsyncMock()
    wrapped.return_value = "async_result"
    instance = Mock(_model_name="google-genai-model")
    kwargs = {"contents": [{"role": "user", "parts": ["Hello async"]}], "stream": False}
    decorator = generate_content_async(mock_tracer)
    result = await decorator(wrapped, instance, (), kwargs)
    assert result == "async_result"
    mock_tracer.start_as_current_span.assert_called_once()


@pytest.mark.asyncio
async def test_generate_content_async_error(mock_tracer, mock_span):
    error = Exception("Async error")
    wrapped = AsyncMock(side_effect=error)
    instance = Mock(_model_name="google-genai-model")
    kwargs = {}
    decorator = generate_content_async(mock_tracer)
    with pytest.raises(Exception) as exc_info:
        await decorator(wrapped, instance, (), kwargs)
    assert exc_info.value is error
    mock_span.set_status.assert_called_once()
    status = mock_span.set_status.call_args[0][0]
    assert status.status_code == StatusCode.ERROR
    assert status.description == "Async error"
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_generate_content_async_streaming(mock_tracer, mock_span):
    class DummyCandidate:
        def __init__(self, index, finish_reason):
            self.index = index
            self.finish_reason = finish_reason

    class DummyChunk:
        def __init__(self, candidates):
            self.candidates = candidates

    candidate = DummyCandidate(0, "completed")

    async def async_stream():
        yield DummyChunk([candidate])
        yield DummyChunk([candidate])

    wrapped = AsyncMock()
    wrapped.return_value = async_stream()
    instance = Mock(_model_name="google-genai-model")
    kwargs = {
        "contents": [{"role": "user", "parts": ["Async streaming test"]}],
        "stream": True,
    }
    decorator = generate_content_async(mock_tracer)
    result = await decorator(wrapped, instance, (), kwargs)
    chunks = [chunk async for chunk in result]
    assert len(chunks) == 2
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.end.assert_called_once()


def test_generate_content_with_string_contents(mock_tracer, mock_span):
    """Test generate_content with string contents (line 48)."""
    wrapped = Mock()
    wrapped.return_value = "result"
    instance = Mock(_model_name="google-genai-model")
    kwargs = {"contents": "Hello world", "stream": False}

    decorator = generate_content(mock_tracer)
    result = decorator(wrapped, instance, (), kwargs)

    assert result == "result"
    # Should convert string to list format
    mock_span.add_event.assert_called()


def test_generate_content_with_dict_contents(mock_tracer, mock_span):
    """Test generate_content with dict contents (line 50)."""
    wrapped = Mock()
    wrapped.return_value = "result"
    instance = Mock(_model_name="google-genai-model")
    kwargs = {"contents": {"role": "user", "parts": ["Hello"]}, "stream": False}

    decorator = generate_content(mock_tracer)
    result = decorator(wrapped, instance, (), kwargs)

    assert result == "result"
    # Should convert dict to list format
    mock_span.add_event.assert_called()


def test_generate_content_with_streaming(mock_tracer, mock_span):
    """Test generate_content with streaming (line 57)."""

    def stream_generator():
        yield "chunk1"
        yield "chunk2"

    wrapped = Mock()
    wrapped.return_value = stream_generator()
    instance = Mock(_model_name="google-genai-model")
    kwargs = {"contents": [{"role": "user", "parts": ["Hello"]}], "stream": True}

    with patch("lilypad._opentelemetry._opentelemetry_google_genai.patch.set_stream") as mock_set_stream:
        decorator = generate_content(mock_tracer, stream=True)
        result = decorator(wrapped, instance, (), kwargs)

        # Should call set_stream for streaming
        mock_set_stream.assert_called_once()


@pytest.mark.asyncio
async def test_generate_content_async_with_string_contents(mock_tracer, mock_span):
    """Test generate_content_async with string contents (line 101)."""
    wrapped = AsyncMock()
    wrapped.return_value = "async_result"
    instance = Mock(_model_name="google-genai-model")
    kwargs = {"contents": "Hello async world", "stream": False}

    decorator = generate_content_async(mock_tracer)
    result = await decorator(wrapped, instance, (), kwargs)

    assert result == "async_result"
    # Should convert string to list format
    mock_span.add_event.assert_called()


@pytest.mark.asyncio
async def test_generate_content_async_with_dict_contents(mock_tracer, mock_span):
    """Test generate_content_async with dict contents (line 103)."""
    wrapped = AsyncMock()
    wrapped.return_value = "async_result"
    instance = Mock(_model_name="google-genai-model")
    kwargs = {"contents": {"role": "user", "parts": ["Hello async"]}, "stream": False}

    decorator = generate_content_async(mock_tracer)
    result = await decorator(wrapped, instance, (), kwargs)

    assert result == "async_result"
    # Should convert dict to list format
    mock_span.add_event.assert_called()


@pytest.mark.asyncio
async def test_generate_content_async_streaming_with_candidates(mock_tracer, mock_span):
    """Test generate_content_async streaming with candidates (lines 110-137)."""

    class MockFinishReason:
        def __init__(self, value):
            self.value = value

    class DummyCandidate:
        def __init__(self, index, finish_reason_value):
            self.index = index
            self.finish_reason = MockFinishReason(finish_reason_value) if finish_reason_value else None

    class DummyChunk:
        def __init__(self, candidates):
            self.candidates = candidates

    candidate1 = DummyCandidate(0, "in_progress")
    candidate2 = DummyCandidate(1, "completed")

    async def async_stream():
        yield DummyChunk([candidate1])
        yield DummyChunk([candidate2])

    wrapped = AsyncMock()
    wrapped.return_value = async_stream()
    instance = Mock(_model_name="google-genai-model")
    kwargs = {
        "contents": [{"role": "user", "parts": ["Streaming with candidates"]}],
        "stream": True,
    }

    decorator = generate_content_async(mock_tracer)
    result = await decorator(wrapped, instance, (), kwargs)

    # Process the stream
    chunks = [chunk async for chunk in result]
    assert len(chunks) == 2

    # Should add events for candidates and set finish reasons
    mock_span.add_event.assert_called()
    mock_span.set_attributes.assert_called()


@pytest.mark.asyncio
async def test_generate_content_async_streaming_with_no_finish_reason(mock_tracer, mock_span):
    """Test generate_content_async streaming with candidate without finish reason."""

    class DummyCandidate:
        def __init__(self, index):
            self.index = index
            self.finish_reason = None  # No finish reason

    class DummyChunk:
        def __init__(self, candidates):
            self.candidates = candidates

    candidate = DummyCandidate(0)

    async def async_stream():
        yield DummyChunk([candidate])

    wrapped = AsyncMock()
    wrapped.return_value = async_stream()
    instance = Mock(_model_name="google-genai-model")
    kwargs = {
        "contents": [{"role": "user", "parts": ["Test"]}],
        "stream": True,
    }

    decorator = generate_content_async(mock_tracer)
    result = await decorator(wrapped, instance, (), kwargs)

    # Process the stream
    chunks = [chunk async for chunk in result]
    assert len(chunks) == 1

    # Should handle None finish reason gracefully
    mock_span.add_event.assert_called()
