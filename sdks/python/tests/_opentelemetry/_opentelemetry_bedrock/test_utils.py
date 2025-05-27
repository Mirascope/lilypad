"""Tests for Bedrock OpenTelemetry utilities."""

from unittest.mock import Mock

import pytest
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad.lib._opentelemetry._opentelemetry_bedrock.utils import (
    BedrockMetadata,
    BedrockChunkHandler,
    default_bedrock_cleanup,
    get_bedrock_llm_request_attributes,
)


@pytest.fixture
def mock_stream_chunk():
    return {
        "contentBlockDelta": {
            "delta": {"text": "partial text"},
            "contentBlockIndex": 0,
        },
        "metadata": {"usage": {"inputTokens": 10, "outputTokens": 5}},
    }


def test_bedrock_metadata():
    metadata = BedrockMetadata()
    assert "prompt_tokens" not in metadata
    assert "completion_tokens" not in metadata
    assert "response_model" not in metadata
    assert "finish_reasons" not in metadata


def test_bedrock_chunk_handler_extract_metadata(mock_stream_chunk):
    handler = BedrockChunkHandler()
    metadata = BedrockMetadata()
    handler.extract_metadata(mock_stream_chunk, metadata)
    assert metadata["prompt_tokens"] == 10  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["completion_tokens"] == 5  # pyright: ignore [reportTypedDictNotRequiredAccess]


def test_bedrock_chunk_handler_process_chunk(mock_stream_chunk):
    handler = BedrockChunkHandler()
    buffers = []
    handler.process_chunk(mock_stream_chunk, buffers)
    assert len(buffers) == 1
    assert buffers[0].text_content == ["partial text"]


def test_bedrock_chunk_handler_stop_reason():
    handler = BedrockChunkHandler()
    metadata = BedrockMetadata()
    chunk = {"messageStop": {"stopReason": "max_length"}}
    handler.extract_metadata(chunk, metadata)
    assert metadata["finish_reasons"] == ["max_length"]  # pyright: ignore [reportTypedDictNotRequiredAccess]


def test_default_bedrock_cleanup():
    span = Mock()
    metadata = BedrockMetadata()
    metadata["prompt_tokens"] = 20
    metadata["completion_tokens"] = 30
    metadata["finish_reasons"] = ["stop"]
    buffers = []
    default_bedrock_cleanup(span, metadata, buffers)
    assert span.set_attributes.called
    span.set_attributes.assert_called_with(
        {
            gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS: 20,
            gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS: 30,
            gen_ai_attributes.GEN_AI_RESPONSE_FINISH_REASONS: ["stop"],
        }
    )


def test_get_bedrock_llm_request_attributes():
    kwargs = {
        "modelId": "anthropic.claude-3-haiku-20240307-v1:0",
        "inferenceConfig": {
            "temperature": 0.5,
            "topP": 0.9,
            "maxTokens": 1024,
            "stopSequences": "STOP",
        },
    }
    attrs = get_bedrock_llm_request_attributes(kwargs)
    assert attrs["gen_ai.request.model"] == "anthropic.claude-3-haiku-20240307-v1:0"
    assert attrs["gen_ai.request.temperature"] == 0.5
    assert attrs["gen_ai.request.top_p"] == 0.9
    assert attrs["gen_ai.request.max_tokens"] == 1024
    assert attrs["gen_ai.request.stop_sequences"] == ["STOP"]
