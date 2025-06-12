"""Advanced tests to complete traces.py coverage."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from lilypad.traces import (
    Trace,
    AsyncTrace,
    Annotation,
    _get_trace_type,
)


class TestAdvancedTraces:
    """Tests for missing coverage in traces.py."""

    def test_trace_base_init(self):
        """Test _TraceBase initialization."""
        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        assert trace.response == "test"
        assert trace.function_uuid == "test-uuid"
        assert trace.formated_span_id == "000000000000007b"  # formatted span id for 123
        assert trace._flush is False

    def test_async_trace_base_init(self):
        """Test AsyncTrace initialization."""
        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        assert trace.response == "test"
        assert trace.function_uuid == "test-uuid"
        assert trace.formated_span_id == "000000000000007b"  # formatted span id for 123
        assert trace._flush is False

    @patch("lilypad.traces.get_tracer_provider")
    def test_trace_force_flush_success(self, mock_get_tracer):
        """Test successful force flush."""
        mock_tracer = Mock()
        mock_force_flush = Mock()
        mock_tracer.force_flush = mock_force_flush
        mock_get_tracer.return_value = mock_tracer

        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
        trace._force_flush()

        mock_force_flush.assert_called_once_with(timeout_millis=5000)
        assert trace._flush is True

    @patch("lilypad.traces.get_tracer_provider")
    def test_trace_force_flush_no_method(self, mock_get_tracer):
        """Test force flush when tracer has no force_flush method."""
        mock_tracer = Mock(spec=[])  # No methods
        mock_get_tracer.return_value = mock_tracer

        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
        trace._force_flush()

        # Should not raise an error, _flush remains False
        assert trace._flush is False

    def test_create_request_multiple_annotations(self):
        """Test _create_request with multiple annotations."""
        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        annotation1 = Annotation(data={"key1": "value1"}, label="pass", reasoning="First annotation", type="manual")
        annotation2 = Annotation(data={"key2": "value2"}, label="fail", reasoning="Second annotation", type="automatic")

        result = trace._create_request("project-id", "span-uuid", (annotation1, annotation2))

        assert len(result) == 2
        assert result[0].data == {"key1": "value1"}
        assert result[0].label == "pass"
        assert result[1].data == {"key2": "value2"}
        assert result[1].label == "fail"

    @patch("lilypad._utils.settings.get_settings")
    def test_trace_get_span_uuid_force_flush_called(self, mock_get_settings):
        """Test that _get_span_uuid calls _force_flush when _flush is False."""
        mock_settings = Mock()
        mock_settings.project_id = "project-123"
        mock_get_settings.return_value = mock_settings

        # Mock the span response
        mock_span = Mock()
        mock_span.span_id = "000000000000007b"
        mock_span.uuid_ = "span-uuid-123"

        mock_response = Mock()
        mock_response.items = [mock_span]

        mock_client = Mock()
        mock_client.projects.functions.spans.list_paginated.return_value = mock_response

        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        with patch.object(trace, "_force_flush") as mock_force_flush:
            result = trace._get_span_uuid(mock_client)

        # Should call _force_flush because _flush is False
        mock_force_flush.assert_called_once()
        assert result == "span-uuid-123"

    @pytest.mark.asyncio
    async def test_async_trace_get_span_uuid_force_flush_called(self):
        """Test that AsyncTrace._get_span_uuid calls _force_flush when _flush is False."""
        mock_settings = Mock()
        mock_settings.project_id = "project-123"

        # Mock the span response
        mock_span = Mock()
        mock_span.span_id = "000000000000007b"
        mock_span.uuid_ = "span-uuid-123"

        mock_response = Mock()
        mock_response.items = [mock_span]

        mock_client = Mock()
        mock_client.projects.functions.spans.list_paginated = AsyncMock(return_value=mock_response)

        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        with (
            patch.object(trace, "_force_flush") as mock_force_flush,
            patch("lilypad._utils.settings.get_settings", return_value=mock_settings),
        ):
            result = await trace._get_span_uuid(mock_client)

        # Should call _force_flush because _flush is False
        mock_force_flush.assert_called_once()
        assert result == "span-uuid-123"

    def test_trace_tag_early_return_no_tags(self):
        """Test that tag method returns early when no tags provided."""
        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        # Should return None without any client calls
        result = trace.tag()
        assert result is None

    @pytest.mark.asyncio
    async def test_async_trace_tag_early_return_no_tags(self):
        """Test that AsyncTrace tag method returns early when no tags provided."""
        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        # Should return None without any client calls
        result = await trace.tag()
        assert result is None

    def test_get_trace_type_with_function(self):
        """Test _get_trace_type with a function object."""
        mock_function = Mock()
        result = _get_trace_type(mock_function)
        assert result == "function"

    def test_get_trace_type_with_none(self):
        """Test _get_trace_type with None."""
        result = _get_trace_type(None)
        assert result == "trace"

    @patch("lilypad._utils.settings.get_settings")
    @patch("lilypad._utils.client.get_sync_client")
    def test_trace_annotate_valid_flow(self, mock_get_client, mock_get_settings):
        """Test the complete annotate flow with proper mocking."""
        # Setup settings
        mock_settings = Mock()
        mock_settings.project_id = "project-123"
        mock_settings.api_key = "api-key"
        mock_get_settings.return_value = mock_settings

        # Setup client
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")

        annotation = Annotation(data={"test": "data"}, label="pass", reasoning="Test annotation", type="manual")

        # Mock _get_span_uuid to return a UUID
        with patch.object(trace, "_get_span_uuid", return_value="span-uuid-123"):
            trace.annotate(annotation)

        # Verify client was called with correct parameters
        mock_client.ee.projects.annotations.create.assert_called_once()
        call_kwargs = mock_client.ee.projects.annotations.create.call_args[1]
        assert call_kwargs["project_uuid"] == "project-123"
        assert len(call_kwargs["request"]) == 1

    @pytest.mark.asyncio
    @patch("lilypad._utils.settings.get_settings")
    @patch("lilypad._utils.client.get_async_client")
    async def test_async_trace_annotate_valid_flow(self, mock_get_client, mock_get_settings):
        """Test the complete AsyncTrace annotate flow with proper mocking."""
        # Setup settings
        mock_settings = Mock()
        mock_settings.project_id = "project-123"
        mock_settings.api_key = "api-key"
        mock_get_settings.return_value = mock_settings

        # Setup client
        mock_client = Mock()
        mock_client.ee.projects.annotations.create = AsyncMock()
        mock_get_client.return_value = mock_client

        trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")

        annotation = Annotation(data={"test": "data"}, label="pass", reasoning="Test annotation", type="manual")

        # Mock _get_span_uuid to return a UUID
        with patch.object(trace, "_get_span_uuid", return_value="span-uuid-123"):
            await trace.annotate(annotation)

        # Verify client was called with correct parameters
        mock_client.ee.projects.annotations.create.assert_called_once()

    def test_annotation_creation(self):
        """Test Annotation model creation."""
        annotation = Annotation(
            data={"key": "value", "nested": {"inner": "data"}},
            label="pass",
            reasoning="This is a detailed reasoning",
            type="manual",
        )

        assert annotation.data == {"key": "value", "nested": {"inner": "data"}}
        assert annotation.label == "pass"
        assert annotation.reasoning == "This is a detailed reasoning"
        assert annotation.type == "manual"

    def test_annotation_with_none_values(self):
        """Test Annotation model with None values."""
        annotation = Annotation(data=None, label=None, reasoning=None, type=None)

        assert annotation.data is None
        assert annotation.label is None
        assert annotation.reasoning is None
        assert annotation.type is None
