"""Tests for Mistral OpenTelemetry utilities."""

from unittest.mock import Mock

import pytest
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad.lib._opentelemetry._utils import ChoiceBuffer
from lilypad.lib._opentelemetry._opentelemetry_mistral.utils import (
    MistralMetadata,
    MistralChunkHandler,
    default_mistral_cleanup,
    get_mistral_llm_request_attributes,
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
    }
    attrs = get_mistral_llm_request_attributes(kwargs)
    assert attrs["gen_ai.request.model"] == "mistral-large-latest"


def test_mistral_chunk_handler_extract_and_process():
    # Mock a CompletionChunk-like event
    # CompletionChunk: id, model, choices[], usage...
    chunk = Mock()
    chunk.model = "mistral-large-latest"
    usage = Mock()
    usage.prompt_tokens = 10
    usage.completion_tokens = 20
    chunk.usage = usage
    choice = Mock()
    choice.index = 0
    choice.finish_reason = "stop"
    delta = Mock()
    delta.content = "This is partial content"
    choice.delta = delta
    chunk.choices = [choice]

    event = Mock()
    event.data = chunk

    metadata = MistralMetadata()
    handler = MistralChunkHandler()

    handler.extract_metadata(event, metadata)
    assert metadata["response_model"] == "mistral-large-latest"
    assert metadata["prompt_tokens"] == 10
    assert metadata["completion_tokens"] == 20

    buffers = []
    handler.process_chunk(event, buffers)
    assert len(buffers) == 1
    assert buffers[0].finish_reason == "stop"
    assert "".join(buffers[0].text_content) == "This is partial content"


def test_default_mistral_cleanup(mock_span):
    metadata = MistralMetadata()
    metadata["response_model"] = "mistral-large-latest"
    metadata["prompt_tokens"] = 10
    metadata["completion_tokens"] = 20
    metadata["finish_reasons"] = ["stop"]

    buffers = [ChoiceBuffer(0)]
    buffers[0].finish_reason = "stop"  # pyright: ignore [reportAttributeAccessIssue]
    buffers[0].append_text_content("Final content")

    default_mistral_cleanup(mock_span, metadata, buffers)
    mock_span.set_attributes.assert_called_once()
    attrs = mock_span.set_attributes.call_args[0][0]
    assert attrs[gen_ai_attributes.GEN_AI_RESPONSE_MODEL] == "mistral-large-latest"
    assert attrs[gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS] == 10
    assert attrs[gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS] == 20
    assert attrs[gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS] == ["stop"]
    mock_span.add_event.assert_called_once()
    event_call = mock_span.add_event.call_args[0][0]
    assert event_call == "gen_ai.choice"
