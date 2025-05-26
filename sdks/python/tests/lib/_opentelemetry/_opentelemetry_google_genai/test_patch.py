from contextlib import contextmanager
from unittest.mock import Mock, AsyncMock

import pytest
from opentelemetry.trace import StatusCode

from lilypad.lib._opentelemetry._opentelemetry_google_genai.patch import (
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
