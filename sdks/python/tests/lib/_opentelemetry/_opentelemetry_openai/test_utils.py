"""Tests for OpenAI OpenTelemetry utilities."""

import json
from unittest.mock import Mock

import pytest
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageToolCall
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from openai.types.chat.chat_completion_message_tool_call import Function

from lilypad.lib._opentelemetry._opentelemetry_openai.utils import (
    OpenAIMetadata,
    OpenAIChunkHandler,
    get_tool_calls,
    get_choice_event,
    set_message_event,
    default_openai_cleanup,
    set_response_attributes,
)


@pytest.fixture
def mock_chunk():
    chunk = Mock()
    chunk.model = "gpt-4"
    chunk.id = "test-id"
    chunk.service_tier = "standard"

    choice = Mock()
    choice.index = 0
    choice.delta = Mock()
    choice.delta.content = "test response"
    choice.delta.tool_calls = None
    choice.finish_reason = "stop"

    chunk.choices = [choice]
    chunk.usage = Mock(completion_tokens=20, prompt_tokens=10)
    return chunk


class DictLikeMock:
    """A mock that behaves like a dict but has attribute access."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)


def test_openai_metadata():
    metadata = OpenAIMetadata()
    assert metadata.get("response_id") is None
    assert metadata.get("response_model") is None
    assert metadata.get("service_tier") is None
    assert metadata.get("finish_reasons", []) == []
    assert metadata.get("prompt_tokens") is None
    assert metadata.get("completion_tokens") is None


def test_openai_chunk_handler(mock_chunk):
    handler = OpenAIChunkHandler()
    metadata = OpenAIMetadata()
    buffers = []

    handler.extract_metadata(mock_chunk, metadata)
    assert metadata["response_model"] == "gpt-4"  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["response_id"] == "test-id"  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["service_tier"] == "standard"  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["completion_tokens"] == 20  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["prompt_tokens"] == 10  # pyright: ignore [reportTypedDictNotRequiredAccess]

    handler.process_chunk(mock_chunk, buffers)
    assert len(buffers) == 1
    assert buffers[0].text_content == ["test response"]


def test_get_tool_calls():
    # Create a mock that behaves like a dict with attribute access
    message = {
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {"name": "test_function", "arguments": '{"arg": "value"}'},
            }
        ]
    }
    tool_calls = get_tool_calls(message)
    assert len(tool_calls) == 1  # pyright: ignore [reportArgumentType]
    assert tool_calls[0]["id"] == "call_123"  # pyright: ignore [reportOptionalSubscript]
    assert tool_calls[0]["type"] == "function"  # pyright: ignore [reportOptionalSubscript]
    assert tool_calls[0]["function"]["name"] == "test_function"  # pyright: ignore [reportOptionalSubscript]
    message = ChatCompletionMessage(
        role="assistant",
        content=None,
        tool_calls=[
            ChatCompletionMessageToolCall(
                id="call_123",
                type="function",
                function=Function(name="test_function", arguments='{"arg": "value"}'),
            )
        ],
    )
    tool_calls = get_tool_calls(message)
    assert len(tool_calls) == 1  # pyright: ignore [reportArgumentType]
    assert tool_calls[0]["id"] == "call_123"  # pyright: ignore [reportOptionalSubscript]
    assert tool_calls[0]["type"] == "function"  # pyright: ignore [reportOptionalSubscript]
    assert tool_calls[0]["function"]["name"] == "test_function"  # pyright: ignore [reportOptionalSubscript]

    # Test without tool calls
    message = {"tool_calls": None}
    assert get_tool_calls(message) is None


def test_set_message_event():
    span = Mock()
    # Test user message
    message = {"role": "user", "content": "Hello"}
    set_message_event(span, message)
    span.add_event.assert_called_with(
        "gen_ai.user.message",
        attributes={gen_ai_attributes.GEN_AI_SYSTEM: "openai", "content": "Hello"},
    )


def test_get_choice_event():
    # Create a mock with proper attribute structure
    message = DictLikeMock(role="assistant", content="Hello", tool_calls=None)

    choice = DictLikeMock(message=message, index=0, finish_reason="stop")

    event_attrs = get_choice_event(choice)
    assert event_attrs[gen_ai_attributes.GEN_AI_SYSTEM] == "openai"
    assert event_attrs["index"] == 0
    assert event_attrs["finish_reason"] == "stop"
    assert json.loads(event_attrs["message"])["role"] == "assistant"  # pyright: ignore [reportArgumentType]
    assert json.loads(event_attrs["message"])["content"] == "Hello"  # pyright: ignore [reportArgumentType]


def test_set_response_attributes():
    span = Mock()
    # Create response with proper message structure
    message = DictLikeMock(role="assistant", content="Hello", tool_calls=None)

    choice = DictLikeMock(message=message, index=0, finish_reason="stop")

    response = DictLikeMock(
        model="gpt-4",
        choices=[choice],
        id="test-id",
        usage=DictLikeMock(prompt_tokens=10, completion_tokens=20),
        service_tier="standard",
    )

    set_response_attributes(span, response)
    assert span.set_attributes.called
    assert span.add_event.called


def test_default_openai_cleanup(mock_chunk):
    span = Mock()
    metadata = OpenAIMetadata(
        response_model="gpt-4",
        response_id="test-id",
        service_tier="standard",
        prompt_tokens=10,
        completion_tokens=20,
        finish_reasons=["stop"],
    )
    buffers = []
    handler = OpenAIChunkHandler()
    handler.process_chunk(mock_chunk, buffers)

    default_openai_cleanup(span, metadata, buffers)

    assert span.set_attributes.called
    assert span.add_event.called
