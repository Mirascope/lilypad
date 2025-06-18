"""Tests for Azure OpenTelemetry utils."""

from unittest.mock import Mock, patch
from pydantic import BaseModel

from lilypad._opentelemetry._opentelemetry_azure.utils import (
    AzureMetadata,
    AzureChunkHandler,
    default_azure_cleanup,
    get_tool_calls,
    set_message_event,
    get_choice_event,
    set_response_attributes,
)
from lilypad._opentelemetry._utils import ChoiceBuffer


class TestAzureMetadata:
    """Test AzureMetadata TypedDict."""

    def test_azure_metadata_empty(self):
        """Test creating empty AzureMetadata."""
        metadata: AzureMetadata = {}

        assert metadata == {}
        assert "response_id" not in metadata
        assert "response_model" not in metadata
        assert "finish_reasons" not in metadata
        assert "prompt_tokens" not in metadata
        assert "completion_tokens" not in metadata

    def test_azure_metadata_full(self):
        """Test creating full AzureMetadata."""
        metadata: AzureMetadata = {
            "response_id": "response-123",
            "response_model": "gpt-4",
            "finish_reasons": ["stop", "length"],
            "prompt_tokens": 10,
            "completion_tokens": 20,
        }

        assert metadata["response_id"] == "response-123"
        assert metadata["response_model"] == "gpt-4"
        assert metadata["finish_reasons"] == ["stop", "length"]
        assert metadata["prompt_tokens"] == 10
        assert metadata["completion_tokens"] == 20

    def test_azure_metadata_partial(self):
        """Test creating partial AzureMetadata."""
        metadata: AzureMetadata = {
            "response_id": "response-456",
            "prompt_tokens": 15,
        }

        assert metadata["response_id"] == "response-456"
        assert metadata["prompt_tokens"] == 15
        assert "response_model" not in metadata
        assert "finish_reasons" not in metadata
        assert "completion_tokens" not in metadata


class TestAzureChunkHandler:
    """Test AzureChunkHandler class."""

    def test_init(self):
        """Test AzureChunkHandler initialization."""
        handler = AzureChunkHandler()
        assert isinstance(handler, AzureChunkHandler)

    def test_extract_metadata_with_model(self):
        """Test extract_metadata with model attribute."""
        handler = AzureChunkHandler()
        metadata: AzureMetadata = {}

        mock_chunk = Mock()
        mock_chunk.model = "gpt-4-turbo"

        handler.extract_metadata(mock_chunk, metadata)

        assert metadata["response_model"] == "gpt-4-turbo"

    def test_extract_metadata_with_existing_model(self):
        """Test extract_metadata doesn't overwrite existing model."""
        handler = AzureChunkHandler()
        metadata: AzureMetadata = {"response_model": "existing-model"}

        mock_chunk = Mock()
        mock_chunk.model = "new-model"

        handler.extract_metadata(mock_chunk, metadata)

        assert metadata["response_model"] == "existing-model"

    def test_extract_metadata_without_model(self):
        """Test extract_metadata when chunk has no model attribute."""
        handler = AzureChunkHandler()
        metadata: AzureMetadata = {}

        mock_chunk = Mock(spec=[])  # Mock with no attributes

        handler.extract_metadata(mock_chunk, metadata)

        assert "response_model" not in metadata

    def test_extract_metadata_with_id(self):
        """Test extract_metadata with id attribute."""
        handler = AzureChunkHandler()
        metadata: AzureMetadata = {}

        mock_chunk = Mock()
        mock_chunk.id = "response-id-123"

        handler.extract_metadata(mock_chunk, metadata)

        assert metadata["response_id"] == "response-id-123"

    def test_extract_metadata_with_existing_id(self):
        """Test extract_metadata doesn't overwrite existing id."""
        handler = AzureChunkHandler()
        metadata: AzureMetadata = {"response_id": "existing-id"}

        mock_chunk = Mock()
        mock_chunk.id = "new-id"

        handler.extract_metadata(mock_chunk, metadata)

        assert metadata["response_id"] == "existing-id"

    def test_extract_metadata_with_usage_full(self):
        """Test extract_metadata with full usage information."""
        handler = AzureChunkHandler()
        metadata: AzureMetadata = {}

        mock_usage = Mock()
        mock_usage.completion_tokens = 25
        mock_usage.prompt_tokens = 15

        mock_chunk = Mock()
        mock_chunk.usage = mock_usage

        handler.extract_metadata(mock_chunk, metadata)

        assert metadata["completion_tokens"] == 25
        assert metadata["prompt_tokens"] == 15

    def test_extract_metadata_with_usage_partial(self):
        """Test extract_metadata with partial usage information."""
        handler = AzureChunkHandler()
        metadata: AzureMetadata = {}

        mock_usage = Mock(spec=["completion_tokens"])  # Only has completion_tokens
        mock_usage.completion_tokens = 30

        mock_chunk = Mock()
        mock_chunk.usage = mock_usage

        handler.extract_metadata(mock_chunk, metadata)

        assert metadata["completion_tokens"] == 30
        assert "prompt_tokens" not in metadata

    def test_extract_metadata_without_usage(self):
        """Test extract_metadata when chunk has no usage attribute."""
        handler = AzureChunkHandler()
        metadata: AzureMetadata = {}

        mock_chunk = Mock(spec=["model", "id"])  # Mock without usage
        mock_chunk.model = "test-model"
        mock_chunk.id = "test-id"

        handler.extract_metadata(mock_chunk, metadata)

        assert metadata["response_model"] == "test-model"
        assert metadata["response_id"] == "test-id"
        assert "completion_tokens" not in metadata
        assert "prompt_tokens" not in metadata

    def test_process_chunk_without_choices(self):
        """Test process_chunk when chunk has no choices attribute."""
        handler = AzureChunkHandler()
        buffers = []

        mock_chunk = Mock(spec=[])  # Mock with no attributes

        handler.process_chunk(mock_chunk, buffers)

        assert len(buffers) == 0

    def test_process_chunk_with_empty_choices(self):
        """Test process_chunk with empty choices list."""
        handler = AzureChunkHandler()
        buffers = []

        mock_chunk = Mock()
        mock_chunk.choices = []

        handler.process_chunk(mock_chunk, buffers)

        assert len(buffers) == 0

    def test_process_chunk_without_delta(self):
        """Test process_chunk when choice has no delta."""
        handler = AzureChunkHandler()
        buffers = []

        mock_choice = Mock()
        mock_choice.delta = None
        mock_choice.index = 0

        mock_chunk = Mock()
        mock_chunk.choices = [mock_choice]

        handler.process_chunk(mock_chunk, buffers)

        # Should not create any buffers since delta is None
        assert len(buffers) == 0

    def test_process_chunk_creates_buffer_for_new_index(self):
        """Test process_chunk creates buffer for new choice index."""
        handler = AzureChunkHandler()
        buffers = []

        mock_delta = Mock()
        mock_delta.content = "Hello"
        mock_delta.tool_calls = None

        mock_choice = Mock()
        mock_choice.delta = mock_delta
        mock_choice.index = 0
        mock_choice.finish_reason = None

        mock_chunk = Mock()
        mock_chunk.choices = [mock_choice]

        handler.process_chunk(mock_chunk, buffers)

        assert len(buffers) == 1
        assert isinstance(buffers[0], ChoiceBuffer)
        assert buffers[0].index == 0

    def test_process_chunk_creates_multiple_buffers(self):
        """Test process_chunk creates multiple buffers for high index."""
        handler = AzureChunkHandler()
        buffers = []

        mock_delta = Mock()
        mock_delta.content = "Hello"
        mock_delta.tool_calls = None

        mock_choice = Mock()
        mock_choice.delta = mock_delta
        mock_choice.index = 2  # Should create buffers for indices 0, 1, 2
        mock_choice.finish_reason = None

        mock_chunk = Mock()
        mock_chunk.choices = [mock_choice]

        handler.process_chunk(mock_chunk, buffers)

        assert len(buffers) == 3
        assert all(isinstance(buffer, ChoiceBuffer) for buffer in buffers)
        assert buffers[0].index == 0
        assert buffers[1].index == 1
        assert buffers[2].index == 2

    def test_process_chunk_sets_finish_reason(self):
        """Test process_chunk sets finish_reason on buffer."""
        handler = AzureChunkHandler()
        buffers = []

        mock_delta = Mock()
        mock_delta.content = "Hello"
        mock_delta.tool_calls = None

        mock_choice = Mock()
        mock_choice.delta = mock_delta
        mock_choice.index = 0
        mock_choice.finish_reason = "stop"

        mock_chunk = Mock()
        mock_chunk.choices = [mock_choice]

        handler.process_chunk(mock_chunk, buffers)

        assert len(buffers) == 1
        assert buffers[0].finish_reason == "stop"

    def test_process_chunk_with_content(self):
        """Test process_chunk processes delta content."""
        handler = AzureChunkHandler()
        buffers = []

        mock_delta = Mock()
        mock_delta.content = "Hello world"
        mock_delta.tool_calls = None

        mock_choice = Mock()
        mock_choice.delta = mock_delta
        mock_choice.index = 0
        mock_choice.finish_reason = None

        mock_chunk = Mock()
        mock_chunk.choices = [mock_choice]

        # Create initial buffer to verify content processing
        buffer = ChoiceBuffer(0)
        buffers.append(buffer)

        handler.process_chunk(mock_chunk, buffers)

        # The actual content processing logic would be in the full implementation
        assert len(buffers) == 1

    def test_process_chunk_with_none_content(self):
        """Test process_chunk when delta content is None."""
        handler = AzureChunkHandler()
        buffers = []

        mock_delta = Mock()
        mock_delta.content = None
        mock_delta.tool_calls = None

        mock_choice = Mock()
        mock_choice.delta = mock_delta
        mock_choice.index = 0
        mock_choice.finish_reason = "stop"

        mock_chunk = Mock()
        mock_chunk.choices = [mock_choice]

        handler.process_chunk(mock_chunk, buffers)

        assert len(buffers) == 1
        assert buffers[0].finish_reason == "stop"

    def test_process_chunk_multiple_choices(self):
        """Test process_chunk with multiple choices."""
        handler = AzureChunkHandler()
        buffers = []

        # First choice
        mock_delta1 = Mock()
        mock_delta1.content = "First"
        mock_delta1.tool_calls = None
        mock_choice1 = Mock()
        mock_choice1.delta = mock_delta1
        mock_choice1.index = 0
        mock_choice1.finish_reason = None

        # Second choice
        mock_delta2 = Mock()
        mock_delta2.content = "Second"
        mock_delta2.tool_calls = None
        mock_choice2 = Mock()
        mock_choice2.delta = mock_delta2
        mock_choice2.index = 1
        mock_choice2.finish_reason = "stop"

        mock_chunk = Mock()
        mock_chunk.choices = [mock_choice1, mock_choice2]

        handler.process_chunk(mock_chunk, buffers)

        assert len(buffers) == 2
        assert buffers[0].index == 0
        assert buffers[1].index == 1
        assert buffers[1].finish_reason == "stop"

    def test_process_chunk_with_tool_calls(self):
        """Test process_chunk with tool calls."""
        handler = AzureChunkHandler()
        buffers = []

        # Mock tool call
        mock_tool_call = Mock()
        mock_tool_call.id = "call_123"
        mock_tool_call.index = 0
        mock_tool_call.function = Mock()
        mock_tool_call.function.name = "test_function"

        mock_delta = Mock()
        mock_delta.content = None
        mock_delta.tool_calls = [mock_tool_call]

        mock_choice = Mock()
        mock_choice.delta = mock_delta
        mock_choice.index = 0
        mock_choice.finish_reason = None

        mock_chunk = Mock()
        mock_chunk.choices = [mock_choice]

        # Create buffer to test tool call processing
        buffer = ChoiceBuffer(0)
        buffers.append(buffer)

        handler.process_chunk(mock_chunk, buffers)

        assert len(buffers) == 1


class TestDefaultAzureCleanup:
    """Test default_azure_cleanup function."""

    def test_default_azure_cleanup_basic(self):
        """Test basic default_azure_cleanup functionality."""
        mock_span = Mock()
        metadata: AzureMetadata = {
            "response_model": "gpt-4",
            "response_id": "test-id",
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "finish_reasons": ["stop"],
        }

        # Create a buffer with text content
        buffer = ChoiceBuffer(0)
        buffer.text_content = ["Hello", " world"]
        buffer.finish_reason = Mock()
        buffer.finish_reason.value = "stop"
        buffers = [buffer]

        default_azure_cleanup(mock_span, metadata, buffers)

        # Verify span.set_attributes was called
        mock_span.set_attributes.assert_called_once()

        # Verify span.add_event was called for each choice
        mock_span.add_event.assert_called()

    def test_default_azure_cleanup_with_tool_calls(self):
        """Test default_azure_cleanup with tool calls."""
        mock_span = Mock()
        metadata: AzureMetadata = {
            "response_model": "gpt-4",
            "response_id": "test-id",
        }

        # Create a buffer with tool calls
        buffer = ChoiceBuffer(0)

        # Mock tool call buffer
        mock_tool_buffer = Mock()
        mock_tool_buffer.tool_call_id = "call_123"
        mock_tool_buffer.function_name = "test_function"
        mock_tool_buffer.arguments = ["arg1", "arg2"]

        buffer.tool_calls_buffers = [mock_tool_buffer]
        buffer.finish_reason = Mock()
        buffer.finish_reason.value = "tool_calls"

        buffers = [buffer]

        default_azure_cleanup(mock_span, metadata, buffers)

        mock_span.set_attributes.assert_called_once()
        mock_span.add_event.assert_called()

    def test_default_azure_cleanup_empty_metadata(self):
        """Test default_azure_cleanup with empty metadata."""
        mock_span = Mock()
        metadata: AzureMetadata = {}
        buffers = []

        default_azure_cleanup(mock_span, metadata, buffers)

        mock_span.set_attributes.assert_called_once()
        # Should still call set_attributes even with empty metadata

    def test_default_azure_cleanup_mixed_content(self):
        """Test default_azure_cleanup with mixed content and tool calls."""
        mock_span = Mock()
        metadata: AzureMetadata = {"response_model": "gpt-4"}

        buffer = ChoiceBuffer(0)
        buffer.text_content = ["Hello"]

        # Mock tool call buffer
        mock_tool_buffer = Mock()
        mock_tool_buffer.tool_call_id = "call_456"
        mock_tool_buffer.function_name = "another_function"
        mock_tool_buffer.arguments = ["test_arg"]

        buffer.tool_calls_buffers = [mock_tool_buffer]
        buffer.finish_reason = Mock()
        buffer.finish_reason.value = "stop"

        buffers = [buffer]

        default_azure_cleanup(mock_span, metadata, buffers)

        mock_span.set_attributes.assert_called_once()
        mock_span.add_event.assert_called()


class TestGetToolCalls:
    """Test get_tool_calls function."""

    def test_get_tool_calls_from_dict(self):
        """Test get_tool_calls with dict message."""
        message = {
            "tool_calls": [
                {
                    "id": "call_123",
                    "type": "function",
                    "function": {"name": "test_func", "arguments": "test_args"},
                }
            ]
        }

        result = get_tool_calls(message)
        assert result is not None
        assert len(result) == 1
        assert result[0]["id"] == "call_123"
        assert result[0]["type"] == "function"
        assert result[0]["function"]["name"] == "test_func"
        assert result[0]["function"]["arguments"] == "test_args"

    def test_get_tool_calls_from_basemodel(self):
        """Test get_tool_calls with BaseModel message."""

        class MockToolCall(BaseModel):
            id: str
            type: str
            function: dict

        class MockMessage(BaseModel):
            tool_calls: list[MockToolCall]

        tool_call = MockToolCall(
            id="call_456", type="function", function={"name": "test_func", "arguments": "test_args"}
        )
        message = MockMessage(tool_calls=[tool_call])

        # Mock the function.model_dump method
        tool_call.function = Mock()
        tool_call.function.model_dump.return_value = {"name": "test_func", "arguments": "test_args"}

        result = get_tool_calls(message)
        assert result is not None
        assert len(result) == 1
        assert result[0]["id"] == "call_456"
        assert result[0]["type"] == "function"

    def test_get_tool_calls_none(self):
        """Test get_tool_calls with None tool_calls."""
        message = {"tool_calls": None}
        result = get_tool_calls(message)
        assert result is None

    def test_get_tool_calls_missing_function_dict(self):
        """Test get_tool_calls with missing function in dict."""
        message = {
            "tool_calls": [
                {
                    "id": "call_789",
                    "type": "function",
                    # Missing function key
                }
            ]
        }

        result = get_tool_calls(message)
        assert result is not None
        assert len(result) == 1
        assert result[0]["id"] == "call_789"
        assert result[0]["type"] == "function"
        assert "function" not in result[0]

    def test_get_tool_calls_partial_function_dict(self):
        """Test get_tool_calls with partial function data."""
        message = {
            "tool_calls": [
                {
                    "id": "call_abc",
                    "type": "function",
                    "function": {"name": "test_func"},  # Missing arguments
                }
            ]
        }

        result = get_tool_calls(message)
        assert result is not None
        assert len(result) == 1
        assert result[0]["function"]["name"] == "test_func"
        assert "arguments" not in result[0]["function"]


class TestSetMessageEvent:
    """Test set_message_event function."""

    def test_set_message_event_with_content(self):
        """Test set_message_event with content."""
        mock_span = Mock()
        message = {"role": "user", "content": "Hello world"}

        set_message_event(mock_span, message)

        mock_span.add_event.assert_called_once()
        call_args = mock_span.add_event.call_args
        assert call_args[0][0] == "gen_ai.user.message"
        assert call_args[1]["attributes"]["content"] == "Hello world"

    def test_set_message_event_with_non_string_content(self):
        """Test set_message_event with non-string content."""
        mock_span = Mock()
        message = {"role": "user", "content": {"type": "text", "text": "Hello"}}

        with patch("lilypad._opentelemetry._opentelemetry_azure.utils.json_dumps") as mock_json_dumps:
            mock_json_dumps.return_value = '{"type": "text", "text": "Hello"}'
            set_message_event(mock_span, message)

        mock_span.add_event.assert_called_once()
        mock_json_dumps.assert_called_once()

    def test_set_message_event_assistant_with_tool_calls(self):
        """Test set_message_event for assistant with tool calls."""
        mock_span = Mock()
        message = {
            "role": "assistant",
            "tool_calls": [
                {"id": "call_123", "type": "function", "function": {"name": "test_func", "arguments": "{}"}}
            ],
        }

        with patch("lilypad._opentelemetry._opentelemetry_azure.utils.json_dumps") as mock_json_dumps:
            mock_json_dumps.return_value = '[{"id": "call_123"}]'
            set_message_event(mock_span, message)

        mock_span.add_event.assert_called_once()
        call_args = mock_span.add_event.call_args
        assert call_args[0][0] == "gen_ai.assistant.message"
        assert "tool_calls" in call_args[1]["attributes"]

    def test_set_message_event_tool_role(self):
        """Test set_message_event for tool role."""
        mock_span = Mock()
        message = {"role": "tool", "tool_call_id": "call_456", "content": "result"}

        set_message_event(mock_span, message)

        mock_span.add_event.assert_called_once()
        call_args = mock_span.add_event.call_args
        assert call_args[0][0] == "gen_ai.tool.message"
        assert call_args[1]["attributes"]["id"] == "call_456"
        assert call_args[1]["attributes"]["content"] == "result"

    def test_set_message_event_no_role(self):
        """Test set_message_event with no role."""
        mock_span = Mock()
        message = {"content": "Hello"}

        set_message_event(mock_span, message)

        mock_span.add_event.assert_called_once()
        call_args = mock_span.add_event.call_args
        assert call_args[0][0] == "gen_ai..message"


class TestGetChoiceEvent:
    """Test get_choice_event function."""

    def test_get_choice_event_with_content(self):
        """Test get_choice_event with message content."""
        mock_message = Mock()
        mock_message.role = "assistant"
        mock_message.content = "Hello world"

        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_choice.index = 0
        mock_choice.finish_reason = Mock()
        mock_choice.finish_reason.value = "stop"

        with (
            patch("lilypad._opentelemetry._opentelemetry_azure.utils.get_tool_calls", return_value=None),
            patch("lilypad._opentelemetry._opentelemetry_azure.utils.json_dumps") as mock_json_dumps,
        ):
            mock_json_dumps.return_value = '{"role": "assistant", "content": "Hello world"}'

            result = get_choice_event(mock_choice)

        assert result["message"] == '{"role": "assistant", "content": "Hello world"}'
        assert result["index"] == 0
        assert result["finish_reason"] == "stop"

    def test_get_choice_event_with_tool_calls(self):
        """Test get_choice_event with tool calls."""
        mock_message = Mock()
        mock_message.role = "assistant"
        mock_message.content = None

        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_choice.index = 1
        mock_choice.finish_reason = Mock()
        mock_choice.finish_reason.value = "tool_calls"

        mock_tool_calls = [{"id": "call_123", "type": "function"}]

        with (
            patch("lilypad._opentelemetry._opentelemetry_azure.utils.get_tool_calls", return_value=mock_tool_calls),
            patch("lilypad._opentelemetry._opentelemetry_azure.utils.json_dumps") as mock_json_dumps,
        ):
            mock_json_dumps.return_value = '{"role": "assistant", "tool_calls": [{"id": "call_123"}]}'

            result = get_choice_event(mock_choice)

        assert result["index"] == 1
        assert result["finish_reason"] == "tool_calls"

    def test_get_choice_event_no_finish_reason(self):
        """Test get_choice_event with no finish reason."""
        mock_message = Mock()
        mock_message.role = "assistant"
        mock_message.content = "Hello"

        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_choice.index = 0
        mock_choice.finish_reason = None

        with (
            patch("lilypad._opentelemetry._opentelemetry_azure.utils.get_tool_calls", return_value=None),
            patch("lilypad._opentelemetry._opentelemetry_azure.utils.json_dumps") as mock_json_dumps,
        ):
            mock_json_dumps.return_value = '{"role": "assistant", "content": "Hello"}'

            result = get_choice_event(mock_choice)

        assert result["finish_reason"] == "none"


class TestSetResponseAttributes:
    """Test set_response_attributes function."""

    def test_set_response_attributes_complete(self):
        """Test set_response_attributes with complete response."""
        mock_span = Mock()

        # Mock choice with message
        mock_message = Mock()
        mock_message.role = "assistant"
        mock_message.content = "Hello"

        mock_choice = Mock()
        mock_choice.message = mock_message
        mock_choice.index = 0
        mock_choice.finish_reason = Mock()
        mock_choice.finish_reason.value = "stop"

        # Mock usage
        mock_usage = Mock()
        mock_usage.prompt_tokens = 10
        mock_usage.completion_tokens = 20

        # Mock response
        mock_response = Mock()
        mock_response.model = "gpt-4"
        mock_response.choices = [mock_choice]
        mock_response.id = "response-123"
        mock_response.usage = mock_usage

        with patch("lilypad._opentelemetry._opentelemetry_azure.utils.get_choice_event") as mock_get_choice:
            mock_get_choice.return_value = {"test": "attributes"}

            set_response_attributes(mock_span, mock_response)

        mock_span.set_attributes.assert_called_once()
        mock_span.add_event.assert_called_once()
        mock_get_choice.assert_called_once_with(mock_choice)

    def test_set_response_attributes_no_choices(self):
        """Test set_response_attributes with no choices."""
        mock_span = Mock()

        mock_response = Mock()
        mock_response.model = "gpt-4"
        mock_response.id = "response-456"
        # Use delattr to make choices attribute not exist (getattr will return None)
        if hasattr(mock_response, "choices"):
            delattr(mock_response, "choices")
        # Similarly for usage
        if hasattr(mock_response, "usage"):
            delattr(mock_response, "usage")

        set_response_attributes(mock_span, mock_response)

        mock_span.set_attributes.assert_called_once()

    def test_set_response_attributes_no_usage(self):
        """Test set_response_attributes with no usage information."""
        mock_span = Mock()

        mock_choice = Mock()
        mock_choice.finish_reason = Mock()
        mock_choice.finish_reason.value = "stop"

        mock_response = Mock()
        mock_response.model = "gpt-4"
        mock_response.choices = [mock_choice]
        mock_response.id = "response-789"

        # Remove usage attribute to make getattr return None
        if hasattr(mock_response, "usage"):
            delattr(mock_response, "usage")

        with patch("lilypad._opentelemetry._opentelemetry_azure.utils.get_choice_event") as mock_get_choice:
            mock_get_choice.return_value = {"test": "attributes"}

            set_response_attributes(mock_span, mock_response)

        mock_span.set_attributes.assert_called_once()
        mock_span.add_event.assert_called_once()

    def test_set_response_attributes_multiple_choices(self):
        """Test set_response_attributes with multiple choices."""
        mock_span = Mock()

        # Mock choices
        mock_choice1 = Mock()
        mock_choice1.finish_reason = Mock()
        mock_choice1.finish_reason.value = "stop"

        mock_choice2 = Mock()
        mock_choice2.finish_reason = Mock()
        mock_choice2.finish_reason.value = "length"

        mock_response = Mock()
        mock_response.model = "gpt-4"
        mock_response.choices = [mock_choice1, mock_choice2]
        mock_response.id = "response-multi"

        # Remove usage attribute to make getattr return None
        if hasattr(mock_response, "usage"):
            delattr(mock_response, "usage")

        with patch("lilypad._opentelemetry._opentelemetry_azure.utils.get_choice_event") as mock_get_choice:
            mock_get_choice.return_value = {"test": "attributes"}

            set_response_attributes(mock_span, mock_response)

        mock_span.set_attributes.assert_called_once()
        # Should be called once for each choice
        assert mock_span.add_event.call_count == 2
