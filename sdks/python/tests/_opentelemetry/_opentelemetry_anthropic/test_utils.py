"""Tests for Anthropic OpenTelemetry utilities."""

from unittest.mock import Mock, patch

import pytest
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from lilypad._opentelemetry._opentelemetry_anthropic.utils import (
    AnthropicMetadata,
    AnthropicChunkHandler,
    get_message_event,
    set_message_event,
    set_response_attributes,
    default_anthropic_cleanup,
    get_llm_request_attributes,
    get_tool_call,
    get_tool_calls,
)


class DictLikeMock:
    """A mock that behaves like a dict but has attribute access."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)


@pytest.fixture
def mock_chunk():
    chunk = Mock()
    chunk.model = "claude-3-opus-20240229"
    chunk.id = "msg_123"
    chunk.type = "content_block_delta"

    chunk.delta = Mock()
    chunk.delta.type = "text_delta"
    chunk.delta.text = "test response"
    chunk.index = 0
    chunk.stop_reason = "stop"

    chunk.usage = Mock(input_tokens=10, output_tokens=20)
    return chunk


def test_anthropic_metadata():
    metadata = AnthropicMetadata()
    assert metadata.get("message_id") is None
    assert metadata.get("model") is None
    assert metadata.get("input_tokens") is None
    assert metadata.get("output_tokens") is None
    assert metadata.get("stop_reason") is None


def test_anthropic_chunk_handler(mock_chunk):
    handler = AnthropicChunkHandler()
    metadata = AnthropicMetadata()
    buffers = []

    # Test metadata extraction
    handler.extract_metadata(mock_chunk, metadata)
    assert metadata["model"] == "claude-3-opus-20240229"  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["message_id"] == "msg_123"  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["stop_reason"] == "stop"  # pyright: ignore [reportTypedDictNotRequiredAccess]

    # Test chunk processing
    handler.process_chunk(mock_chunk, buffers)
    assert len(buffers) == 1
    assert buffers[0].text_content == ["test response"]


def test_get_tool_call():
    content = DictLikeMock(type="tool_use", id="call_123", name="test_function", input={"arg": "value"})

    # Initialize tool_call_dict with function key
    tool_call_dict = {
        "id": content.id,  # pyright: ignore [reportAttributeAccessIssue]
        "type": content.type,  # pyright: ignore [reportAttributeAccessIssue]
        "function": {"name": content.name, "arguments": content.input},  # pyright: ignore [reportAttributeAccessIssue]
    }

    assert tool_call_dict["id"] == "call_123"
    assert tool_call_dict["type"] == "tool_use"
    assert tool_call_dict["function"]["name"] == "test_function"
    assert tool_call_dict["function"]["arguments"] == {"arg": "value"}


def test_get_tool_calls():
    message = DictLikeMock(type="tool_use", id="call_123", name="test_function", input={"arg": "value"})

    messages = [message]
    tool_calls = []
    for msg in messages:
        if msg.type == "tool_use":  # pyright: ignore [reportAttributeAccessIssue]
            tool_call = {
                "id": msg.id,  # pyright: ignore [reportAttributeAccessIssue]
                "type": msg.type,  # pyright: ignore [reportAttributeAccessIssue]
                "function": {"name": msg.name, "arguments": msg.input},  # pyright: ignore [reportAttributeAccessIssue]
            }
            tool_calls.append(tool_call)

    assert len(tool_calls) == 1
    assert tool_calls[0]["id"] == "call_123"
    assert tool_calls[0]["type"] == "tool_use"
    assert tool_calls[0]["function"]["name"] == "test_function"
    assert tool_calls[0]["function"]["arguments"] == {"arg": "value"}


def test_set_message_event():
    span = Mock()
    message = {"role": "user", "content": [{"type": "text", "text": "Hello"}]}

    set_message_event(span, message)
    span.add_event.assert_called_with(
        "gen_ai.user.message",
        attributes={
            gen_ai_attributes.GEN_AI_SYSTEM: "anthropic",
            "content": '[{"type":"text","text":"Hello"}]',
        },
    )


def test_get_message_event():
    message = DictLikeMock(text="Hello", type="text")

    event_attrs = get_message_event(message)
    assert event_attrs[gen_ai_attributes.GEN_AI_SYSTEM] == "anthropic"
    assert "message" in event_attrs


def test_set_response_attributes():
    span = Mock()
    content = DictLikeMock(type="text", text="Hello")

    response = DictLikeMock(
        model="claude-3-opus-20240229",
        role="assistant",
        content=[content],
        stop_reason="stop",
        id="msg_123",
        usage=DictLikeMock(input_tokens=10, output_tokens=20),
    )

    set_response_attributes(span, response)
    assert span.set_attributes.called
    assert span.add_event.called


def test_default_anthropic_cleanup(mock_chunk):
    span = Mock()
    metadata = AnthropicMetadata(
        model="claude-3-opus-20240229",
        message_id="msg_123",
        stop_reason="stop",
        input_tokens=10,
        output_tokens=20,
    )
    buffers = []
    handler = AnthropicChunkHandler()
    handler.process_chunk(mock_chunk, buffers)

    default_anthropic_cleanup(span, metadata, buffers)

    assert span.set_attributes.called
    assert span.add_event.called


def test_llm_request_attributes():
    kwargs = {
        "model": "claude-3-opus-20240229",
        "temperature": 0.7,
        "max_tokens": 100,
        "top_p": 0.9,
        "top_k": 40,
        "stop_sequences": ["END"],
    }
    client_instance = Mock()

    attrs = get_llm_request_attributes(kwargs, client_instance)
    assert attrs[gen_ai_attributes.GEN_AI_SYSTEM] == "anthropic"
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_MODEL] == "claude-3-opus-20240229"
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TEMPERATURE] == 0.7
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_MAX_TOKENS] == 100
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TOP_P] == 0.9
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_TOP_K] == 40
    assert attrs[gen_ai_attributes.GEN_AI_REQUEST_STOP_SEQUENCES] == ["END"]


def test_anthropic_chunk_handler_with_tool_calls():
    """Test chunk processing with tool calls."""
    handler = AnthropicChunkHandler()
    buffers = []

    # Create a chunk with tool calls
    chunk = Mock()
    chunk.index = 0
    chunk.type = "content_block_delta"
    chunk.delta = Mock()
    chunk.delta.type = "input_json_delta"

    # Create proper tool_call mock with required attributes
    tool_call_mock = Mock()
    tool_call_mock.index = 0
    tool_call_mock.id = "call_123"
    tool_call_mock.function = Mock()
    tool_call_mock.function.name = "test_func"

    chunk.delta.tool_call = tool_call_mock

    handler.process_chunk(chunk, buffers)
    assert len(buffers) == 1
    assert len(buffers[0].tool_calls_buffers) == 1


def test_anthropic_chunk_handler_no_index():
    """Test chunk processing when chunk has no index."""
    handler = AnthropicChunkHandler()
    buffers = []

    chunk = Mock()
    del chunk.index  # Remove index attribute

    result = handler.process_chunk(chunk, buffers)
    assert result is None
    assert len(buffers) == 0


def test_default_anthropic_cleanup_with_tool_calls():
    """Test cleanup with tool calls in buffers."""
    span = Mock()
    metadata = AnthropicMetadata(
        model="claude-3-opus-20240229",
        message_id="msg_123",
        stop_reason="stop",
        input_tokens=10,
        output_tokens=20,
    )

    # Create buffer with tool calls
    from lilypad._opentelemetry._utils import ChoiceBuffer, ToolCallBuffer

    buffer = ChoiceBuffer(0)
    tool_call_buffer = ToolCallBuffer(0, "call_123", "test_func")
    tool_call_buffer.arguments = ['{"arg": "value"}']
    buffer.tool_calls_buffers = [tool_call_buffer]
    buffers = [buffer]

    default_anthropic_cleanup(span, metadata, buffers)

    assert span.set_attributes.called
    assert span.add_event.called


def test_get_tool_call_with_actual_function():
    """Test get_tool_call function with proper content."""
    content = DictLikeMock(type="tool_use", id="call_123", name="test_function", input={"arg": "value"})

    result = get_tool_call(content)
    assert result is not None
    assert result["id"] == "call_123"
    assert result["type"] == "tool_use"
    assert result["function"]["name"] == "test_function"
    assert result["function"]["arguments"] == {"arg": "value"}


def test_get_tool_call_non_tool_use():
    """Test get_tool_call with non-tool_use content."""
    content = DictLikeMock(type="text", text="Hello")

    result = get_tool_call(content)
    assert result is None


def test_get_tool_calls_multiple_messages():
    """Test get_tool_calls with multiple messages."""
    tool_message = DictLikeMock(type="tool_use", id="call_123", name="test_function", input={"arg": "value"})
    text_message = DictLikeMock(type="text", text="Hello")

    messages = [tool_message, text_message]
    result = get_tool_calls(messages)

    assert len(result) == 1
    assert result[0]["id"] == "call_123"


def test_set_message_event_assistant_with_tool_calls():
    """Test set_message_event for assistant with tool calls."""
    span = Mock()

    # Create a message that will trigger tool_calls path
    message = {"role": "assistant", "content": "Some assistant response"}

    # Mock get_tool_calls to return tool calls
    with patch("lilypad._opentelemetry._opentelemetry_anthropic.utils.get_tool_calls") as mock_get_tool_calls:
        mock_get_tool_calls.return_value = [{"id": "call_123", "type": "tool_use"}]
        set_message_event(span, message)

        span.add_event.assert_called()


def test_get_message_event_with_tool_call():
    """Test get_message_event with tool_call content."""
    message = DictLikeMock(type="tool_use", id="call_123", name="test_function", input={"arg": "value"})

    result = get_message_event(message)
    assert gen_ai_attributes.GEN_AI_SYSTEM in result
    assert "message" in result


def test_set_message_event_assistant_no_content_with_tool_calls():
    """Test set_message_event for assistant with no content but tool calls - covers lines 159-160."""
    span = Mock()

    # Create message with no content but tool calls available
    message = {"role": "assistant"}  # No content field

    # Mock get_tool_calls to return tool calls
    with patch("lilypad._opentelemetry._opentelemetry_anthropic.utils.get_tool_calls") as mock_get_tool_calls:
        mock_get_tool_calls.return_value = [{"id": "call_123", "type": "tool_use", "function": {"name": "test"}}]
        set_message_event(span, message)

        # Should call add_event with tool_calls in attributes
        span.add_event.assert_called_with(
            "gen_ai.assistant.message",
            attributes={
                gen_ai_attributes.GEN_AI_SYSTEM: "anthropic",
                "tool_calls": '[{"id":"call_123","type":"tool_use","function":{"name":"test"}}]',
            },
        )
