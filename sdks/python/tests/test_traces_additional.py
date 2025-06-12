"""Additional tests for traces.py to improve coverage."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from lilypad.traces import (
    _get_trace_type,
    Annotation,
    Trace,
    _TraceBase,
)
from lilypad.generated.types.function_public import FunctionPublic
from lilypad.generated.types.annotation_create import AnnotationCreate
from lilypad.exceptions import SpanNotFoundError


class TestTraceTypeFunction:
    """Test _get_trace_type function."""

    def test_get_trace_type_with_function(self):
        """Test _get_trace_type returns 'function' when function is provided."""
        mock_function = Mock(spec=FunctionPublic)
        result = _get_trace_type(mock_function)
        assert result == "function"

    def test_get_trace_type_without_function(self):
        """Test _get_trace_type returns 'trace' when function is None."""
        result = _get_trace_type(None)
        assert result == "trace"


class TestAnnotation:
    """Test Annotation model."""

    def test_annotation_creation_minimal(self):
        """Test Annotation creation with minimal fields."""
        annotation = Annotation(data=None, label=None, reasoning=None, type=None)

        assert annotation.data is None
        assert annotation.label is None
        assert annotation.reasoning is None
        assert annotation.type is None

    def test_annotation_creation_full(self):
        """Test Annotation creation with all fields."""
        data = {"key": "value"}
        reasoning = "This is the reasoning"

        annotation = Annotation(data=data, label="pass", reasoning=reasoning, type="manual")

        assert annotation.data == data
        assert annotation.label == "pass"
        assert annotation.reasoning == reasoning
        assert annotation.type == "manual"


class TestTraceBase:
    """Test _TraceBase class."""

    def test_trace_base_init(self):
        """Test _TraceBase initialization."""
        response = {"result": "success"}
        span_id = 12345
        function_uuid = "func-uuid-123"

        trace_base = _TraceBase(response, span_id, function_uuid)

        assert trace_base.response == response
        assert trace_base.function_uuid == function_uuid
        assert trace_base.formated_span_id == "0000000000003039"  # format_span_id(12345)
        assert trace_base._flush is False

    @patch("lilypad.traces.get_tracer_provider")
    def test_force_flush_with_force_flush_method(self, mock_get_tracer_provider):
        """Test _force_flush when tracer has force_flush method."""
        mock_tracer = Mock()
        mock_force_flush = Mock()
        mock_tracer.force_flush = mock_force_flush
        mock_get_tracer_provider.return_value = mock_tracer

        trace_base = _TraceBase("response", 123, "uuid")
        trace_base._force_flush()

        mock_force_flush.assert_called_once_with(timeout_millis=5000)
        assert trace_base._flush is True

    @patch("lilypad.traces.get_tracer_provider")
    def test_force_flush_without_force_flush_method(self, mock_get_tracer_provider):
        """Test _force_flush when tracer doesn't have force_flush method."""
        mock_tracer = Mock()
        del mock_tracer.force_flush  # Ensure force_flush doesn't exist
        mock_get_tracer_provider.return_value = mock_tracer

        trace_base = _TraceBase("response", 123, "uuid")
        trace_base._force_flush()

        # Should not raise exception, _flush should remain False
        assert trace_base._flush is False

    def test_create_request(self):
        """Test _create_request method."""
        trace_base = _TraceBase("response", 123, "func-uuid")

        annotation1 = Annotation(data={"key1": "value1"}, label="pass", reasoning="Good result", type="manual")
        annotation2 = Annotation(data={"key2": "value2"}, label="fail", reasoning="Bad result", type="verified")

        annotations = (annotation1, annotation2)
        project_id = "project-123"
        span_uuid = "span-uuid-456"

        result = trace_base._create_request(project_id, span_uuid, annotations)

        assert len(result) == 2
        assert all(isinstance(item, AnnotationCreate) for item in result)

        # Check first annotation
        assert result[0].data == {"key1": "value1"}
        assert result[0].function_uuid == "func-uuid"
        assert result[0].span_uuid == "span-uuid-456"
        assert result[0].label == "pass"
        assert result[0].reasoning == "Good result"
        assert result[0].type == "manual"
        assert result[0].project_uuid == "project-123"

        # Check second annotation
        assert result[1].data == {"key2": "value2"}
        assert result[1].label == "fail"


class TestTrace:
    """Test Trace class."""

    def test_trace_inheritance(self):
        """Test that Trace inherits from _TraceBase."""
        trace = Trace("response", 123, "uuid")
        assert isinstance(trace, _TraceBase)

    @patch("lilypad.traces.get_settings")
    def test_get_span_uuid_success(self, mock_get_settings):
        """Test _get_span_uuid successfully finds span."""
        mock_settings = Mock()
        mock_settings.project_id = "project-123"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_span = Mock()
        mock_span.span_id = "0000000000003039"  # format_span_id(12345)
        mock_span.uuid_ = "span-uuid-found"

        mock_response = Mock()
        mock_response.items = [mock_span]
        mock_client.projects.functions.spans.list_paginated.return_value = mock_response

        trace = Trace("response", 12345, "func-uuid")
        result = trace._get_span_uuid(mock_client)

        assert result == "span-uuid-found"
        mock_client.projects.functions.spans.list_paginated.assert_called_once_with(
            project_uuid="project-123", function_uuid="func-uuid"
        )

    @patch("lilypad.traces.get_settings")
    def test_get_span_uuid_not_found(self, mock_get_settings):
        """Test _get_span_uuid when span is not found."""
        mock_settings = Mock()
        mock_settings.project_id = "project-123"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_span = Mock()
        mock_span.span_id = "different-span-id"
        mock_span.uuid_ = "span-uuid-different"

        mock_response = Mock()
        mock_response.items = [mock_span]
        mock_client.projects.functions.spans.list_paginated.return_value = mock_response

        trace = Trace("response", 12345, "func-uuid")
        result = trace._get_span_uuid(mock_client)

        assert result is None

    @patch("lilypad.traces.get_settings")
    def test_get_span_uuid_empty_response(self, mock_get_settings):
        """Test _get_span_uuid when response has no items."""
        mock_settings = Mock()
        mock_settings.project_id = "project-123"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_response = Mock()
        mock_response.items = []
        mock_client.projects.functions.spans.list_paginated.return_value = mock_response

        trace = Trace("response", 12345, "func-uuid")
        result = trace._get_span_uuid(mock_client)

        assert result is None

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad.traces.get_settings")
    def test_annotate_success(self, mock_get_settings, mock_get_sync_client):
        """Test successful annotation."""
        mock_settings = Mock()
        mock_settings.api_key = "api-key-123"
        mock_settings.project_id = "project-123"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_get_sync_client.return_value = mock_client

        # Mock successful span lookup
        trace = Trace("response", 12345, "func-uuid")
        trace._get_span_uuid = Mock(return_value="span-uuid-found")

        annotation = Annotation(data={"key": "value"}, label="pass", reasoning="Good", type="manual")

        trace.annotate(annotation)

        # Verify client calls
        mock_get_sync_client.assert_called_once_with(api_key="api-key-123")
        trace._get_span_uuid.assert_called_once_with(mock_client)
        mock_client.ee.projects.annotations.create.assert_called_once()

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad.traces.get_settings")
    def test_annotate_no_annotations(self, mock_get_settings, mock_get_sync_client):
        """Test annotate raises error when no annotations provided."""
        trace = Trace("response", 12345, "func-uuid")

        with pytest.raises(ValueError, match="At least one annotation must be provided"):
            trace.annotate()

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad.traces.get_settings")
    def test_annotate_span_not_found(self, mock_get_settings, mock_get_sync_client):
        """Test annotate raises error when span is not found."""
        mock_settings = Mock()
        mock_settings.api_key = "api-key-123"
        mock_settings.project_id = "project-123"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_get_sync_client.return_value = mock_client

        trace = Trace("response", 12345, "func-uuid")
        trace._get_span_uuid = Mock(return_value=None)

        annotation = Annotation(data={}, label=None, reasoning=None, type=None)

        with pytest.raises(SpanNotFoundError, match="Cannot annotate: span not found for function func-uuid"):
            trace.annotate(annotation)

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad.traces.get_settings")
    def test_assign_success(self, mock_get_settings, mock_get_sync_client):
        """Test successful assignment."""
        mock_settings = Mock()
        mock_settings.api_key = "api-key-123"
        mock_settings.project_id = "project-123"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_get_sync_client.return_value = mock_client

        trace = Trace("response", 12345, "func-uuid")
        trace._get_span_uuid = Mock(return_value="span-uuid-found")

        trace.assign("user@example.com", "admin@example.com")

        # Verify client calls
        mock_get_sync_client.assert_called_once_with(api_key="api-key-123")
        trace._get_span_uuid.assert_called_once_with(mock_client)

        # Verify annotation creation call
        call_args = mock_client.ee.projects.annotations.create.call_args
        assert call_args[1]["project_uuid"] == "project-123"
        assert len(call_args[1]["request"]) == 1
        assert call_args[1]["request"][0].assignee_email == ["user@example.com", "admin@example.com"]

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad.traces.get_settings")
    def test_assign_no_emails(self, mock_get_settings, mock_get_sync_client):
        """Test assign raises error when no emails provided."""
        trace = Trace("response", 12345, "func-uuid")

        with pytest.raises(ValueError, match="At least one email address must be provided"):
            trace.assign()

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad.traces.get_settings")
    def test_assign_span_not_found(self, mock_get_settings, mock_get_sync_client):
        """Test assign raises error when span is not found."""
        mock_settings = Mock()
        mock_settings.api_key = "api-key-123"
        mock_settings.project_id = "project-123"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_get_sync_client.return_value = mock_client

        trace = Trace("response", 12345, "func-uuid")
        trace._get_span_uuid = Mock(return_value=None)

        with pytest.raises(SpanNotFoundError, match="Cannot assign: span not found for function func-uuid"):
            trace.assign("user@example.com")

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad.traces.get_settings")
    def test_tag_success(self, mock_get_settings, mock_get_sync_client):
        """Test successful tagging."""
        mock_settings = Mock()
        mock_settings.api_key = "api-key-123"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_get_sync_client.return_value = mock_client

        trace = Trace("response", 12345, "func-uuid")
        trace._get_span_uuid = Mock(return_value="span-uuid-found")

        result = trace.tag("tag1", "tag2", "tag3")

        # Verify client calls
        mock_get_sync_client.assert_called_once_with(api_key="api-key-123")
        trace._get_span_uuid.assert_called_once_with(mock_client)
        mock_client.spans.update.assert_called_once_with(
            span_uuid="span-uuid-found", tags_by_name=["tag1", "tag2", "tag3"]
        )
        assert result is None

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad.traces.get_settings")
    def test_tag_no_tags(self, mock_get_settings, mock_get_sync_client):
        """Test tag returns None when no tags provided."""
        trace = Trace("response", 12345, "func-uuid")

        result = trace.tag()

        assert result is None
        # Should not make any client calls
        mock_get_sync_client.assert_not_called()

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad.traces.get_settings")
    def test_tag_span_not_found(self, mock_get_settings, mock_get_sync_client):
        """Test tag raises error when span is not found."""
        mock_settings = Mock()
        mock_settings.api_key = "api-key-123"
        mock_get_settings.return_value = mock_settings

        mock_client = Mock()
        mock_get_sync_client.return_value = mock_client

        trace = Trace("response", 12345, "func-uuid")
        trace._get_span_uuid = Mock(return_value=None)

        with pytest.raises(SpanNotFoundError, match="Cannot tag: span not found for function func-uuid"):
            trace.tag("tag1", "tag2")
