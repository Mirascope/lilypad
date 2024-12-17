"""Tests for Mistral OpenTelemetry utilities."""

from unittest.mock import Mock

import pytest
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad._opentelemetry._opentelemetry_mistral.utils import (
    get_mistral_llm_request_attributes,
    set_mistral_response_attributes,
)


@pytest.fixture
def mock_span():
    span = Mock()
    span.is_recording.return_value = True
    return span


def test_get_mistral_llm_request_attributes():
    kwargs = {
        "model": "mistral-large-latest",
        "messages": [{"role": "user", "content": "Hello"}],
        "temperature": 0.7,
        "top_p": 0.9,
        "max_tokens": 1024,
        "stop": "STOP",
    }
    attrs = get_mistral_llm_request_attributes(kwargs)
    assert attrs["gen_ai.request.model"] == "mistral-large-latest"
    assert attrs["gen_ai.request.temperature"] == 0.7
    assert attrs["gen_ai.request.top_p"] == 0.9
    assert attrs["gen_ai.request.max_tokens"] == 1024
    assert attrs["gen_ai.request.stop_sequences"] == ["STOP"]


def test_set_mistral_response_attributes(mock_span):
    # Mock response object similar to ChatCompletionResponse
    response = Mock()
    response.model = "mistral-large-latest"
    usage = Mock()
    usage.prompt_tokens = 10
    usage.completion_tokens = 20
    response.usage = usage

    choice = Mock()
    choice.message = Mock(content="Recommended: The Hobbit")
    choice.finish_reason = "stop"
    response.choices = [choice]

    set_mistral_response_attributes(mock_span, response)
    mock_span.set_attributes.assert_called_once()
    mock_span.add_event.assert_called_once()
    event_call = mock_span.add_event.call_args[0][0]
    assert event_call == "gen_ai.choice"

    set_attrs_call = mock_span.set_attributes.call_args[0][0]
    assert (
        set_attrs_call[gen_ai_attributes.GEN_AI_RESPONSE_MODEL]
        == "mistral-large-latest"
    )
    assert set_attrs_call[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] == 10
    assert set_attrs_call[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] == 20
    assert set_attrs_call[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] == ["stop"]
