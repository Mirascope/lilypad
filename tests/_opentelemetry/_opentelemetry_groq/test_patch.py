"""Tests for Groq OpenTelemetry patching."""

from contextlib import contextmanager
from unittest.mock import AsyncMock, Mock

import pytest
from opentelemetry.trace import Status, StatusCode

from lilypad._opentelemetry._opentelemetry_groq.patch import (
    chat_completions_create,
    chat_completions_create_async,
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
    response.choices = []
    response.model = "mixtral-8x7b-32768"
    response.id = "test-id"
    response.usage = Mock(prompt_tokens=10, completion_tokens=20)
    return response


def test_chat_completions_create(mock_tracer, mock_response):
    wrapped = Mock()
    wrapped.return_value = mock_response
    instance = Mock()
    kwargs = {
        "model": "mixtral-8x7b-32768",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False,
    }

    decorator = chat_completions_create(mock_tracer)
    result = decorator(wrapped, instance, (), kwargs)

    assert result is mock_response
    mock_tracer.start_as_current_span.assert_called_once()


def test_chat_completions_create_error(mock_tracer, mock_span):
    error = Exception("Test error")
    wrapped = Mock(side_effect=error)
    instance = Mock()
    kwargs = {
        "model": "mixtral-8x7b-32768",
    }

    decorator = chat_completions_create(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        decorator(wrapped, instance, (), kwargs)
        assert exc_info.value is error
        mock_span.set_status.assert_called_with(Status(StatusCode.ERROR, str(error)))


@pytest.mark.asyncio
async def test_chat_completions_create_async(mock_tracer, mock_response):
    wrapped = AsyncMock()
    wrapped.return_value = mock_response
    instance = Mock()
    kwargs = {
        "model": "mixtral-8x7b-32768",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False,
    }

    decorator = chat_completions_create_async(mock_tracer)
    result = await decorator(wrapped, instance, (), kwargs)

    assert result is mock_response
    mock_tracer.start_as_current_span.assert_called_once()


@pytest.mark.asyncio
async def test_chat_completions_create_async_error(mock_tracer, mock_span):
    error = Exception("Test error")
    wrapped = AsyncMock(side_effect=error)
    instance = Mock()
    kwargs = {
        "model": "mixtral-8x7b-32768",
    }

    decorator = chat_completions_create_async(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        await decorator(wrapped, instance, (), kwargs)

    assert str(exc_info.value) == str(error)
    called_status = mock_span.set_status.call_args[0][0]
    assert called_status.status_code == StatusCode.ERROR
    assert called_status.description == str(error)


def test_chat_completions_create_streaming(mock_tracer, mock_response):
    wrapped = Mock()
    chunk = Mock()
    choice = Mock()
    choice.index = 0  # Add index attribute
    choice.delta = Mock(content="Hello")
    choice.finish_reason = None
    chunk.choices = [choice]
    chunk.model = "mixtral-8x7b-32768"
    chunk.id = "test-id"
    wrapped.return_value = [chunk]  # Return an iterator for streaming
    instance = Mock()
    kwargs = {
        "model": "mixtral-8x7b-32768",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True,
    }

    decorator = chat_completions_create(mock_tracer)
    result = list(decorator(wrapped, instance, (), kwargs))

    assert len(result) == 1
    assert result[0] is chunk
    mock_tracer.start_as_current_span.assert_called_once()


@pytest.mark.asyncio
async def test_chat_completions_create_async_streaming(mock_tracer, mock_response):
    wrapped = AsyncMock()
    chunk = Mock()
    choice = Mock()
    choice.index = 0  # Add index attribute
    choice.delta = Mock(content="Hello")
    choice.finish_reason = None
    chunk.choices = [choice]
    chunk.model = "mixtral-8x7b-32768"
    chunk.id = "test-id"

    # Create a proper async iterator
    async def async_iter():
        yield chunk

    wrapped.return_value = async_iter()
    instance = Mock()
    kwargs = {
        "model": "mixtral-8x7b-32768",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True,
    }

    decorator = chat_completions_create_async(mock_tracer)
    result = [chunk async for chunk in await decorator(wrapped, instance, (), kwargs)]

    assert len(result) == 1
    assert result[0] is chunk
    mock_tracer.start_as_current_span.assert_called_once()
