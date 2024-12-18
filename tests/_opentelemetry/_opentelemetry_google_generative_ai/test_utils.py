"""Tests for Vertex AI OpenTelemetry utils."""

from unittest.mock import Mock

import pytest

from lilypad._opentelemetry._opentelemetry_vertex.utils import (
    get_vertex_llm_request_attributes,
    set_vertex_response_attributes,
    set_vertex_stream,
    set_vertex_stream_async,
)


class MockGenerativeModel:
    def __init__(self, model_name="gemini-pro"):
        self._model_name = model_name


class MockResponse:
    def __init__(self, candidates=None, usage_metadata=None):
        self.candidates = candidates or []
        self.usage_metadata = usage_metadata


class MockCandidate:
    def __init__(self, index=0, finish_reason=1, content=None):
        self.index = index
        self.finish_reason = finish_reason
        self.content = content
        self.function_calls = []


class MockContent:
    def __init__(self, role="assistant", parts=None):
        self.role = role
        self.parts = parts or []


class MockPart:
    def __init__(self, text=None):
        self.text = text


@pytest.fixture
def mock_span():
    span = Mock()
    span.is_recording.return_value = True
    return span


def test_get_vertex_llm_request_attributes():
    instance = MockGenerativeModel()
    kwargs = {
        "stream": True,
        "generation_config": Mock(
            _raw_generation_config=Mock(
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                max_output_tokens=100,
                frequency_penalty=0.5,
                presence_penalty=0.1,
                stop_sequences=["STOP"],
            )
        ),
    }
    attrs = get_vertex_llm_request_attributes(kwargs, instance)
    assert attrs["gen_ai.request.model"] == "gemini-pro"
    assert attrs["vertex.stream"] is True
    assert attrs["gen_ai.request.temperature"] == 0.7
    assert attrs["gen_ai.request.top_p"] == 0.9
    assert attrs["gen_ai.request.top_k"] == 40
    assert attrs["gen_ai.request.max_tokens"] == 100
    assert attrs["gen_ai.request.frequency_penalty"] == 0.5
    assert attrs["gen_ai.request.presence_penalty"] == 0.1
    assert attrs["gen_ai.request.stop_sequences"] == ["STOP"]


def test_set_vertex_response_attributes(mock_span):
    candidate = MockCandidate(
        index=0,
        finish_reason=1,
        content=MockContent(role="assistant", parts=[MockPart(text="Hello!")]),
    )
    response = MockResponse(candidates=[candidate])
    instance = MockGenerativeModel()
    set_vertex_response_attributes(mock_span, response, instance)
    mock_span.set_attributes.assert_called_once()
    mock_span.add_event.assert_called_once()
    event_call = mock_span.add_event.call_args[0][0]
    assert event_call == "gen_ai.choice"


def test_set_vertex_stream(mock_span):
    candidate = MockCandidate(
        index=0,
        finish_reason=1,
        content=MockContent(role="assistant", parts=[MockPart(text="Hello!")]),
    )
    chunk = MockResponse(candidates=[candidate])
    stream = [chunk]
    instance = MockGenerativeModel()
    set_vertex_stream(mock_span, stream, instance)
    mock_span.set_attributes.assert_called_once()
    mock_span.add_event.assert_called_once()


@pytest.mark.asyncio
async def test_set_vertex_stream_async(mock_span):
    candidate = MockCandidate(
        index=0,
        finish_reason=1,
        content=MockContent(role="assistant", parts=[MockPart(text="Hello!")]),
    )
    chunk = MockResponse(candidates=[candidate])

    async def async_gen():
        yield chunk

    instance = MockGenerativeModel()
    await set_vertex_stream_async(mock_span, async_gen(), instance)
    mock_span.set_attributes.assert_called_once()
    mock_span.add_event.assert_called_once()
