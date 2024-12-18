"""Tests for Google Generative AI OpenTelemetry patching."""

from contextlib import contextmanager
from unittest.mock import AsyncMock, Mock

import pytest
from opentelemetry.trace import Status, StatusCode

from lilypad._opentelemetry._opentelemetry_google_generative_ai.patch import (
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


@pytest.fixture
def mock_response():
    response = Mock()
    # Mock required attributes for set_response_attributes
    response.candidates = []
    response.model = "gemini-pro"
    return response


def test_generate_content(mock_tracer, mock_response):
    wrapped = Mock()
    wrapped.return_value = mock_response
    instance = Mock()
    # Set mock model name for get_gemini_model_name
    instance._model_id = "gemini-pro"
    kwargs = {"contents": [{"role": "user", "parts": ["Hello"]}], "stream": False}

    decorated = generate_content(mock_tracer)
    result = decorated(wrapped, instance, (), kwargs)

    assert result is mock_response
    mock_tracer.start_as_current_span.assert_called_once()


def test_generate_content_error(mock_tracer, mock_span):
    error = Exception("Test error")
    wrapped = Mock(side_effect=error)
    instance = Mock()
    kwargs = {}

    decorated = generate_content(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        decorated(wrapped, instance, (), kwargs)

    assert exc_info.value is error
    error_status = Status(StatusCode.ERROR, str(error))
    mock_span.set_status.assert_called_once()
    called_args = mock_span.set_status.call_args[0][0]
    assert called_args.status_code == error_status.status_code
    assert called_args.description == error_status.description


@pytest.mark.asyncio
async def test_generate_content_async(mock_tracer, mock_response):
    wrapped = AsyncMock()
    wrapped.return_value = mock_response
    instance = Mock()
    # Set mock model name for get_gemini_model_name
    instance._model_id = "gemini-pro"
    kwargs = {"contents": [{"role": "user", "parts": ["Hello"]}], "stream": False}

    decorated = generate_content_async(mock_tracer)
    result = await decorated(wrapped, instance, (), kwargs)

    assert result is mock_response
    mock_tracer.start_as_current_span.assert_called_once()


@pytest.mark.asyncio
async def test_generate_content_async_error(mock_tracer, mock_span):
    error = Exception("Test error")
    wrapped = AsyncMock(side_effect=error)
    instance = Mock()
    kwargs = {}

    decorated = generate_content_async(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        await decorated(wrapped, instance, (), kwargs)

    assert exc_info.value is error
    error_status = Status(StatusCode.ERROR, str(error))
    mock_span.set_status.assert_called_once()
    called_args = mock_span.set_status.call_args[0][0]
    assert called_args.status_code == error_status.status_code
    assert called_args.description == error_status.description
