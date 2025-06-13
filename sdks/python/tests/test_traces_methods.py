"""Unit tests for Trace and AsyncTrace methods."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from lilypad.traces import (
    Trace,
    AsyncTrace,
    Annotation,
)
from lilypad.exceptions import SpanNotFoundError


class TestTrace:
    """Test class for Trace methods."""

    def test_force_flush(self):
        """Test _force_flush method."""
        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        # Mock tracer with force_flush method
        mock_tracer = Mock()
        mock_force_flush = Mock()
        mock_tracer.force_flush = mock_force_flush

        with patch("lilypad.traces.get_tracer_provider", return_value=mock_tracer):
            trace._force_flush()
            mock_force_flush.assert_called_once_with(timeout_millis=5000)
            assert trace._flush is True

    def test_force_flush_no_method(self):
        """Test _force_flush when tracer has no force_flush method."""
        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        # Mock tracer without force_flush method
        mock_tracer = Mock(spec=[])  # Empty spec means no methods

        with patch("lilypad.traces.get_tracer_provider", return_value=mock_tracer):
            trace._force_flush()
            # Should not raise an error, but _flush should not be set
            assert trace._flush is False

    def test_create_request(self):
        """Test _create_request method."""
        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        annotation = Annotation(data={"key": "value"}, label="pass", reasoning="Test reasoning", type="manual")

        result = trace._create_request("project-id", "span-uuid", (annotation,))

        assert len(result) == 1
        assert result[0].data == {"key": "value"}
        assert result[0].label == "pass"
        assert result[0].reasoning == "Test reasoning"
        assert result[0].type == "manual"
        assert result[0].function_uuid == "test-uuid"
        assert result[0].span_uuid == "span-uuid"
        assert result[0].project_uuid == "project-id"

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad._utils.settings.get_settings")
    def test_get_span_uuid_found(self, mock_get_settings, mock_get_client):
        """Test _get_span_uuid when span is found."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_get_settings.return_value = mock_settings

        mock_span = Mock()
        mock_span.span_id = "000000000000007b"  # This is the formatted span_id for 123
        mock_span.uuid_ = "span-uuid-123"

        mock_response = Mock()
        mock_response.items = [mock_span]

        mock_client = Mock()
        mock_client.projects.functions.spans.list_paginated.return_value = mock_response
        mock_get_client.return_value = mock_client

        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        # Mock _force_flush to avoid tracer dependencies
        with patch.object(trace, "_force_flush"):
            result = trace._get_span_uuid(mock_client)

        assert result == "span-uuid-123"

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad._utils.settings.get_settings")
    def test_get_span_uuid_not_found(self, mock_get_settings, mock_get_client):
        """Test _get_span_uuid when span is not found."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_get_settings.return_value = mock_settings

        mock_span = Mock()
        mock_span.span_id = "different-id"  # Different from what we're looking for
        mock_span.uuid_ = "different-uuid"

        mock_response = Mock()
        mock_response.items = [mock_span]

        mock_client = Mock()
        mock_client.projects.functions.spans.list_paginated.return_value = mock_response
        mock_get_client.return_value = mock_client

        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        # Mock _force_flush to avoid tracer dependencies
        with patch.object(trace, "_force_flush"):
            result = trace._get_span_uuid(mock_client)

        assert result is None

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad._utils.settings.get_settings")
    def test_annotate_success(self, mock_get_settings, mock_get_client):
        """Test annotate method with successful annotation."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_settings.api_key = "test-key"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        annotation = Annotation(data={"key": "value"}, label="pass", reasoning="Test reasoning", type="manual")

        # Mock _get_span_uuid to return a span UUID
        with (
            patch.object(trace, "_get_span_uuid", return_value="span-uuid-123"),
            patch("lilypad.traces.get_settings", return_value=mock_settings),
        ):
            trace.annotate(annotation)

        # Verify the client call
        mock_client.ee.projects.annotations.create.assert_called_once()
        call_args = mock_client.ee.projects.annotations.create.call_args
        assert call_args[1]["project_uuid"] == "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        assert len(call_args[1]["request"]) == 1

    def test_annotate_no_annotations(self):
        """Test annotate method with no annotations provided."""
        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        with pytest.raises(ValueError, match="At least one annotation must be provided"):
            trace.annotate()

    def test_annotate_span_not_found(self):
        """Test annotate method when span is not found."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_settings.api_key = "test-key"

        mock_client = Mock()

        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        annotation = Annotation(data={"key": "value"}, label="pass", reasoning="Test reasoning", type="manual")

        # Mock all dependencies with None span uuid
        with (
            patch.object(trace, "_get_span_uuid", return_value=None),
            patch("lilypad._utils.settings.get_settings", return_value=mock_settings),
            patch("lilypad._utils.client.get_sync_client", return_value=mock_client),
            pytest.raises(SpanNotFoundError, match="Cannot annotate: span not found for function test-uuid"),
        ):
            trace.annotate(annotation)

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad._utils.settings.get_settings")
    def test_assign_success(self, mock_get_settings, mock_get_client):
        """Test assign method with successful assignment."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_settings.api_key = "test-key"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        # Mock _get_span_uuid to return a span UUID
        with (
            patch.object(trace, "_get_span_uuid", return_value="span-uuid-123"),
            patch("lilypad.traces.get_settings", return_value=mock_settings),
        ):
            trace.assign("user@example.com", "user2@example.com")

        # Verify the client call
        mock_client.ee.projects.annotations.create.assert_called_once()
        call_args = mock_client.ee.projects.annotations.create.call_args
        assert call_args[1]["project_uuid"] == "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        assert len(call_args[1]["request"]) == 1
        assert call_args[1]["request"][0].assignee_email == ["user@example.com", "user2@example.com"]

    def test_assign_no_emails(self):
        """Test assign method with no email addresses provided."""
        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        with pytest.raises(ValueError, match="At least one email address must be provided"):
            trace.assign()

    def test_assign_span_not_found(self):
        """Test assign method when span is not found."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_settings.api_key = "test-key"

        mock_client = Mock()

        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        # Mock all dependencies with None span uuid
        with (
            patch.object(trace, "_get_span_uuid", return_value=None),
            patch("lilypad._utils.settings.get_settings", return_value=mock_settings),
            patch("lilypad._utils.client.get_sync_client", return_value=mock_client),
            pytest.raises(SpanNotFoundError, match="Cannot assign: span not found for function test-uuid"),
        ):
            trace.assign("user@example.com")

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad._utils.settings.get_settings")
    def test_tag_success(self, mock_get_settings, mock_get_client):
        """Test tag method with successful tagging."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_settings.api_key = "test-key"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        # Mock _get_span_uuid to return a span UUID
        with patch.object(trace, "_get_span_uuid", return_value="span-uuid-123"):
            result = trace.tag("tag1", "tag2", "tag3")

        # Verify the client call
        mock_client.spans.update.assert_called_once_with(
            span_uuid="span-uuid-123", tags_by_name=["tag1", "tag2", "tag3"]
        )
        assert result is None

    def test_tag_no_tags(self):
        """Test tag method with no tags provided."""
        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        result = trace.tag()

        assert result is None
        # Client should not be called

    def test_tag_span_not_found(self):
        """Test tag method when span is not found."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_settings.api_key = "test-key"

        mock_client = Mock()

        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        # Mock all dependencies with None span uuid
        with (
            patch.object(trace, "_get_span_uuid", return_value=None),
            patch("lilypad._utils.settings.get_settings", return_value=mock_settings),
            patch("lilypad._utils.client.get_sync_client", return_value=mock_client),
            pytest.raises(SpanNotFoundError, match="Cannot tag: span not found for function test-uuid"),
        ):
            trace.tag("tag1", "tag2")


class TestAsyncTrace:
    """Test class for AsyncTrace methods."""

    @pytest.mark.asyncio
    @patch("lilypad._utils.settings.get_settings")
    async def test_get_span_uuid_found(self, mock_get_settings):
        """Test _get_span_uuid when span is found."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_get_settings.return_value = mock_settings

        mock_span = Mock()
        mock_span.span_id = "000000000000007b"  # This is the formatted span_id for 123
        mock_span.uuid_ = "span-uuid-123"

        mock_response = Mock()
        mock_response.items = [mock_span]

        mock_client = Mock()
        mock_client.projects.functions.spans.list_paginated = AsyncMock(return_value=mock_response)

        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        # Mock _force_flush
        with patch.object(trace, "_force_flush"):
            result = await trace._get_span_uuid(mock_client)

        assert result == "span-uuid-123"

    @pytest.mark.asyncio
    @patch("lilypad._utils.settings.get_settings")
    async def test_get_span_uuid_not_found(self, mock_get_settings):
        """Test _get_span_uuid when span is not found."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_get_settings.return_value = mock_settings

        mock_span = Mock()
        mock_span.span_id = "different-id"  # Different from what we're looking for
        mock_span.uuid_ = "different-uuid"

        mock_response = Mock()
        mock_response.items = [mock_span]

        mock_client = Mock()
        mock_client.projects.functions.spans.list_paginated = AsyncMock(return_value=mock_response)

        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        # Mock _force_flush
        with patch.object(trace, "_force_flush"):
            result = await trace._get_span_uuid(mock_client)

        assert result is None

    @pytest.mark.asyncio
    @patch("lilypad.traces.get_async_client")
    @patch("lilypad._utils.settings.get_settings")
    async def test_annotate_success(self, mock_get_settings, mock_get_client):
        """Test annotate method with successful annotation."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_settings.api_key = "test-key"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.ee.projects.annotations.create = AsyncMock()
        mock_get_client.return_value = mock_client

        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        annotation = Annotation(data={"key": "value"}, label="pass", reasoning="Test reasoning", type="manual")

        # Mock _get_span_uuid to return a span UUID
        with patch.object(trace, "_get_span_uuid", return_value="span-uuid-123"):
            await trace.annotate(annotation)

        # Verify the client call
        mock_client.ee.projects.annotations.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_annotate_no_annotations(self):
        """Test annotate method with no annotations provided."""
        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        with pytest.raises(ValueError, match="At least one annotation must be provided"):
            await trace.annotate()

    @pytest.mark.asyncio
    async def test_annotate_span_not_found(self):
        """Test annotate method when span is not found."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_settings.api_key = "test-key"

        mock_client = Mock()

        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        annotation = Annotation(data={"key": "value"}, label="pass", reasoning="Test reasoning", type="manual")

        # Mock dependencies with None span uuid
        with (
            patch.object(trace, "_get_span_uuid", return_value=None),
            patch("lilypad._utils.settings.get_settings", return_value=mock_settings),
            patch("lilypad._utils.client.get_async_client", return_value=mock_client),
            pytest.raises(SpanNotFoundError, match="Cannot annotate: span not found for function test-uuid"),
        ):
            await trace.annotate(annotation)

    @pytest.mark.asyncio
    @patch("lilypad.traces.get_async_client")
    @patch("lilypad._utils.settings.get_settings")
    async def test_assign_success(self, mock_get_settings, mock_get_client):
        """Test assign method with successful assignment."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_settings.api_key = "test-key"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.ee.projects.annotations.create = AsyncMock()
        mock_get_client.return_value = mock_client

        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        # Mock _get_span_uuid to return a span UUID
        with patch.object(trace, "_get_span_uuid", return_value="span-uuid-123"):
            await trace.assign("user@example.com", "user2@example.com")

        # Verify the client call
        mock_client.ee.projects.annotations.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_assign_no_emails(self):
        """Test assign method with no email addresses provided."""
        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        with pytest.raises(ValueError, match="At least one email address must be provided"):
            await trace.assign()

    @pytest.mark.asyncio
    async def test_assign_span_not_found(self):
        """Test assign method when span is not found."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_settings.api_key = "test-key"

        mock_client = Mock()

        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        # Mock dependencies with None span uuid
        with (
            patch.object(trace, "_get_span_uuid", return_value=None),
            patch("lilypad._utils.settings.get_settings", return_value=mock_settings),
            patch("lilypad._utils.client.get_async_client", return_value=mock_client),
            pytest.raises(SpanNotFoundError, match="Cannot assign: span not found for function test-uuid"),
        ):
            await trace.assign("user@example.com")

    @pytest.mark.asyncio
    @patch("lilypad.traces.get_async_client")
    @patch("lilypad._utils.settings.get_settings")
    async def test_tag_success(self, mock_get_settings, mock_get_client):
        """Test tag method with successful tagging."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_settings.api_key = "test-key"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_client.spans.update = AsyncMock()
        mock_get_client.return_value = mock_client

        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        # Mock _get_span_uuid to return a span UUID
        with patch.object(trace, "_get_span_uuid", return_value="span-uuid-123"):
            result = await trace.tag("tag1", "tag2", "tag3")

        # Verify the client call
        mock_client.spans.update.assert_called_once_with(
            span_uuid="span-uuid-123", tags_by_name=["tag1", "tag2", "tag3"]
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_tag_no_tags(self):
        """Test tag method with no tags provided."""
        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        result = await trace.tag()

        assert result is None
        # Client should not be called

    @pytest.mark.asyncio
    async def test_tag_span_not_found(self):
        """Test tag method when span is not found."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_settings.api_key = "test-key"

        mock_client = Mock()

        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        # Mock dependencies with None span uuid
        with (
            patch.object(trace, "_get_span_uuid", return_value=None),
            patch("lilypad._utils.settings.get_settings", return_value=mock_settings),
            patch("lilypad._utils.client.get_async_client", return_value=mock_client),
            pytest.raises(SpanNotFoundError, match="Cannot tag: span not found for function test-uuid"),
        ):
            await trace.tag("tag1", "tag2")
