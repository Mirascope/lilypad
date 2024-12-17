"""Tests for Bedrock OpenTelemetry utilities."""

from unittest.mock import Mock

import pytest
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad._opentelemetry._opentelemetry_bedrock.utils import (
    get_bedrock_llm_request_attributes,
    set_bedrock_response_attributes,
)


@pytest.fixture
def mock_span():
    span = Mock()
    span.is_recording.return_value = True
    return span


def test_get_bedrock_llm_request_attributes():
    kwargs = {
        "modelId": "anthropic.claude-3-haiku-20240307-v1:0",
        "inferenceConfig": {
            "maxTokens": 1024,
            "temperature": 0.7,
            "topP": 0.9,
            "stopSequences": ["STOP"],
        },
    }
    attrs = get_bedrock_llm_request_attributes(kwargs)
    assert attrs["gen_ai.request.model"] == "anthropic.claude-3-haiku-20240307-v1:0"
    assert attrs["gen_ai.request.temperature"] == 0.7
    assert attrs["gen_ai.request.top_p"] == 0.9
    assert attrs["gen_ai.request.max_tokens"] == 1024
    assert attrs["gen_ai.request.stop_sequences"] == ["STOP"]


def test_set_bedrock_response_attributes(mock_span):
    response = {
        "output": {"message": {"content": [{"text": "Recommended: The Hobbit"}]}},
        "stopReason": "stop",
        "usage": {"inputTokens": 10, "outputTokens": 20},
    }
    set_bedrock_response_attributes(mock_span, response)
    mock_span.set_attributes.assert_called_once()
    mock_span.add_event.assert_called_once()
    event_call = mock_span.add_event.call_args[0][0]
    assert event_call == "gen_ai.choice"
    # Check that attributes for usage and finish reasons are set
    set_attrs_call = mock_span.set_attributes.call_args[0][0]
    assert set_attrs_call[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] == 10
    assert set_attrs_call[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] == 20
    assert set_attrs_call[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] == ["stop"]
