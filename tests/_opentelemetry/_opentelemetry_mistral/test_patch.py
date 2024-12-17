"""Tests for Mistral OpenTelemetry patching."""

from unittest.mock import AsyncMock, Mock

import pytest
from opentelemetry.trace import StatusCode

from lilypad._opentelemetry._opentelemetry_mistral.patch import (
    mistral_complete,
    mistral_complete_async,
)


@pytest.fixture
def mock_span():
    span = Mock()
    span.is_recording.return_value = True
    return span


@pytest.fixture
def mock_tracer(mock_span):
    tracer = Mock()

    def start_as_current_span(*args, **kwargs):
        class SpanContext:
            def __enter__(self):
                return mock_span

            def __exit__(self, exc_type, exc_val, exc_tb):
                pass

        return SpanContext()

    tracer.start_as_current_span.side_effect = start_as_current_span
    return tracer


def test_mistral_complete_success(mock_tracer, mock_span):
    wrapped = Mock()
    # Mock a response like ChatCompletionResponse
    response = Mock()
    response.model = "mistral-large-latest"
    usage = Mock()
    usage.prompt_tokens = 10
    usage.completion_tokens = 20
    response.usage = usage
    choice = Mock()
    choice.finish_reason = "stop"
    choice.message = Mock(content="Recommended: The Hobbit")
    response.choices = [choice]

    wrapped.return_value = response
    instance = Mock()
    kwargs = {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": "Hello"}],
    }

    decorator = mistral_complete(mock_tracer)
    result = decorator(wrapped, instance, (), kwargs)

    assert result is response
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.set_attributes.assert_called_once()
    mock_span.add_event.assert_called_once()


def test_mistral_complete_error(mock_tracer, mock_span):
    error = Exception("Test error")
    wrapped = Mock(side_effect=error)
    instance = Mock()
    kwargs = {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": "Hello"}],
    }

    decorator = mistral_complete(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        decorator(wrapped, instance, (), kwargs)

    assert exc_info.value is error
    mock_span.set_status.assert_called_once()
    called_status = mock_span.set_status.call_args[0][0]
    assert called_status.status_code == StatusCode.ERROR
    assert called_status.description == str(error)


@pytest.mark.asyncio
async def test_mistral_complete_async_success(mock_tracer, mock_span):
    wrapped = AsyncMock()
    response = Mock()
    response.model = "mistral-large-latest"
    usage = Mock()
    usage.prompt_tokens = 10
    usage.completion_tokens = 20
    response.usage = usage
    choice = Mock()
    choice.finish_reason = "stop"
    choice.message = Mock(content="Recommended: The Hobbit")
    response.choices = [choice]

    wrapped.return_value = response
    instance = Mock()
    kwargs = {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": "Hello"}],
    }

    decorator = mistral_complete_async(mock_tracer)
    result = await decorator(wrapped, instance, (), kwargs)

    assert result is response
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.set_attributes.assert_called_once()
    mock_span.add_event.assert_called_once()


@pytest.mark.asyncio
async def test_mistral_complete_async_error(mock_tracer, mock_span):
    error = Exception("Async error")
    wrapped = AsyncMock(side_effect=error)
    instance = Mock()
    kwargs = {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": "Hello"}],
    }

    decorator = mistral_complete_async(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        await decorator(wrapped, instance, (), kwargs)

    assert str(exc_info.value) == str(error)
    mock_span.set_status.assert_called_once()
    called_status = mock_span.set_status.call_args[0][0]
    assert called_status.status_code == StatusCode.ERROR
    assert called_status.description == str(error)
