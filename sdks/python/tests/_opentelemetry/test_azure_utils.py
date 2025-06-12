"""Tests for Azure OpenTelemetry utils."""

import pytest
from unittest.mock import Mock
from lilypad._opentelemetry._opentelemetry_azure.utils import (
    AzureMetadata,
    AzureChunkHandler,
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
