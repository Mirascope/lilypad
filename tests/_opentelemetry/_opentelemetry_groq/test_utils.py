"""Tests for Groq OpenTelemetry utilities."""

import json
from unittest.mock import Mock

import pytest
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad._opentelemetry._opentelemetry_groq.utils import (
    GroqChunkHandler,
    GroqMetadata,
    default_groq_cleanup,
    get_choice_event,
    set_message_event,
    set_response_attributes,
)


@pytest.fixture
def mock_chunk():
    chunk = Mock()
    chunk.model = "mixtral-8x7b-32768"
    chunk.id = "test-id"

    choice = Mock()
    choice.index = 0
    choice.delta = Mock()
    choice.delta.content = "test response"
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


def test_groq_metadata():
    metadata = GroqMetadata()
    assert metadata.get("response_id") is None
    assert metadata.get("response_model") is None
    assert metadata.get("finish_reasons", []) == []
    assert metadata.get("prompt_tokens") is None
    assert metadata.get("completion_tokens") is None


def test_groq_chunk_handler(mock_chunk):
    handler = GroqChunkHandler()
    metadata = GroqMetadata()
    buffers = []

    handler.extract_metadata(mock_chunk, metadata)
    assert metadata["response_model"] == "mixtral-8x7b-32768"  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["response_id"] == "test-id"  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["completion_tokens"] == 20  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["prompt_tokens"] == 10  # pyright: ignore [reportTypedDictNotRequiredAccess]

    handler.process_chunk(mock_chunk, buffers)
    assert len(buffers) == 1
    assert buffers[0].text_content == ["test response"]


def test_set_message_event():
    span = Mock()
    # Test user message
    message = {"role": "user", "content": "Hello"}
    set_message_event(span, message)
    span.add_event.assert_called_with(
        "gen_ai.user.message",
        attributes={gen_ai_attributes.GEN_AI_SYSTEM: "groq", "content": "Hello"},
    )


def test_get_choice_event():
    message = DictLikeMock(role="assistant", content="Hello")
    choice = DictLikeMock(message=message, index=0, finish_reason="stop")

    event_attrs = get_choice_event(choice)
    assert event_attrs[gen_ai_attributes.GEN_AI_SYSTEM] == "groq"
    assert event_attrs["index"] == 0
    assert event_attrs["finish_reason"] == "stop"
    assert json.loads(event_attrs["message"])["role"] == "assistant"  # pyright: ignore [reportArgumentType]
    assert json.loads(event_attrs["message"])["content"] == "Hello"  # pyright: ignore [reportArgumentType]


def test_set_response_attributes():
    span = Mock()
    message = DictLikeMock(role="assistant", content="Hello")
    choice = DictLikeMock(message=message, index=0, finish_reason="stop")

    response = DictLikeMock(
        model="mixtral-8x7b-32768",
        choices=[choice],
        id="test-id",
        usage=DictLikeMock(prompt_tokens=10, completion_tokens=20),
    )

    set_response_attributes(span, response)
    assert span.set_attributes.called
    assert span.add_event.called


def test_default_groq_cleanup(mock_chunk):
    span = Mock()
    metadata = GroqMetadata(
        response_model="mixtral-8x7b-32768",
        response_id="test-id",
        prompt_tokens=10,
        completion_tokens=20,
        finish_reasons=["stop"],
    )
    buffers = []
    handler = GroqChunkHandler()
    handler.process_chunk(mock_chunk, buffers)

    default_groq_cleanup(span, metadata, buffers)

    assert span.set_attributes.called
    assert span.add_event.called


def test_groq_chunk_handler_streaming():
    handler = GroqChunkHandler()
    metadata = GroqMetadata()
    buffers = []

    # Test streaming chunk with content
    chunk = Mock()
    chunk.model = "mixtral-8x7b-32768"
    chunk.id = "test-id"
    chunk.choices = [Mock(index=0, delta=Mock(content="Hello"), finish_reason=None)]

    handler.process_chunk(chunk, buffers)
    assert len(buffers) == 1
    assert buffers[0].text_content == ["Hello"]

    # Test streaming chunk with finish reason
    chunk.choices[0].finish_reason = "stop"
    handler.extract_metadata(chunk, metadata)
    assert "stop" in metadata["finish_reasons"]  # pyright: ignore [reportTypedDictNotRequiredAccess]
