import json
from enum import Enum
from unittest.mock import Mock

import pytest
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad.lib._opentelemetry._opentelemetry_google_genai.utils import (
    set_stream,
    set_stream_async,
    set_content_event,
    set_response_attributes,
    get_llm_request_attributes,
)


class FinishReason(Enum):
    STOP = "STOP"
    COMPLETED = "COMPLETED"
    TIMEOUT = "TIMEOUT"


class DummyCandidate:
    def __init__(self, index, finish_reason: FinishReason, content=None):
        self.index = index
        self.finish_reason = finish_reason
        self.content = content


class DummyChunk:
    def __init__(self, candidates):
        self.candidates = candidates


@pytest.fixture
def instance():
    obj = Mock()
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
        "model": "google-genai-model",
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
    expected_attributes = {
        "gen_ai.system": "google_genai",
        "content": json.dumps(["Test message"]),
    }
    span.add_event.assert_called_once_with("gen_ai.user.message", attributes=expected_attributes)


def test_set_response_attributes(instance):
    span = Mock()
    candidate1 = DummyCandidate(0, FinishReason.COMPLETED, content=None)
    candidate2 = DummyCandidate(1, FinishReason.COMPLETED, content=None)
    response = Mock(model_version="google-genai-model")
    response.candidates = [candidate1, candidate2]
    set_response_attributes(span, response)
    assert span.add_event.call_count == 2
    span.set_attributes.assert_called_once()
    attrs = span.set_attributes.call_args[0][0]
    assert attrs[gen_ai_attributes.GEN_AI_RESPONSE_MODEL] == "google-genai-model"
    assert gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS in attrs
    assert attrs[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] == [
        "COMPLETED",
        "COMPLETED",
    ]


def test_set_stream():
    span = Mock()
    candidate = DummyCandidate(0, FinishReason.COMPLETED, content=None)
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
    candidate = DummyCandidate(0, FinishReason.COMPLETED, content=None)
    chunk = DummyChunk([candidate])

    async def async_stream():
        yield chunk
        yield chunk

    instance = Mock()
    instance._model_name = "google-genai-model"
    await set_stream_async(span, async_stream(), instance)
    span.set_attributes.assert_called()
    assert span.add_event.call_count >= 2
