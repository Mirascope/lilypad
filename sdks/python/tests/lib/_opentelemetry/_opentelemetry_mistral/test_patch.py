"""Tests for Mistral OpenTelemetry patching."""

from unittest.mock import Mock, AsyncMock

import pytest
from opentelemetry.trace import StatusCode

from lilypad.lib._opentelemetry._opentelemetry_mistral.patch import (
    mistral_stream_patch,
    mistral_complete_patch,
    mistral_stream_async_patch,
    mistral_complete_async_patch,
)


@pytest.fixture
def mock_span():
    span = Mock()
    span.is_recording.return_value = True
    return span


@pytest.fixture
def mock_tracer(mock_span):
    tracer = Mock()

    class SpanContext:
        def __enter__(self):
            return mock_span

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    tracer.start_as_current_span.side_effect = lambda *args, **kwargs: SpanContext()
    return tracer


def test_mistral_complete_patch_success(mock_tracer, mock_span):
    wrapped = Mock()
    response = Mock()
    response.model = "mistral-large-latest"
    usage = Mock()
    usage.prompt_tokens = 10
    usage.completion_tokens = 20
    usage.total_tokens = 30
    response.usage = usage
    response.choices = []
    wrapped.return_value = response

    decorator = mistral_complete_patch(mock_tracer)
    result = decorator(wrapped, None, (), {"model": "mistral-large-latest"})
    assert result is response
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.set_attributes.assert_called_once()
    mock_span.end.assert_called_once()


def test_mistral_complete_patch_error(mock_tracer, mock_span):
    error = Exception("Test error")
    wrapped = Mock(side_effect=error)
    decorator = mistral_complete_patch(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        decorator(wrapped, None, (), {"model": "mistral-large-latest"})
    assert exc_info.value is error
    mock_span.set_status.assert_called_once()
    status_call = mock_span.set_status.call_args[0][0]
    assert status_call.status_code == StatusCode.ERROR
    assert status_call.description == "Test error"
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_mistral_complete_async_patch_success(mock_tracer, mock_span):
    wrapped = AsyncMock()
    response = Mock()
    response.model = "mistral-large-latest"
    usage = Mock()
    usage.prompt_tokens = 10
    usage.completion_tokens = 20
    usage.total_tokens = 30
    response.usage = usage
    response.choices = []
    wrapped.return_value = response

    decorator = mistral_complete_async_patch(mock_tracer)
    result = await decorator(wrapped, None, (), {"model": "mistral-large-latest"})
    assert result is response
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.set_attributes.assert_called_once()
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_mistral_complete_async_patch_error(mock_tracer, mock_span):
    error = Exception("Async error")
    wrapped = AsyncMock(side_effect=error)
    decorator = mistral_complete_async_patch(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        await decorator(wrapped, None, (), {"model": "mistral-large-latest"})
    assert str(exc_info.value) == "Async error"
    mock_span.set_status.assert_called_once()
    status_call = mock_span.set_status.call_args[0][0]
    assert status_call.status_code == StatusCode.ERROR
    assert status_call.description == "Async error"
    mock_span.end.assert_called_once()


def test_mistral_stream_patch_success(mock_tracer, mock_span):
    from mistralai import (
        UsageInfo,
        DeltaMessage,
        CompletionChunk,
        CompletionEvent,
        CompletionResponseStreamChoice,
    )

    wrapped = Mock()

    delta_msg = DeltaMessage(content="partial")
    usage = UsageInfo(prompt_tokens=5, completion_tokens=5, total_tokens=10)
    choice = CompletionResponseStreamChoice(index=0, finish_reason=None, delta=delta_msg)
    chunk = CompletionChunk(id="test", model="mistral-large-latest", choices=[choice], usage=usage)
    event = CompletionEvent(data=chunk)

    def stream_gen():
        yield event

    wrapped.return_value = stream_gen()

    decorator = mistral_stream_patch(mock_tracer)
    result = decorator(wrapped, None, (), {"model": "mistral-large-latest"})
    assert hasattr(result, "__iter__")
    chunks = list(result)
    assert chunks == [event]
    # Check that start_as_current_span was called
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.end.assert_called_once()


@pytest.mark.asyncio
async def test_mistral_stream_async_patch_success(mock_tracer, mock_span):
    from mistralai import (
        UsageInfo,
        DeltaMessage,
        CompletionChunk,
        CompletionEvent,
        CompletionResponseStreamChoice,
    )

    wrapped = AsyncMock()

    delta_msg = DeltaMessage(content="async_partial")
    usage = UsageInfo(prompt_tokens=5, completion_tokens=5, total_tokens=10)
    choice = CompletionResponseStreamChoice(index=0, finish_reason=None, delta=delta_msg)
    chunk = CompletionChunk(id="test_async", model="mistral-large-latest", choices=[choice], usage=usage)
    event = CompletionEvent(data=chunk)

    async def async_stream_gen():
        yield event

    wrapped.return_value = async_stream_gen()

    decorator = mistral_stream_async_patch(mock_tracer)
    result = await decorator(wrapped, None, (), {"model": "mistral-large-latest"})
    assert hasattr(result, "__aiter__")

    collected = []
    async for c in result:
        collected.append(c)
    assert collected == [event]

    # Check that start_as_current_span was called
    mock_tracer.start_as_current_span.assert_called_once()
    mock_span.end.assert_called_once()
