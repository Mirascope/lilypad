"""Tests for Anthropic OpenTelemetry utilities."""

import json
from unittest.mock import Mock

import pytest
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad.lib._opentelemetry._opentelemetry_anthropic.utils import (
    AnthropicMetadata,
    AnthropicChunkHandler,
    get_message_event,
    set_message_event,
    set_response_attributes,
    default_anthropic_cleanup,
    get_llm_request_attributes,
)


class DictLikeMock:
    """A mock that behaves like a dict but has attribute access."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)


@pytest.fixture
def mock_chunk():
    chunk = Mock()
    chunk.model = "claude-3-opus-20240229"
    chunk.id = "msg_123"
    chunk.type = "content_block_delta"

    chunk.delta = Mock()
    chunk.delta.type = "text_delta"
    chunk.delta.text = "test response"
    chunk.index = 0
    chunk.stop_reason = "stop"

    chunk.usage = Mock(input_tokens=10, output_tokens=20)
    return chunk


def test_anthropic_metadata():
    metadata = AnthropicMetadata()
    assert metadata.get("message_id") is None
    assert metadata.get("model") is None
    assert metadata.get("input_tokens") is None
    assert metadata.get("output_tokens") is None
    assert metadata.get("stop_reason") is None


def test_anthropic_chunk_handler(mock_chunk):
    handler = AnthropicChunkHandler()
    metadata = AnthropicMetadata()
    buffers = []

    # Test metadata extraction
    handler.extract_metadata(mock_chunk, metadata)
    assert metadata["model"] == "claude-3-opus-20240229"  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["message_id"] == "msg_123"  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["stop_reason"] == "stop"  # pyright: ignore [reportTypedDictNotRequiredAccess]

    # Test chunk processing
    handler.process_chunk(mock_chunk, buffers)
    assert len(buffers) == 1
    assert buffers[0].text_content == ["test response"]


def test_get_tool_call():
    content = DictLikeMock(type="tool_use", id="call_123", name="test_function", input={"arg": "value"})

    # Initialize tool_call_dict with function key
    tool_call_dict = {
        "id": content.id,  # pyright: ignore [reportAttributeAccessIssue]
        "type": content.type,  # pyright: ignore [reportAttributeAccessIssue]
        "function": {"name": content.name, "arguments": content.input},  # pyright: ignore [reportAttributeAccessIssue]
    }

    assert tool_call_dict["id"] == "call_123"
    assert tool_call_dict["type"] == "tool_use"
    assert tool_call_dict["function"]["name"] == "test_function"
    assert tool_call_dict["function"]["arguments"] == {"arg": "value"}


def test_get_tool_calls():
    message = DictLikeMock(type="tool_use", id="call_123", name="test_function", input={"arg": "value"})

    messages = [message]
    tool_calls = []
    for msg in messages:
        if msg.type == "tool_use":  # pyright: ignore [reportAttributeAccessIssue]
            tool_call = {
                "id": msg.id,  # pyright: ignore [reportAttributeAccessIssue]
                "type": msg.type,  # pyright: ignore [reportAttributeAccessIssue]
                "function": {"name": msg.name, "arguments": msg.input},  # pyright: ignore [reportAttributeAccessIssue]
            }
            tool_calls.append(tool_call)

    assert len(tool_calls) == 1
    assert tool_calls[0]["id"] == "call_123"
    assert tool_calls[0]["type"] == "tool_use"
    assert tool_calls[0]["function"]["name"] == "test_function"
    assert tool_calls[0]["function"]["arguments"] == {"arg": "value"}


def test_set_message_event():
    span = Mock()
    message = {"role": "user", "content": [{"type": "text", "text": "Hello"}]}

    set_message_event(span, message)
    span.add_event.assert_called_with(
        "gen_ai.user.message",
        attributes={
            gen_ai_attributes.GEN_AI_SYSTEM: "anthropic",
            "content": '[{"type":"text","text":"Hello"}]',
        },
    )


def test_get_message_event():
    message = DictLikeMock(text="Hello", type="text")

    event_attrs = get_message_event(message)
    assert event_attrs[gen_ai_attributes.GEN_AI_SYSTEM] == "anthropic"
    assert "message" in event_attrs


def test_set_response_attributes():
    span = Mock()
    content = DictLikeMock(type="text", text="Hello")

    response = DictLikeMock(
        model="claude-3-opus-20240229",
        role="assistant",
        content=[content],
        stop_reason="stop",
        id="msg_123",
        usage=DictLikeMock(input_tokens=10, output_tokens=20),
    )

    set_response_attributes(span, response)
    assert span.set_attributes.called
    assert span.add_event.called


def test_default_anthropic_cleanup(mock_chunk):
    span = Mock()
    metadata = AnthropicMetadata(
        model="claude-3-opus-20240229",
        message_id="msg_123",
        stop_reason="stop",
        input_tokens=10,
        output_tokens=20,
    )
    buffers = []
    handler = AnthropicChunkHandler()
    handler.process_chunk(mock_chunk, buffers)

    default_anthropic_cleanup(span, metadata, buffers)

    assert span.set_attributes.called
    assert span.add_event.called


def test_llm_request_attributes():
    kwargs = {
        "model": "claude-3-opus-20240229",
        "temperature": 0.7,
        "max_tokens": 100,
        "top_p": 0.9,
        "top_k": 40,
        "stop_sequences": ["END"],
    }
    client_instance = Mock()

    attrs = get_llm_request_attributes(kwargs, client_instance)
    assert attrs[gen_ai_attributes.GEN_AI_SYSTEM] == "anthropic"
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_MODEL] == "claude-3-opus-20240229"
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] == 0.7
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] == 100
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] == 0.9
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TOP_K] == 40
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_STOP_SEQUENCES] == ["END"]
