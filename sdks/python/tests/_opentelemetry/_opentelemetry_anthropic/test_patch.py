"""Tests for Anthropic OpenTelemetry patching."""

from contextlib import contextmanager
from unittest.mock import Mock, AsyncMock

import pytest
from opentelemetry.trace import StatusCode

from lilypad.lib._opentelemetry._opentelemetry_anthropic.patch import (
    chat_completions_create,
    chat_completions_create_async,
)


@pytest.fixture
def mock_content_block():
    content = Mock()
    content.text = "Hello, world!"
    content.type = "text"
    return content


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
def mock_response(mock_content_block):
    response = Mock()
    # Setup Anthropic-specific response attributes
    response.model = "claude-3-opus-20240229"
    response.id = "msg_123"
    response.usage = Mock(input_tokens=10, output_tokens=20)
    response.role = "assistant"
    # Set content as a list of content blocks
    response.content = [mock_content_block]
    response.stop_reason = "stop"
    return response


def test_chat_completions_create(mock_tracer, mock_response):
    wrapped = Mock()
    wrapped.return_value = mock_response
    instance = Mock()
    kwargs = {
        "messages": [{"role": "user", "content": "Hello"}],
        "model": "claude-3-opus-20240229",
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
    kwargs = {"model": "claude-3-opus-20240229"}

    decorator = chat_completions_create(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        decorator(wrapped, instance, (), kwargs)

    assert str(exc_info.value) == str(error)
    called_status = mock_span.set_status.call_args[0][0]
    assert called_status.status_code == StatusCode.ERROR
    assert called_status.description == str(error)


@pytest.mark.asyncio
async def test_chat_completions_create_async(mock_tracer, mock_response):
    wrapped = AsyncMock()
    wrapped.return_value = mock_response
    instance = Mock()
    kwargs = {
        "messages": [{"role": "user", "content": "Hello"}],
        "model": "claude-3-opus-20240229",
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
    kwargs = {"model": "claude-3-opus-20240229"}

    decorator = chat_completions_create_async(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        await decorator(wrapped, instance, (), kwargs)

    assert str(exc_info.value) == str(error)
    called_status = mock_span.set_status.call_args[0][0]
    assert called_status.status_code == StatusCode.ERROR
    assert called_status.description == str(error)
