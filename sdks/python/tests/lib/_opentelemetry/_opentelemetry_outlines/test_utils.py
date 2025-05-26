"""Tests for Outlines OpenTelemetry utilities."""

import json
from unittest.mock import Mock

import pytest
from pydantic import BaseModel
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad.lib._opentelemetry._opentelemetry_outlines.utils import (
    record_prompts,
    set_choice_event,
    record_stop_sequences,
    extract_generation_attributes,
)


@pytest.fixture
def mock_span():
    span = Mock()
    span.is_recording.return_value = True
    return span


def test_record_prompts_single(mock_span):
    record_prompts(mock_span, "hello")
    mock_span.add_event.assert_called_with("gen_ai.user.message", attributes={"content": "hello"})


def test_record_prompts_list(mock_span):
    mock_span.reset_mock()
    record_prompts(mock_span, ["hi", "there"])
    calls = mock_span.add_event.call_args_list
    assert len(calls) == 2
    assert calls[0][0][0] == "gen_ai.user.message"
    assert calls[0][1]["attributes"]["content"] == "hi"
    assert calls[1][0][0] == "gen_ai.user.message"
    assert calls[1][1]["attributes"]["content"] == "there"


def test_record_stop_sequences(mock_span):
    record_stop_sequences(mock_span, ["STOP", "END"])
    mock_span.set_attribute.assert_called_once()
    args, kwargs = mock_span.set_attribute.call_args
    assert args[0] == "outlines.request.stop_sequences"
    assert json.loads(args[1]) == ["STOP", "END"]


def test_set_response_event(mock_span):
    set_choice_event(mock_span, "some response")
    mock_span.add_event.assert_called_with(
        "gen_ai.choice",
        attributes={
            "role": "assistant",
            "index": 0,
            "finish_reason": "none",
            "message": "some response",
        },
    )

    class Response(BaseModel):
        genre: str
        author: str

    model_response = Response(genre="fantasy", author="John")
    set_choice_event(mock_span, model_response)
    mock_span.add_event.assert_called_with(
        "gen_ai.choice",
        attributes={
            "role": "assistant",
            "index": 0,
            "finish_reason": "none",
            "message": '{"genre":"fantasy","author":"John"}',
        },
    )


def test_extract_generation_attributes():
    generation_parameters = Mock(max_tokens=100, stop_at="STOP", seed=42)
    sampling_parameters = Mock(sampler="multinomial", num_samples=1, top_p=0.9, top_k=None, temperature=0.5)
    attrs = extract_generation_attributes(generation_parameters, sampling_parameters, "test-model")

    assert attrs[gen_ai_attributes.GEN_AI_SYSTEM] == "outlines"
    assert attrs[gen_ai_attributes.GEN_AI_OPERATION_NAME] == "generate"
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_MODEL] == "test-model"
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] == 100
    assert attrs["outlines.request.seed"] == 42
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] == 0.9
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] == 0.5


def test_extract_generation_attributes_no_params():
    attrs = extract_generation_attributes(None, None, "model")
    assert attrs[gen_ai_attributes.GEN_AI_SYSTEM] == "outlines"
    assert attrs[gen_ai_attributes.GEN_AI_OPERATION_NAME] == "generate"
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_MODEL] == "model"
    assert len(attrs) == 3
