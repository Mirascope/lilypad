"""Tests for Bedrock OpenTelemetry utilities."""

from unittest.mock import Mock

import pytest
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad._opentelemetry._opentelemetry_bedrock.utils import (
    BedrockMetadata,
    BedrockChunkHandler,
    default_bedrock_cleanup,
    get_bedrock_llm_request_attributes,
    set_bedrock_message_event,
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


def test_bedrock_chunk_handler_process_chunk_not_dict():
    """Test process_chunk with non-dict chunk - covers line 56."""
    handler = BedrockChunkHandler()
    buffers = []

    # Test with non-dict chunk
    handler.process_chunk("not a dict", buffers)
    assert len(buffers) == 0

    # Test with dict that has no contentBlockDelta
    handler.process_chunk({"other": "data"}, buffers)
    assert len(buffers) == 0

    # Test with contentBlockDelta that's not a dict
    handler.process_chunk({"contentBlockDelta": "not a dict"}, buffers)
    assert len(buffers) == 0


def test_bedrock_chunk_handler_process_chunk_edge_cases():
    """Test process_chunk edge cases - covers lines 71, 80-103."""

    handler = BedrockChunkHandler()
    buffers = []

    # Test with higher index to trigger buffer expansion
    chunk = {"contentBlockDelta": {"contentBlockIndex": 2, "delta": {"text": "text for index 2"}}}
    handler.process_chunk(chunk, buffers)
    assert len(buffers) == 3  # Should create buffers 0, 1, 2
    assert buffers[2].text_content == ["text for index 2"]

    # Test with delta that's not a dict
    chunk_invalid_delta = {"contentBlockDelta": {"contentBlockIndex": 0, "delta": "not a dict"}}
    handler.process_chunk(chunk_invalid_delta, buffers)
    # Should not crash, just not add content

    # Test with text that's not a string
    chunk_invalid_text = {
        "contentBlockDelta": {
            "contentBlockIndex": 0,
            "delta": {"text": 123},  # Not a string
        }
    }
    handler.process_chunk(chunk_invalid_text, buffers)
    # Should not crash, just not add content


def test_set_bedrock_message_event():
    """Test set_bedrock_message_event function - covers lines 109-116, 120."""
    span = Mock()
    span.is_recording.return_value = True

    # Test with string content
    message = {"role": "user", "content": "Hello world"}
    set_bedrock_message_event(span, message)
    span.add_event.assert_called_with(
        "gen_ai.user.message", attributes={gen_ai_attributes.GEN_AI_SYSTEM: "bedrock", "content": "Hello world"}
    )

    # Test with list content
    message_list = {"role": "assistant", "content": [{"type": "text", "text": "Response"}]}
    set_bedrock_message_event(span, message_list)
    span.add_event.assert_called_with(
        "gen_ai.assistant.message",
        attributes={gen_ai_attributes.GEN_AI_SYSTEM: "bedrock", "content": '[{"type":"text","text":"Response"}]'},
    )

    # Test with non-string, non-list content
    message_other = {"role": "system", "content": 123}
    set_bedrock_message_event(span, message_other)
    span.add_event.assert_called_with(
        "gen_ai.system.message", attributes={gen_ai_attributes.GEN_AI_SYSTEM: "bedrock", "content": ""}
    )

    # Test when span is not recording
    span.is_recording.return_value = False
    span.add_event.reset_mock()
    set_bedrock_message_event(span, message)
    span.add_event.assert_not_called()


def test_set_bedrock_message_event_json_error():
    """Test set_bedrock_message_event with JSON serialization error - covers lines 115-116."""
    span = Mock()
    span.is_recording.return_value = True

    # Create a content that will cause JSON serialization error
    class UnserializableObject:
        def __str__(self):
            return "unserializable"

    message = {"role": "user", "content": {"obj": UnserializableObject()}}

    # Mock json_dumps to raise an error
    with pytest.raises(TypeError):
        import json

        json.dumps(message["content"])

    # The function should handle this gracefully and use str() instead
    set_bedrock_message_event(span, message)
    span.add_event.assert_called_with(
        "gen_ai.user.message",
        attributes={gen_ai_attributes.GEN_AI_SYSTEM: "bedrock", "content": str(message["content"])},
    )


def test_default_bedrock_cleanup_with_response_model():
    """Test default_bedrock_cleanup with response_model in metadata - covers line 71."""
    span = Mock()
    metadata = BedrockMetadata()
    metadata["response_model"] = "bedrock-model"  # Set response_model
    metadata["prompt_tokens"] = 20
    metadata["completion_tokens"] = 30
    metadata["finish_reasons"] = ["stop"]
    buffers = []

    default_bedrock_cleanup(span, metadata, buffers)

    # Check that set_attributes was called with response_model
    attrs = span.set_attributes.call_args[0][0]
    assert gen_ai_attributes.GEN_AI_RESPONSE_MODEL in attrs
    assert attrs[gen_ai_attributes.GEN_AI_RESPONSE_MODEL] == "bedrock-model"


def test_default_bedrock_cleanup_with_tool_calls():
    """Test default_bedrock_cleanup with tool calls in buffers - covers lines 80-103."""
    span = Mock()
    metadata = BedrockMetadata()
    metadata["prompt_tokens"] = 20
    metadata["completion_tokens"] = 30
    metadata["finish_reasons"] = ["stop"]

    # Create buffer with tool calls
    from lilypad._opentelemetry._utils import ChoiceBuffer, ToolCallBuffer

    buffer = ChoiceBuffer(0)

    # Add text content
    buffer.text_content = ["Hello, "]
    buffer.append_text_content("world\!")

    # Add tool calls
    tool_call_buffer = ToolCallBuffer(0, "call_123", "test_function")
    tool_call_buffer.arguments = ['{"arg1": "value1",', ' "arg2": "value2"}']
    buffer.tool_calls_buffers = [tool_call_buffer]
    buffer.finish_reason = "tool_calls"

    buffers = [buffer]

    default_bedrock_cleanup(span, metadata, buffers)

    # Verify span.add_event was called
    span.add_event.assert_called_once()
    event_call = span.add_event.call_args
    assert event_call[0][0] == "gen_ai.choice"

    # Verify the event attributes contain tool_calls
    event_attrs = event_call[1]["attributes"]
    assert "message" in event_attrs

    # Parse the message to verify tool_calls
    import json

    message = json.loads(event_attrs["message"])
    assert "content" in message
    assert message["content"] == "Hello, world\!"
    assert "tool_calls" in message
    assert len(message["tool_calls"]) == 1
    assert message["tool_calls"][0]["id"] == "call_123"
    assert message["tool_calls"][0]["type"] == "function"
    assert message["tool_calls"][0]["function"]["name"] == "test_function"
    assert message["tool_calls"][0]["function"]["arguments"] == '{"arg1": "value1", "arg2": "value2"}'
