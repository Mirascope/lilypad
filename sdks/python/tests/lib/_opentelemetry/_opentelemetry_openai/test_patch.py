"""Tests for OpenAI OpenTelemetry patching with updated response_format logic."""

from contextlib import contextmanager
from unittest.mock import Mock, AsyncMock

import pytest
from opentelemetry.trace import StatusCode
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad.lib._opentelemetry._opentelemetry_openai.patch import (
    chat_completions_parse,
    chat_completions_create,
    chat_completions_parse_async,
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

    decorator = chat_completions_create(mock_tracer)
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

    decorator = chat_completions_create(mock_tracer)
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

    decorator = chat_completions_create(mock_tracer)

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

    decorator = chat_completions_create_async(mock_tracer)
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

    decorator = chat_completions_create_async(mock_tracer)
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

    decorator = chat_completions_create_async(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        await decorator(wrapped, instance, (), kwargs)

    assert str(exc_info.value) == str(error)
    # Compare status code and description instead of Status object directly
    called_status = mock_span.set_status.call_args[0][0]
    assert called_status.status_code == StatusCode.ERROR
    assert called_status.description == str(error)


def test_chat_completions_parse(mock_tracer, mock_response):
    wrapped = Mock()
    wrapped.return_value = mock_response
    instance = Mock()
    kwargs = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}],
        "response_format": {"type": "json_object"},
    }

    decorator = chat_completions_parse(mock_tracer)
    result = decorator(wrapped, instance, (), kwargs)

    assert result is mock_response
    mock_tracer.start_as_current_span.assert_called_once()
    attributes = mock_tracer.start_as_current_span.call_args[1]["attributes"]
    assert attributes[gen_ai_attributes.GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT] == "json_object"


def test_chat_completions_parse_error(mock_tracer, mock_span):
    error = Exception("Test error")
    wrapped = Mock(side_effect=error)
    instance = Mock()
    kwargs = {
        "model": "gpt-4",
    }

    decorator = chat_completions_parse(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        decorator(wrapped, instance, (), kwargs)
    assert exc_info.value is error

    called_status = mock_span.set_status.call_args[0][0]
    assert called_status.status_code == StatusCode.ERROR
    assert called_status.description == str(error)


def test_chat_completions_parse_response_format_class(mock_tracer, mock_response):
    class ParseDummyFormat:
        pass

    wrapped = Mock()
    wrapped.return_value = mock_response
    instance = Mock()
    kwargs = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}],
        "response_format": ParseDummyFormat,
    }

    decorator = chat_completions_parse(mock_tracer)
    result = decorator(wrapped, instance, (), kwargs)

    assert result is mock_response
    mock_tracer.start_as_current_span.assert_called_once()
    attributes = mock_tracer.start_as_current_span.call_args[1]["attributes"]
    assert attributes[gen_ai_attributes.GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT] == "ParseDummyFormat"


@pytest.mark.asyncio
async def test_chat_completions_parse_async(mock_tracer, mock_response):
    wrapped = AsyncMock()
    wrapped.return_value = mock_response
    instance = Mock()
    kwargs = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}],
        "response_format": {"type": "json_object"},
    }

    decorator = chat_completions_parse_async(mock_tracer)
    result = await decorator(wrapped, instance, (), kwargs)

    assert result is mock_response
    mock_tracer.start_as_current_span.assert_called_once()
    attributes = mock_tracer.start_as_current_span.call_args[1]["attributes"]
    assert attributes[gen_ai_attributes.GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT] == "json_object"


@pytest.mark.asyncio
async def test_chat_completions_parse_async_error(mock_tracer, mock_span):
    error = Exception("Test error")
    wrapped = AsyncMock(side_effect=error)
    instance = Mock()
    kwargs = {
        "model": "gpt-4",
    }

    decorator = chat_completions_parse_async(mock_tracer)

    with pytest.raises(Exception) as exc_info:
        await decorator(wrapped, instance, (), kwargs)
    assert str(exc_info.value) == str(error)

    called_status = mock_span.set_status.call_args[0][0]
    assert called_status.status_code == StatusCode.ERROR
    assert called_status.description == str(error)


@pytest.mark.asyncio
async def test_chat_completions_parse_async_response_format_class(mock_tracer, mock_response):
    class AsyncParseDummyFormat:
        pass

    wrapped = AsyncMock()
    wrapped.return_value = mock_response
    instance = Mock()
    kwargs = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}],
        "response_format": AsyncParseDummyFormat,
    }

    decorator = chat_completions_parse_async(mock_tracer)
    result = await decorator(wrapped, instance, (), kwargs)

    assert result is mock_response
    mock_tracer.start_as_current_span.assert_called_once()
    attributes = mock_tracer.start_as_current_span.call_args[1]["attributes"]
    assert attributes[gen_ai_attributes.GEN_AI_OPENAI_REQUEST_RESPONSE_FORMAT] == "AsyncParseDummyFormat"
