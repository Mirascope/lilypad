"""Tests for OpenAI OpenTelemetry utilities."""

import json
from unittest.mock import Mock

import pytest
from openai.types.chat import ChatCompletionMessage, ChatCompletionMessageToolCall
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from openai.types.chat.chat_completion_message_tool_call import Function

from lilypad._opentelemetry._opentelemetry_openai.utils import (
    OpenAIMetadata,
    OpenAIChunkHandler,
    get_tool_calls,
    get_choice_event,
    set_message_event,
    default_openai_cleanup,
    set_response_attributes,
)


@pytest.fixture
def mock_chunk():
    chunk = Mock()
    chunk.model = "gpt-4"
    chunk.id = "test-id"
    chunk.service_tier = "standard"

    choice = Mock()
    choice.index = 0
    choice.delta = Mock()
    choice.delta.content = "test response"
    choice.delta.tool_calls = None
    choice.finish_reason = "stop"

    chunk.choices = [choice]
    chunk.usage = Mock(completion_tokens=20, prompt_tokens=10)
    return chunk


class DictLikeMock:
    """A mock that behaves like a dict but has attribute access."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

    def get(self, key, default=None):
        return self.__dict__.get(key, default)


def test_openai_metadata():
    metadata = OpenAIMetadata()
    assert metadata.get("response_id") is None
    assert metadata.get("response_model") is None
    assert metadata.get("service_tier") is None
    assert metadata.get("finish_reasons", []) == []
    assert metadata.get("prompt_tokens") is None
    assert metadata.get("completion_tokens") is None


def test_openai_chunk_handler(mock_chunk):
    handler = OpenAIChunkHandler()
    metadata = OpenAIMetadata()
    buffers = []

    handler.extract_metadata(mock_chunk, metadata)
    assert metadata["response_model"] == "gpt-4"  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["response_id"] == "test-id"  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["service_tier"] == "standard"  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["completion_tokens"] == 20  # pyright: ignore [reportTypedDictNotRequiredAccess]
    assert metadata["prompt_tokens"] == 10  # pyright: ignore [reportTypedDictNotRequiredAccess]

    handler.process_chunk(mock_chunk, buffers)
    assert len(buffers) == 1
    assert buffers[0].text_content == ["test response"]


def test_get_tool_calls():
    # Create a mock that behaves like a dict with attribute access
    message = {
        "tool_calls": [
            {
                "id": "call_123",
                "type": "function",
                "function": {"name": "test_function", "arguments": '{"arg": "value"}'},
            }
        ]
    }
    tool_calls = get_tool_calls(message)
    assert len(tool_calls) == 1  # pyright: ignore [reportArgumentType]
    assert tool_calls[0]["id"] == "call_123"  # pyright: ignore [reportOptionalSubscript]
    assert tool_calls[0]["type"] == "function"  # pyright: ignore [reportOptionalSubscript]
    assert tool_calls[0]["function"]["name"] == "test_function"  # pyright: ignore [reportOptionalSubscript]
    message = ChatCompletionMessage(
        role="assistant",
        content=None,
        tool_calls=[
            ChatCompletionMessageToolCall(
                id="call_123",
                type="function",
                function=Function(name="test_function", arguments='{"arg": "value"}'),
            )
        ],
    )
    tool_calls = get_tool_calls(message)
    assert len(tool_calls) == 1  # pyright: ignore [reportArgumentType]
    assert tool_calls[0]["id"] == "call_123"  # pyright: ignore [reportOptionalSubscript]
    assert tool_calls[0]["type"] == "function"  # pyright: ignore [reportOptionalSubscript]
    assert tool_calls[0]["function"]["name"] == "test_function"  # pyright: ignore [reportOptionalSubscript]

    # Test without tool calls
    message = {"tool_calls": None}
    assert get_tool_calls(message) is None


def test_set_message_event():
    span = Mock()
    # Test user message
    message = {"role": "user", "content": "Hello"}
    set_message_event(span, message)
    span.add_event.assert_called_with(
        "gen_ai.user.message",
        attributes={gen_ai_attributes.GEN_AI_SYSTEM: "openai", "content": "Hello"},
    )


def test_get_choice_event():
    # Create a mock with proper attribute structure
    message = DictLikeMock(role="assistant", content="Hello", tool_calls=None)

    choice = DictLikeMock(message=message, index=0, finish_reason="stop")

    event_attrs = get_choice_event(choice)
    assert event_attrs[gen_ai_attributes.GEN_AI_SYSTEM] == "openai"
    assert event_attrs["index"] == 0
    assert event_attrs["finish_reason"] == "stop"
    assert json.loads(event_attrs["message"])["role"] == "assistant"  # pyright: ignore [reportArgumentType]
    assert json.loads(event_attrs["message"])["content"] == "Hello"  # pyright: ignore [reportArgumentType]


def test_set_response_attributes():
    span = Mock()
    # Create response with proper message structure
    message = DictLikeMock(role="assistant", content="Hello", tool_calls=None)

    choice = DictLikeMock(message=message, index=0, finish_reason="stop")

    response = DictLikeMock(
        model="gpt-4",
        choices=[choice],
        id="test-id",
        usage=DictLikeMock(prompt_tokens=10, completion_tokens=20),
        service_tier="standard",
    )

    set_response_attributes(span, response)
    assert span.set_attributes.called
    assert span.add_event.called


def test_default_openai_cleanup(mock_chunk):
    span = Mock()
    metadata = OpenAIMetadata(
        response_model="gpt-4",
        response_id="test-id",
        service_tier="standard",
        prompt_tokens=10,
        completion_tokens=20,
        finish_reasons=["stop"],
    )
    buffers = []
    handler = OpenAIChunkHandler()
    handler.process_chunk(mock_chunk, buffers)

    default_openai_cleanup(span, metadata, buffers)

    assert span.set_attributes.called
    assert span.add_event.called


def test_process_chunk_no_choices():
    """Test line 52: early return when chunk has no choices attribute."""
    handler = OpenAIChunkHandler()
    chunk = Mock()
    # Remove choices attribute to trigger early return
    delattr(chunk, "choices") if hasattr(chunk, "choices") else None
    buffers = []

    # This should return early and not modify buffers
    handler.process_chunk(chunk, buffers)
    assert len(buffers) == 0


def test_process_chunk_no_delta():
    """Test line 56: continue when choice.delta is None."""
    handler = OpenAIChunkHandler()
    chunk = Mock()

    choice = Mock()
    choice.index = 0
    choice.delta = None  # This should trigger continue
    choice.finish_reason = None

    chunk.choices = [choice]
    buffers = []

    handler.process_chunk(chunk, buffers)
    # No buffer should be created since we continue early when delta is None
    assert len(buffers) == 0


def test_process_chunk_with_tool_calls():
    """Test lines 69-70: tool call processing loop."""
    handler = OpenAIChunkHandler()
    chunk = Mock()

    # Create mock tool calls - tool_call.index is critical for append_tool_call
    tool_call1 = Mock()
    tool_call1.index = 0  # This is required for ToolCallBuffer indexing
    tool_call1.id = "call_1"
    tool_call1.function = Mock()
    tool_call1.function.name = "test_func"
    tool_call1.function.arguments = '{"arg": "value"}'

    tool_call2 = Mock()
    tool_call2.index = 1  # Different index for second tool call
    tool_call2.id = "call_2"
    tool_call2.function = Mock()
    tool_call2.function.name = "another_func"
    tool_call2.function.arguments = '{"arg2": "value2"}'

    choice = Mock()
    choice.index = 0
    choice.delta = Mock()
    choice.delta.content = None
    choice.delta.tool_calls = [tool_call1, tool_call2]
    choice.finish_reason = None

    chunk.choices = [choice]
    buffers = []

    handler.process_chunk(chunk, buffers)
    assert len(buffers) == 1
    assert len(buffers[0].tool_calls_buffers) == 2


def test_default_cleanup_with_tool_calls():
    """Test lines 95-107: tool calls processing in cleanup."""
    from lilypad._opentelemetry._utils import ChoiceBuffer, ToolCallBuffer

    span = Mock()
    metadata = OpenAIMetadata(response_model="gpt-4")

    # Create buffer with tool calls
    buffer = ChoiceBuffer(0)
    buffer.text_content = ["Some text"]

    # Create tool call buffers - need index, tool_call_id, function_name
    tool_call1 = ToolCallBuffer(0, "call_1", "test_func")
    tool_call1.arguments = ["arg1", "arg2"]

    tool_call2 = ToolCallBuffer(1, "call_2", "another_func")
    tool_call2.arguments = ["arg3"]

    buffer.tool_calls_buffers = [tool_call1, tool_call2]
    buffers = [buffer]

    default_openai_cleanup(span, metadata, buffers)

    # Verify span.add_event was called for choice with tool calls
    assert span.add_event.called
    call_args = span.add_event.call_args[1]["attributes"]
    message_data = json.loads(call_args["message"])
    assert "tool_calls" in message_data
    assert len(message_data["tool_calls"]) == 2
    assert message_data["tool_calls"][0]["id"] == "call_1"
    assert message_data["tool_calls"][0]["function"]["name"] == "test_func"
    assert message_data["tool_calls"][0]["function"]["arguments"] == "arg1arg2"


def test_set_message_event_non_string_content():
    """Test line 151: non-string content JSON conversion."""
    span = Mock()
    # Test with dict content (non-string)
    message = {"role": "user", "content": {"type": "text", "text": "Hello"}}
    set_message_event(span, message)

    call_args = span.add_event.call_args[1]["attributes"]
    # Content should be JSON string of the dict (compact JSON format)
    assert '"type":"text"' in call_args["content"]
    assert '"text":"Hello"' in call_args["content"]


def test_set_message_event_assistant_with_tool_calls():
    """Test lines 153-154: assistant role with tool calls."""
    span = Mock()
    message = {
        "role": "assistant",
        "content": None,  # No content, but has tool calls
        "tool_calls": [
            {"id": "call_123", "type": "function", "function": {"name": "test_func", "arguments": '{"arg": "value"}'}}
        ],
    }
    set_message_event(span, message)

    call_args = span.add_event.call_args[1]["attributes"]
    assert "tool_calls" in call_args
    tool_calls_data = json.loads(call_args["tool_calls"])
    assert len(tool_calls_data) == 1
    assert tool_calls_data[0]["id"] == "call_123"


def test_set_message_event_tool_role():
    """Test lines 155-156: tool role with tool_call_id."""
    span = Mock()
    # Test tool role WITHOUT content to hit the elif branch (lines 155-156)
    message = {"role": "tool", "tool_call_id": "call_456"}
    set_message_event(span, message)

    call_args = span.add_event.call_args[1]["attributes"]
    # Should have id attribute when no content (elif branch)
    assert call_args["id"] == "call_456"
    assert "content" not in call_args


def test_set_message_event_tool_role_with_content():
    """Test tool role with content (takes first if branch, not elif)."""
    span = Mock()
    message = {"role": "tool", "content": "Tool response", "tool_call_id": "call_456"}
    set_message_event(span, message)

    call_args = span.add_event.call_args[1]["attributes"]
    # When there's content, it takes the first if branch, not the elif
    assert call_args["content"] == "Tool response"
    # The tool_call_id is NOT set because elif is not reached
    assert "id" not in call_args


def test_get_choice_event_with_tool_calls():
    """Test line 176: tool calls processing in get_choice_event."""
    # Create mock message with tool calls
    message = DictLikeMock(
        role="assistant",
        content=None,
        tool_calls=[
            {"id": "call_789", "type": "function", "function": {"name": "my_func", "arguments": '{"test": "data"}'}}
        ],
    )

    choice = DictLikeMock(message=message, index=0, finish_reason="tool_calls")

    event_attrs = get_choice_event(choice)
    message_data = json.loads(event_attrs["message"])

    assert "tool_calls" in message_data
    assert len(message_data["tool_calls"]) == 1
    assert message_data["tool_calls"][0]["id"] == "call_789"
