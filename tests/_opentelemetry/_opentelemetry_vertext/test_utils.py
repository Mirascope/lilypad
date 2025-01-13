"""Tests for Google Generative AI OpenTelemetry utilities."""

from unittest.mock import Mock, PropertyMock

import pytest
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad._opentelemetry._opentelemetry_google_generative_ai.utils import (
    get_candidate_event,
    get_gemini_model_name,
    get_llm_request_attributes,
    set_content_event,
    set_response_attributes,
    set_stream,
    set_stream_async,
)


class MockPart:
    """Mock class for Gemini content parts"""

    def __init__(self, text: str):
        self.text = text
        self.function_call = None


class MockContent:
    """Mock class for Gemini content"""

    def __init__(self, role: str, text: str):
        self.role = role
        part = MockPart(text)
        self.parts = [part]


class MockCandidate:
    """Mock class for Gemini candidates"""

    def __init__(self, index: int, content: MockContent, finish_reason: int = 1):
        self.index = index
        self.content = content
        self.finish_reason = finish_reason


@pytest.fixture
def mock_client():
    """Create a mock client with proper model ID property"""
    client = Mock()
    # Configure _model_id as a property correctly
    PropertyMock(return_value="gemini-pro")
    type(client).__getattr__ = Mock(return_value="gemini-pro")
    return client


@pytest.fixture
def mock_candidate():
    content = MockContent("assistant", "test response")
    return MockCandidate(0, content, 1)  # Use integer for finish_reason


@pytest.fixture
def mock_chunk(mock_candidate):
    chunk = Mock()
    chunk.model = "gemini-pro"
    chunk.candidates = [mock_candidate]
    chunk.usage_metadata = Mock(prompt_token_count=10, candidates_token_count=20)
    return chunk


def test_get_llm_request_attributes(mock_client):
    kwargs = {"temperature": 0.7, "max_output_tokens": 100, "top_p": 0.9, "top_k": 40}

    attrs = get_llm_request_attributes(kwargs, mock_client)
    assert attrs[gen_ai_attributes.GEN_AI_SYSTEM] == "gemini"
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_MODEL] == "gemini-pro"
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] == 0.7
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] == 100
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] == 0.9
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TOP_K] == 40


def test_get_gemini_model_name():
    # Test with model_id
    client = Mock()

    # Configure direct returns instead of nested Mocks
    def get_attr(name):
        values = {"_model_id": "gemini-pro", "_model_name": "gemini-pro"}
        return values.get(name)

    type(client).__getattr__ = Mock(side_effect=get_attr)
    assert get_gemini_model_name(client) == "gemini-pro"

    # Test with model_name fallback
    client = Mock()

    # First request for _model_id returns None, then _model_name returns the value
    def get_attr_fallback(name):
        values = {"_model_id": None, "_model_name": "gemini-pro"}
        return values.get(name)

    type(client).__getattr__ = Mock(side_effect=get_attr_fallback)
    assert get_gemini_model_name(client) == "gemini-pro"

    # Test unknown case
    client = Mock(spec=[])
    assert get_gemini_model_name(client) == "unknown"


def test_get_candidate_event(mock_candidate):
    event_attrs = get_candidate_event(mock_candidate)
    assert event_attrs[gen_ai_attributes.GEN_AI_SYSTEM] == "gemini"
    assert event_attrs["index"] == 0
    assert event_attrs["finish_reason"] == 1
    assert "message" in event_attrs


def test_set_content_event():
    span = Mock()

    # Test simple text content
    content = {"role": "user", "parts": ["Hello"]}
    set_content_event(span, content)
    span.add_event.assert_called_once()

    # Test binary content
    span = Mock()
    binary_data = b"test data"
    content = {
        "role": "user",
        "parts": [{"mime_type": "image/jpeg", "data": binary_data}],
    }
    set_content_event(span, content)
    span.add_event.assert_called_once()


def test_set_response_attributes(mock_chunk, mock_client):
    span = Mock()
    set_response_attributes(span, mock_chunk, mock_client)
    assert span.set_attributes.called
    assert span.add_event.called


@pytest.mark.asyncio
async def test_set_stream_async(mock_chunk, mock_client):
    span = Mock()
    stream = [mock_chunk]

    async def async_iterator():
        for chunk in stream:
            yield chunk

    await set_stream_async(span, async_iterator(), mock_client)
    assert span.set_attributes.called
    assert span.add_event.called


def test_set_stream(mock_chunk, mock_client):
    span = Mock()
    stream = [mock_chunk]

    set_stream(span, stream, mock_client)
    assert span.set_attributes.called
    assert span.add_event.called
