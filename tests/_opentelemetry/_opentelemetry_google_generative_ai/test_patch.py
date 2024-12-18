"""Tests for Vertex AI OpenTelemetry patching."""

from unittest.mock import AsyncMock, Mock

import pytest
from opentelemetry.trace import StatusCode

from lilypad._opentelemetry._opentelemetry_vertex.patch import (
    vertex_generate_content,
    vertex_generate_content_async,
)


@pytest.fixture
def mock_span():
    span = Mock()
    span.is_recording.return_value = True
    return span


@pytest.fixture
def mock_tracer(mock_span):
    tracer = Mock()

    @pytest.fixture
    def start_span():
        yield mock_span

    # Use a context manager mock:
    def start_as_current_span(*args, **kwargs):
        class SpanContext:
            def __enter__(self):
                return mock_span

            def __exit__(self, exc_type, exc_value, traceback):
                pass

        return SpanContext()

    tracer.start_as_current_span.side_effect = start_as_current_span
    return tracer


def test_vertex_generate_content(mock_tracer, mock_span):
    wrapped = Mock()
    wrapped.return_value = "mock_result"
    instance = Mock(_model_name="gemini-pro")
    kwargs = {"contents": [{"role": "user", "parts": ["Hello"]}], "stream": False}

    decorated = vertex_generate_content(mock_tracer)
    result = decorated(wrapped, instance, (), kwargs)

    assert result == "mock_result"
    mock_tracer.start_as_current_span.assert_called_once()


def test_vertex_generate_content_error(mock_tracer, mock_span):
    error = Exception("Test error")
    wrapped = Mock(side_effect=error)
    instance = Mock(_model_name="gemini-pro")
    kwargs = {}

    decorated = vertex_generate_content(mock_tracer)
    with pytest.raises(Exception) as exc_info:
        decorated(wrapped, instance, (), kwargs)

    assert exc_info.value is error
    mock_span.set_status.assert_called_once()
    called_args = mock_span.set_status.call_args[0][0]
    assert called_args.status_code == StatusCode.ERROR
    assert called_args.description == str(error)


@pytest.mark.asyncio
async def test_vertex_generate_content_async(mock_tracer, mock_span):
    wrapped = AsyncMock()
    wrapped.return_value = "mock_async_result"
    instance = Mock(_model_name="gemini-pro")
    kwargs = {"contents": [{"role": "user", "parts": ["Hello"]}], "stream": False}

    decorated = vertex_generate_content_async(mock_tracer)
    result = await decorated(wrapped, instance, (), kwargs)

    assert result == "mock_async_result"
    mock_tracer.start_as_current_span.assert_called_once()


@pytest.mark.asyncio
async def test_vertex_generate_content_async_error(mock_tracer, mock_span):
    error = Exception("Async error")
    wrapped = AsyncMock(side_effect=error)
    instance = Mock(_model_name="gemini-pro")
    kwargs = {}

    decorated = vertex_generate_content_async(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        await decorated(wrapped, instance, (), kwargs)

    assert exc_info.value is error
    mock_span.set_status.assert_called_once()
    called_args = mock_span.set_status.call_args[0][0]
    assert called_args.status_code == StatusCode.ERROR
    assert called_args.description == str(error)
