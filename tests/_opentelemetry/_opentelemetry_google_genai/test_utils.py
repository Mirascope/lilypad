from unittest.mock import Mock

import pytest
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad._opentelemetry._opentelemetry_google_genai.utils import (
    get_llm_request_attributes,
    set_content_event,
    set_response_attributes,
    set_stream,
    set_stream_async,
)


class DummyCandidate:
    def __init__(self, index, finish_reason):
        self.index = index
        self.finish_reason = finish_reason


class DummyChunk:
    def __init__(self, candidates):
        self.candidates = candidates


@pytest.fixture
def instance():
    obj = Mock()
    obj._model_name = "google-genai-model"
    return obj


def test_get_llm_request_attributes(instance):
    kwargs = {
        "config": {
            "temperature": 0.8,
            "top_p": 0.95,
            "top_k": 50,
            "max_output_tokens": 200,
        },
        "stream": True,
    }
    attrs = get_llm_request_attributes(kwargs, instance)
    assert attrs[gen_ai_attributes.GEN_AI_OPERATION_NAME] == "generate_content"
    assert attrs[gen_ai_attributes.GEN_AI_SYSTEM] == "google_genai"
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_MODEL] == "google-genai-model"
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] == 0.8
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] == 0.95
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TOP_K] == 50
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] == 200
    assert attrs["google_genai.stream"] is True


def test_set_content_event():
    span = Mock()
    content = {"role": "user", "parts": ["Test message"]}
    set_content_event(span, content)
    span.add_event.assert_called_once_with(
        "gen_ai.content", attributes={"content": str(content)}
    )


def test_set_response_attributes(instance):
    span = Mock()
    candidate1 = DummyCandidate(0, "completed")
    candidate2 = DummyCandidate(1, "completed")
    response = Mock()
    response.candidates = [candidate1, candidate2]
    set_response_attributes(span, response, instance)
    assert span.add_event.call_count == 2
    span.set_attributes.assert_called_once()
    attrs = span.set_attributes.call_args[0][0]
    assert attrs[gen_ai_attributes.GEN_AI_RESPONSE_MODEL] == "google-genai-model"
    assert gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS in attrs
    assert attrs[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] == [
        "completed",
        "completed",
    ]


def test_set_stream():
    span = Mock()
    candidate = DummyCandidate(0, "completed")
    chunk1 = DummyChunk([candidate])
    chunk2 = DummyChunk([candidate])
    stream = [chunk1, chunk2]
    instance = Mock()
    instance._model_name = "google-genai-model"
    set_stream(span, stream, instance)
    span.set_attributes.assert_called_once()
    assert span.add_event.call_count >= 2


@pytest.mark.asyncio
async def test_set_stream_async():
    span = Mock()
    candidate = DummyCandidate(0, "completed")
    chunk = DummyChunk([candidate])

    async def async_stream():
        yield chunk
        yield chunk

    instance = Mock()
    instance._model_name = "google-genai-model"
    await set_stream_async(span, async_stream(), instance)
    span.set_attributes.assert_called_once()
    assert span.add_event.call_count >= 2
