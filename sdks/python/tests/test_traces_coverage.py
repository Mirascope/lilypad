"""Tests to improve coverage for traces.py missing lines."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from lilypad.traces import (
    _get_trace_type,
    Trace,
    AsyncTrace,
    trace,
    Annotation,
)
from lilypad.generated.types.function_public import FunctionPublic


def test_get_trace_type_with_function():
    """Test _get_trace_type when function is provided (lines 71-72)."""
    mock_function = Mock(spec=FunctionPublic)
    result = _get_trace_type(mock_function)
    assert result == "function"


def test_get_trace_type_with_none():
    """Test _get_trace_type when function is None (line 73)."""
    result = _get_trace_type(None)
    assert result == "trace"


def test_trace_force_flush_with_flush_method():
    """Test _force_flush when tracer has force_flush method (lines 100-101)."""
    trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
    
    # Mock tracer with force_flush method
    mock_tracer = Mock()
    mock_force_flush = Mock()
    mock_tracer.force_flush = mock_force_flush
    
    with patch("lilypad.traces.get_tracer_provider", return_value=mock_tracer):
        trace._force_flush()
        mock_force_flush.assert_called_once_with(timeout_millis=5000)
        assert trace._flush is True


def test_trace_create_request_multiple_annotations():
    """Test _create_request with multiple annotations (line 106)."""
    trace = Trace(response="test", span_id=123, function_uuid="test-func-uuid")
    
    annotation1 = Annotation(data={"key1": "value1"}, label="pass", reasoning="Test 1", type="manual")
    annotation2 = Annotation(data={"key2": "value2"}, label="fail", reasoning="Test 2", type="manual")
    
    result = trace._create_request("project-id", "span-uuid", (annotation1, annotation2))
    
    assert len(result) == 2
    assert result[0].data == {"key1": "value1"}
    assert result[0].label == "pass"
    assert result[1].data == {"key2": "value2"}
    assert result[1].label == "fail"


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_sync_client")
def test_trace_get_span_uuid_with_flush_false(mock_get_client, mock_get_settings):
    """Test _get_span_uuid when _flush is False (lines 152-153)."""
    # Setup mocks
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    mock_response = Mock()
    mock_response.items = []
    mock_client = Mock()
    mock_client.projects.functions.spans.list_paginated.return_value = mock_response
    mock_get_client.return_value = mock_client
    
    trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
    assert trace._flush is False  # Initial state
    
    with patch.object(trace, "_force_flush") as mock_force_flush:
        result = trace._get_span_uuid(mock_client)
        
        # Should call _force_flush because _flush is False
        mock_force_flush.assert_called_once()
        assert result is None


def test_trace_version_method_not_found_error():
    """Test versioning when function not found raises RemoteFunctionError."""
    from lilypad.generated.errors.not_found_error import NotFoundError
    from lilypad.exceptions import RemoteFunctionError
    
    @trace(versioning="automatic")
    def test_function(x: int) -> int:
        return x * 2
    
    # Mock to raise NotFoundError
    with (
        patch("lilypad.traces.get_function_by_version_sync", side_effect=NotFoundError("Function not found")),
        patch("lilypad.traces.get_sync_client") as mock_client,
        patch("lilypad.traces.get_settings") as mock_settings,
    ):
        mock_settings.return_value.api_key = "test-key"
        mock_client.return_value = Mock()
        
        # This should raise RemoteFunctionError when NotFoundError occurs
        with pytest.raises(RemoteFunctionError):
            test_function.version(1)(5)


def test_trace_remote_method_not_found_error():
    """Test remote method when function not found raises RemoteFunctionError."""
    from lilypad.generated.errors.not_found_error import NotFoundError
    from lilypad.exceptions import RemoteFunctionError
    
    @trace(versioning="automatic")
    def test_function(x: int) -> int:
        return x * 2
    
    # Mock to raise NotFoundError
    with (
        patch("lilypad.traces.get_deployed_function_sync", side_effect=NotFoundError("Function not found")),
        patch("lilypad.traces.get_sync_client") as mock_client,
        patch("lilypad.traces.get_settings") as mock_settings,
    ):
        mock_settings.return_value.api_key = "test-key"
        mock_client.return_value = Mock()
        
        # This should raise RemoteFunctionError when NotFoundError occurs
        with pytest.raises(RemoteFunctionError):
            test_function.remote()(5)


def test_trace_assign_empty_emails_error():
    """Test assign method with empty emails (line 215)."""
    trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
    
    # Should raise ValueError when no emails provided
    with pytest.raises(ValueError, match="At least one email address must be provided"):
        trace.assign()


def test_trace_annotate_empty_annotations_error():
    """Test annotate method with empty annotations."""
    trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
    
    # Should raise ValueError when no annotations provided
    with pytest.raises(ValueError, match="At least one annotation must be provided"):
        trace.annotate()


@patch("lilypad.traces.get_settings")
def test_trace_tag_early_return_no_tags(mock_get_settings):
    """Test tag method early return when no tags provided."""
    trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
    
    # Should return early when no tags provided
    result = trace.tag()
    
    # Should not call get_settings since it returns early
    mock_get_settings.assert_not_called()
    assert result is None


def test_annotation_model_creation():
    """Test Annotation model creation with various fields."""
    # Test with all fields
    annotation = Annotation(
        data={"key": "value"},
        label="pass",
        reasoning="Test reasoning",
        type="manual"
    )
    assert annotation.data == {"key": "value"}
    assert annotation.label == "pass"
    assert annotation.reasoning == "Test reasoning"
    assert annotation.type == "manual"
    
    # Test with minimal fields
    annotation_minimal = Annotation(
        data=None,
        label=None,
        reasoning=None,
        type="manual"
    )
    assert annotation_minimal.data is None
    assert annotation_minimal.label is None
    assert annotation_minimal.reasoning is None
    assert annotation_minimal.type == "manual"


def test_trace_decorator_with_disabled_recording():
    """Test trace decorator when recording is disabled."""
    from lilypad.traces import disable_recording, enable_recording
    
    # Disable recording
    disable_recording()
    
    try:
        @trace(versioning="automatic")
        def test_function(x: int) -> int:
            return x * 2
        
        # Function should still work but not register
        result = test_function(5)
        assert result == 10
        
    finally:
        # Re-enable recording for other tests
        enable_recording()


def test_async_trace_force_flush():
    """Test AsyncTrace _force_flush method is same as sync version."""
    trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")
    
    # Mock tracer with force_flush method
    mock_tracer = Mock()
    mock_force_flush = Mock()
    mock_tracer.force_flush = mock_force_flush
    
    with patch("lilypad.traces.get_tracer_provider", return_value=mock_tracer):
        # AsyncTrace._force_flush is same as sync version since it's inherited
        trace._force_flush()
        mock_force_flush.assert_called_once_with(timeout_millis=5000)
        assert trace._flush is True


def test_trace_get_span_uuid_success():
    """Test _get_span_uuid when span is found (lines 167-168)."""
    from opentelemetry.trace import format_span_id
    
    span_id = 123
    formatted_span_id = format_span_id(span_id)
    
    mock_span = Mock()
    mock_span.uuid_ = "test-span-uuid"  # Note: uuid_ not uuid
    mock_span.span_id = formatted_span_id  # This needs to match formated_span_id
    
    mock_response = Mock()
    mock_response.items = [mock_span]
    
    mock_client = Mock()
    mock_client.projects.functions.spans.list_paginated.return_value = mock_response
    
    trace = Trace(response="test", span_id=span_id, function_uuid="test-uuid")
    result = trace._get_span_uuid(mock_client)
    
    assert result == "test-span-uuid"


def test_trace_create_request_single_annotation():
    """Test _create_request with single annotation (line 105)."""
    trace = Trace(response="test", span_id=123, function_uuid="test-func-uuid")
    
    annotation = Annotation(data={"key": "value"}, label="pass", reasoning="Test", type="manual")
    
    result = trace._create_request("project-id", "span-uuid", (annotation,))
    
    assert len(result) == 1
    assert result[0].data == {"key": "value"}
    assert result[0].label == "pass"


def test_trace_decorator_with_wrap_mode():
    """Test trace decorator with wrap mode."""
    
    # In wrap mode, the function returns a Trace object, not the original result
    @trace(mode="wrap")
    def test_function(x: int) -> int:
        return x * 2
    
    # Should return a Trace object in wrap mode
    result = test_function(5)
    assert isinstance(result, Trace)


def test_trace_decorator_init_with_automatic_versioning():
    """Test trace decorator initialization with automatic versioning."""
    
    @trace(versioning="automatic")
    def test_function(x: int) -> int:
        return x * 2
    
    # Should have wrapped function with versioning capability
    assert hasattr(test_function, 'version')


def test_trace_decorator_init_with_none_versioning():
    """Test trace decorator initialization with None versioning."""
    
    @trace(versioning=None)
    def test_function(x: int) -> int:
        return x * 2
    
    # Should be wrapped but without versioning
    assert callable(test_function)


def test_trace_decorator_with_custom_function():
    """Test trace decorator with custom function provided."""
    mock_function = Mock()
    mock_function.uuid = "custom-func-uuid"
    
    @trace(function=mock_function)
    def test_function(x: int) -> int:
        return x * 2
    
    # Should use custom function and return Trace object in wrap mode
    result = test_function(5)
    assert isinstance(result, Trace)


def test_trace_version_method_success():
    """Test version method when function is found."""
    
    @trace(versioning="automatic")
    def test_function(x: int) -> int:
        return x * 2
    
    mock_function = Mock()
    mock_function.uuid = "versioned-func-uuid"
    
    with (
        patch("lilypad.traces.get_function_by_version_sync", return_value=mock_function),
        patch("lilypad.traces.get_sync_client") as mock_client,
        patch("lilypad.traces.get_settings") as mock_settings,
    ):
        mock_settings.return_value.api_key = "test-key"
        mock_settings.return_value.project_id = "test-project"
        mock_client.return_value = Mock()
        
        versioned_func = test_function.version(1)
        # Should return a callable with the versioned function
        assert callable(versioned_func)


def test_trace_remote_method_success():
    """Test remote method when function is found."""
    
    @trace(versioning="automatic")
    def test_function(x: int) -> int:
        return x * 2
    
    mock_function = Mock()
    mock_function.uuid = "remote-func-uuid"
    
    with (
        patch("lilypad.traces.get_deployed_function_sync", return_value=mock_function),
        patch("lilypad.traces.get_sync_client") as mock_client,
        patch("lilypad.traces.get_settings") as mock_settings,
    ):
        mock_settings.return_value.api_key = "test-key"
        mock_settings.return_value.project_id = "test-project"
        mock_client.return_value = Mock()
        
        remote_func = test_function.remote()
        # Should return a callable with the remote function
        assert callable(remote_func)


def test_async_trace_decorator_initialization():
    """Test async trace decorator initialization."""
    
    @trace()
    async def async_function(x: int) -> int:
        return x * 2
    
    # Should be callable after decoration
    assert callable(async_function)


def test_trace_sync_with_tags():
    """Test sync trace with tags."""
    trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
    
    with (
        patch("lilypad.traces.get_settings") as mock_get_settings,
        patch("lilypad.traces.get_sync_client") as mock_get_client,
    ):
        mock_settings = Mock()
        mock_settings.project_id = "test-project"
        mock_get_settings.return_value = mock_settings
        
        mock_client = Mock()
        mock_client.projects.functions.spans.create_span_tag.return_value = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock _get_span_uuid to return a UUID
        with patch.object(trace, '_get_span_uuid', return_value="span-uuid"):
            # Should not raise when tags are provided
            trace.tag("tag1", "tag2")


def test_trace_sync_with_annotations():
    """Test sync trace with annotations."""
    trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
    
    annotation = Annotation(data={"key": "value"}, label="pass", reasoning="Test", type="manual")
    
    with (
        patch("lilypad.traces.get_settings") as mock_get_settings,
        patch("lilypad.traces.get_sync_client") as mock_get_client,
    ):
        mock_settings = Mock()
        mock_settings.project_id = "test-project"
        mock_get_settings.return_value = mock_settings
        
        mock_client = Mock()
        mock_client.projects.functions.spans.create_span_annotation.return_value = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock _get_span_uuid to return a UUID
        with patch.object(trace, '_get_span_uuid', return_value="span-uuid"):
            # Should not raise when annotations are provided
            trace.annotate(annotation)


def test_trace_sync_with_assignment():
    """Test sync trace with assignment."""
    trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
    
    with (
        patch("lilypad.traces.get_settings") as mock_get_settings,
        patch("lilypad.traces.get_sync_client") as mock_get_client,
    ):
        mock_settings = Mock()
        mock_settings.project_id = "test-project"
        mock_get_settings.return_value = mock_settings
        
        mock_client = Mock()
        mock_client.projects.functions.spans.create_span_assignment.return_value = Mock()
        mock_get_client.return_value = mock_client
        
        # Mock _get_span_uuid to return a UUID
        with patch.object(trace, '_get_span_uuid', return_value="span-uuid"):
            # Should not raise when emails are provided
            trace.assign("test@example.com")