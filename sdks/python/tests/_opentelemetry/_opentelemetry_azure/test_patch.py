"""Tests for Azure OpenTelemetry patching with updated response_format logic."""

from contextlib import contextmanager
from unittest.mock import Mock, AsyncMock

import pytest
from opentelemetry.trace import StatusCode
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad._opentelemetry._opentelemetry_azure.patch import (
    chat_completions_complete,
    chat_completions_complete_async,
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
    response.model = "gpt-4"
    response.id = "test-id"
    response.usage = Mock(prompt_tokens=10, completion_tokens=20)
    return response


def test_chat_completions_create(mock_tracer, mock_response):
    wrapped = Mock()
    wrapped.return_value = mock_response
    instance = Mock()
    kwargs = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False,
        "response_format": {"type": "json_object"},
    }

    decorator = chat_completions_complete(mock_tracer)
    result = decorator(wrapped, instance, (), kwargs)

    assert result is mock_response
    mock_tracer.start_as_current_span.assert_called_once()
    # Check attributes to ensure response_format got picked up correctly
    attributes = mock_tracer.start_as_current_span.call_args[1]["attributes"]
    # response_format should be "json_object"
    assert attributes[gen_ai_attributes.GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT] == "json_object"


def test_chat_completions_create_response_format_class(mock_tracer, mock_response):
    class DummyFormat:
        pass

    wrapped = Mock()
    wrapped.return_value = mock_response
    instance = Mock()
    kwargs = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False,
        "response_format": DummyFormat,  # class type
    }

    decorator = chat_completions_complete(mock_tracer)
    result = decorator(wrapped, instance, (), kwargs)

    assert result is mock_response
    mock_tracer.start_as_current_span.assert_called_once()
    attributes = mock_tracer.start_as_current_span.call_args[1]["attributes"]
    # response_format should be "DummyFormat" (class name)
    assert attributes[gen_ai_attributes.GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT] == "DummyFormat"


def test_chat_completions_create_error(mock_tracer, mock_span):
    error = Exception("Test error")
    wrapped = Mock(side_effect=error)
    instance = Mock()
    kwargs = {
        "model": "gpt-4",  # Add required model parameter
    }

    decorator = chat_completions_complete(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        decorator(wrapped, instance, (), kwargs)
    assert exc_info.value is error

    called_status = mock_span.set_status.call_args[0][0]
    assert called_status.status_code == StatusCode.ERROR
    assert called_status.description == str(error)


@pytest.mark.asyncio
async def test_chat_completions_create_async(mock_tracer, mock_response):
    wrapped = AsyncMock()
    wrapped.return_value = mock_response
    instance = Mock()
    kwargs = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False,
        "response_format": {"type": "json_object"},
    }

    decorator = chat_completions_complete_async(mock_tracer)
    result = await decorator(wrapped, instance, (), kwargs)

    assert result is mock_response
    mock_tracer.start_as_current_span.assert_called_once()
    attributes = mock_tracer.start_as_current_span.call_args[1]["attributes"]
    assert attributes[gen_ai_attributes.GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT] == "json_object"


@pytest.mark.asyncio
async def test_chat_completions_create_async_response_format_class(mock_tracer, mock_response):
    class AsyncDummyFormat:
        pass

    wrapped = AsyncMock()
    wrapped.return_value = mock_response
    instance = Mock()
    kwargs = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": False,
        "response_format": AsyncDummyFormat,
    }

    decorator = chat_completions_complete_async(mock_tracer)
    result = await decorator(wrapped, instance, (), kwargs)

    assert result is mock_response
    mock_tracer.start_as_current_span.assert_called_once()
    attributes = mock_tracer.start_as_current_span.call_args[1]["attributes"]
    assert attributes[gen_ai_attributes.GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT] == "AsyncDummyFormat"


@pytest.mark.asyncio
async def test_chat_completions_create_async_error(mock_tracer, mock_span):
    error = Exception("Test error")
    wrapped = AsyncMock(side_effect=error)
    instance = Mock()
    kwargs = {
        "model": "gpt-4",  # Add required model parameter
    }

    decorator = chat_completions_complete_async(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        await decorator(wrapped, instance, (), kwargs)

    assert str(exc_info.value) == str(error)
    # Compare status code and description instead of Status object directly
    called_status = mock_span.set_status.call_args[0][0]
    assert called_status.status_code == StatusCode.ERROR
    assert called_status.description == str(error)


def test_chat_completions_create_openrouter_system(mock_tracer, mock_response):
    """Test that openrouter system is detected correctly."""
    from lilypad._opentelemetry._opentelemetry_azure.patch import get_llm_request_attributes
    from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

    from httpx import URL

    wrapped = Mock()
    wrapped.return_value = mock_response
    instance = Mock()
    # Mock base URL to contain openrouter
    instance._client = Mock()
    # Create a real URL object for openrouter
    instance._client.base_url = URL("https://openrouter.ai")

    kwargs = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}],
    }

    # Get attributes to check openrouter system detection
    attributes = get_llm_request_attributes(kwargs, instance)

    # Check that openrouter is detected in the system attribute
    assert attributes[gen_ai_attributes.GEN_AI_SYSTEM] == "openrouter"


def test_chat_completions_create_streaming(mock_tracer, mock_response):
    """Test streaming response returns StreamWrapper."""
    from lilypad._opentelemetry._utils import StreamWrapper

    wrapped = Mock()
    wrapped.return_value = mock_response
    instance = Mock()
    kwargs = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True,  # Enable streaming
    }

    decorator = chat_completions_complete(mock_tracer)
    result = decorator(wrapped, instance, (), kwargs)

    # Verify StreamWrapper is returned for streaming
    assert isinstance(result, StreamWrapper)
    assert result.stream is mock_response
    mock_tracer.start_as_current_span.assert_called_once()


@pytest.mark.asyncio
async def test_chat_completions_create_async_streaming(mock_tracer, mock_response):
    """Test async streaming response returns AsyncStreamWrapper."""
    from lilypad._opentelemetry._utils import AsyncStreamWrapper

    wrapped = AsyncMock()
    wrapped.return_value = mock_response
    instance = Mock()
    # Mock async get_model_info
    instance.get_model_info = AsyncMock(return_value={"model_name": "gpt-4"})

    kwargs = {
        "messages": [{"role": "user", "content": "Hello"}],
        "stream": True,  # Enable streaming
    }

    decorator = chat_completions_complete_async(mock_tracer)
    result = await decorator(wrapped, instance, (), kwargs)

    # Verify AsyncStreamWrapper is returned for streaming
    assert isinstance(result, AsyncStreamWrapper)
    assert result.stream is mock_response
    mock_tracer.start_as_current_span.assert_called_once()
