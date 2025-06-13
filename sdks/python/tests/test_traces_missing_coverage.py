"""Comprehensive tests to cover missing lines in traces.py."""

import os
import inspect
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from typing import Any

import pytest

from lilypad.traces import (
    _register_decorated_function,
    enable_recording,
    disable_recording,
    clear_registry,
    get_decorated_functions,
    _get_trace_context,
    _set_trace_context,
    _construct_trace_attributes,
    trace,
    Trace,
    AsyncTrace,
    Annotation,
    _TraceBase,
    _get_trace_type,
    _set_span_attributes,
    _ResultHolder,
)
from lilypad.generated.types.function_public import FunctionPublic
from lilypad.generated.types.label import Label
from lilypad.generated.types.evaluation_type import EvaluationType
from lilypad.spans import Span
from lilypad.exceptions import RemoteFunctionError


def test_register_decorated_function_disabled():
    """Test _register_decorated_function when recording is disabled."""
    clear_registry()
    disable_recording()
    
    def test_fn():
        pass
    
    # Should not register anything when recording is disabled
    _register_decorated_function("test_decorator", test_fn, "test_fn", {"key": "value"})
    
    registry = get_decorated_functions()
    assert registry == {}


def test_register_decorated_function_enabled():
    """Test _register_decorated_function when recording is enabled."""
    clear_registry()
    enable_recording()
    
    def test_fn():
        pass
    
    # Should register when recording is enabled
    _register_decorated_function("test_decorator", test_fn, "test_fn", {"key": "value"})
    
    registry = get_decorated_functions()
    assert "test_decorator" in registry
    assert len(registry["test_decorator"]) == 1
    
    file_path, function_name, line_no, module_name, context = registry["test_decorator"][0]
    assert function_name == "test_fn"
    assert context == {"key": "value"}
    
    disable_recording()
    clear_registry()


def test_register_decorated_function_inspect_failure():
    """Test _register_decorated_function handles inspect failures gracefully."""
    clear_registry()
    enable_recording()
    
    # Create a function that will cause inspect to fail
    test_fn = lambda: None  # lambda functions can cause issues with inspect
    
    # Mock inspect.getfile to raise an exception
    with patch("lilypad.traces.inspect.getfile", side_effect=OSError("File not found")):
        _register_decorated_function("test_decorator", test_fn, "test_fn")
    
    # Should handle the exception gracefully
    registry = get_decorated_functions()
    assert registry == {}
    
    disable_recording()
    clear_registry()


def test_get_decorated_functions_with_specific_decorator():
    """Test get_decorated_functions with specific decorator name."""
    clear_registry()
    enable_recording()
    
    def test_fn1():
        pass
    
    def test_fn2():
        pass
    
    _register_decorated_function("decorator1", test_fn1, "test_fn1")
    _register_decorated_function("decorator2", test_fn2, "test_fn2")
    
    # Get specific decorator
    result = get_decorated_functions("decorator1")
    assert "decorator1" in result
    assert "decorator2" not in result
    assert len(result["decorator1"]) == 1
    
    # Get all decorators
    all_result = get_decorated_functions()
    assert "decorator1" in all_result
    assert "decorator2" in all_result
    
    disable_recording()
    clear_registry()


def test_trace_context_functions():
    """Test trace context get/set functions."""
    # Test setting and getting context
    test_context = {"span_id": 123, "function_uuid": "test-uuid"}
    _set_trace_context(test_context)
    
    retrieved_context = _get_trace_context()
    assert retrieved_context == test_context
    
    # Test that original dict is not modified (it's a copy)
    test_context["new_key"] = "new_value"
    retrieved_context_again = _get_trace_context()
    assert "new_key" not in retrieved_context_again


def test_construct_trace_attributes_serialization_error():
    """Test _construct_trace_attributes handles serialization errors."""
    # Create an object that will fail serialization
    class UnserializableObject:
        def __init__(self):
            # This will create a circular reference
            self.circular = self
    
    arg_values = {
        "good_arg": "test_value",
        "bad_arg": UnserializableObject(),
    }
    arg_types = {
        "good_arg": "str",
        "bad_arg": "UnserializableObject",
    }
    
    result = _construct_trace_attributes("trace", arg_types, arg_values, {})
    
    # Should handle the serialization error gracefully
    assert "lilypad.trace.arg_types" in result
    assert "lilypad.trace.arg_values" in result


def test_get_trace_type():
    """Test _get_trace_type function."""
    # With function
    mock_function = Mock()
    assert _get_trace_type(mock_function) == "function"
    
    # Without function
    assert _get_trace_type(None) == "trace"


def test_result_holder():
    """Test _ResultHolder class."""
    holder = _ResultHolder()
    assert holder.result is None
    
    holder.set_result("test_value")
    assert holder.result == "test_value"


def test_set_span_attributes_no_opentelemetry_span():
    """Test _set_span_attributes when span has no opentelemetry_span."""
    mock_span = Mock()
    mock_span.opentelemetry_span = None
    
    span_attribute = {}
    
    with _set_span_attributes(mock_span, span_attribute, True, None) as result_holder:
        assert isinstance(result_holder, _ResultHolder)
    
    # Should not have set any attributes since opentelemetry_span is None
    assert span_attribute == {}


@patch("lilypad.traces.get_settings")
def test_set_span_attributes_with_function(mock_get_settings):
    """Test _set_span_attributes with a function."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    mock_function = Mock()
    mock_function.uuid_ = "test-function-uuid"
    mock_function.signature = "def test_fn(): pass"
    mock_function.code = "def test_fn(): pass"
    
    mock_span = Mock()
    mock_opentelemetry_span = Mock()
    mock_span.opentelemetry_span = mock_opentelemetry_span
    
    span_attribute = {}
    decorator_tags = ["tag1", "tag2"]
    
    with _set_span_attributes(
        mock_span, span_attribute, True, mock_function, decorator_tags
    ) as result_holder:
        result_holder.set_result("test_output")
    
    # Verify attributes were set
    mock_opentelemetry_span.set_attributes.assert_called_once()
    mock_opentelemetry_span.set_attribute.assert_called_once()
    
    # Check that the right attributes were added
    assert span_attribute["lilypad.project_uuid"] == "test-project"
    assert span_attribute["lilypad.type"] == "function"
    assert span_attribute["lilypad.is_async"] is True
    assert span_attribute["lilypad.trace.tags"] == decorator_tags
    assert span_attribute["lilypad.function.signature"] == "def test_fn(): pass"
    assert span_attribute["lilypad.function.code"] == "def test_fn(): pass"
    assert span_attribute["lilypad.function.uuid"] == "test-function-uuid"


@patch("lilypad.traces.get_settings")
def test_set_span_attributes_without_function(mock_get_settings):
    """Test _set_span_attributes without a function."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    mock_span = Mock()
    mock_opentelemetry_span = Mock()
    mock_span.opentelemetry_span = mock_opentelemetry_span
    
    span_attribute = {}
    
    with _set_span_attributes(mock_span, span_attribute, False, None) as result_holder:
        result_holder.set_result(None)
    
    # Verify attributes were set
    mock_opentelemetry_span.set_attributes.assert_called_once()
    mock_opentelemetry_span.set_attribute.assert_called_once()
    
    # Check that the right attributes were added
    assert span_attribute["lilypad.project_uuid"] == "test-project"
    assert span_attribute["lilypad.type"] == "trace"
    assert span_attribute["lilypad.is_async"] is False
    assert span_attribute["lilypad.function.uuid"] == ""


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_sync_client")
def test_trace_annotate_span_not_found(mock_get_sync_client, mock_get_settings):
    """Test Trace.annotate when span is not found."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_settings.api_key = "test-api-key"
    mock_get_settings.return_value = mock_settings
    
    mock_client = Mock()
    mock_response = Mock()
    mock_response.items = []  # Empty list means span not found
    mock_client.projects.functions.spans.list_paginated.return_value = mock_response
    mock_get_sync_client.return_value = mock_client
    
    trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
    
    # Force flush should be called
    with patch.object(trace, '_force_flush') as mock_force_flush:
        annotation = Annotation(data={"key": "value"}, label="pass", reasoning="test", type="manual")
        
        with pytest.raises(Exception) as exc_info:
            trace.annotate(annotation)
        
        mock_force_flush.assert_called_once()
        assert "SpanNotFoundError" in str(exc_info.value.__class__.__name__)


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_sync_client")
def test_trace_assign_span_not_found(mock_get_sync_client, mock_get_settings):
    """Test Trace.assign when span is not found."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_settings.api_key = "test-api-key"
    mock_get_settings.return_value = mock_settings
    
    mock_client = Mock()
    mock_response = Mock()
    mock_response.items = []  # Empty list means span not found
    mock_client.projects.functions.spans.list_paginated.return_value = mock_response
    mock_get_sync_client.return_value = mock_client
    
    trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
    
    with patch.object(trace, '_force_flush') as mock_force_flush:
        with pytest.raises(Exception) as exc_info:
            trace.assign("test@example.com")
        
        mock_force_flush.assert_called_once()
        assert "SpanNotFoundError" in str(exc_info.value.__class__.__name__)


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_sync_client")
def test_trace_tag_span_not_found(mock_get_sync_client, mock_get_settings):
    """Test Trace.tag when span is not found."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_settings.api_key = "test-api-key"
    mock_get_settings.return_value = mock_settings
    
    mock_client = Mock()
    mock_response = Mock()
    mock_response.items = []  # Empty list means span not found
    mock_client.projects.functions.spans.list_paginated.return_value = mock_response
    mock_get_sync_client.return_value = mock_client
    
    trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
    
    with patch.object(trace, '_force_flush') as mock_force_flush:
        with pytest.raises(Exception) as exc_info:
            trace.tag("tag1", "tag2")
        
        mock_force_flush.assert_called_once()
        assert "SpanNotFoundError" in str(exc_info.value.__class__.__name__)


def test_trace_tag_empty_tags():
    """Test Trace.tag with empty tags."""
    trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
    
    # Should return None for empty tags
    result = trace.tag()
    assert result is None


@pytest.mark.asyncio
@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_async_client")
async def test_async_trace_annotate_span_not_found(mock_get_async_client, mock_get_settings):
    """Test AsyncTrace.annotate when span is not found."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_settings.api_key = "test-api-key"
    mock_get_settings.return_value = mock_settings
    
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.items = []  # Empty list means span not found
    mock_client.projects.functions.spans.list_paginated.return_value = mock_response
    mock_get_async_client.return_value = mock_client
    
    async_trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")
    
    with patch.object(async_trace, '_force_flush') as mock_force_flush:
        annotation = Annotation(data={"key": "value"}, label="pass", reasoning="test", type="manual")
        
        with pytest.raises(Exception) as exc_info:
            await async_trace.annotate(annotation)
        
        mock_force_flush.assert_called_once()
        assert "SpanNotFoundError" in str(exc_info.value.__class__.__name__)


@pytest.mark.asyncio
@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_async_client")
async def test_async_trace_assign_span_not_found(mock_get_async_client, mock_get_settings):
    """Test AsyncTrace.assign when span is not found."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_settings.api_key = "test-api-key"
    mock_get_settings.return_value = mock_settings
    
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.items = []  # Empty list means span not found
    mock_client.projects.functions.spans.list_paginated.return_value = mock_response
    mock_get_async_client.return_value = mock_client
    
    async_trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")
    
    with patch.object(async_trace, '_force_flush') as mock_force_flush:
        with pytest.raises(Exception) as exc_info:
            await async_trace.assign("test@example.com")
        
        mock_force_flush.assert_called_once()
        assert "SpanNotFoundError" in str(exc_info.value.__class__.__name__)


@pytest.mark.asyncio
@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_async_client")
async def test_async_trace_tag_span_not_found(mock_get_async_client, mock_get_settings):
    """Test AsyncTrace.tag when span is not found."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_settings.api_key = "test-api-key"
    mock_get_settings.return_value = mock_settings
    
    mock_client = AsyncMock()
    mock_response = Mock()
    mock_response.items = []  # Empty list means span not found
    mock_client.projects.functions.spans.list_paginated.return_value = mock_response
    mock_get_async_client.return_value = mock_client
    
    async_trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")
    
    with patch.object(async_trace, '_force_flush') as mock_force_flush:
        with pytest.raises(Exception) as exc_info:
            await async_trace.tag("tag1", "tag2")
        
        mock_force_flush.assert_called_once()
        assert "SpanNotFoundError" in str(exc_info.value.__class__.__name__)


@pytest.mark.asyncio
async def test_async_trace_tag_empty_tags():
    """Test AsyncTrace.tag with empty tags."""
    async_trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")
    
    # Should return None for empty tags
    result = await async_trace.tag()
    assert result is None


def test_trace_force_flush():
    """Test _force_flush method."""
    trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
    
    # Mock tracer provider
    mock_tracer_provider = Mock()
    mock_force_flush = Mock()
    mock_tracer_provider.force_flush = mock_force_flush
    
    with patch("lilypad.traces.get_tracer_provider", return_value=mock_tracer_provider):
        trace._force_flush()
        mock_force_flush.assert_called_once_with(timeout_millis=5000)
        assert trace._flush is True


def test_trace_force_flush_no_force_flush_method():
    """Test _force_flush when tracer doesn't have force_flush method."""
    trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
    
    # Mock tracer provider without force_flush method
    mock_tracer_provider = Mock()
    del mock_tracer_provider.force_flush  # Remove the method
    
    with patch("lilypad.traces.get_tracer_provider", return_value=mock_tracer_provider):
        trace._force_flush()  # Should not raise exception
        assert trace._flush is False  # Should remain False


def test_annotation_validation():
    """Test Annotation validation."""
    # Test empty annotation
    with pytest.raises(ValueError):
        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
        trace.annotate()
    
    # Test empty email for assign
    with pytest.raises(ValueError):
        trace = Trace(response="test", span_id=123, function_uuid="test-uuid")
        trace.assign()


@pytest.mark.asyncio
async def test_async_annotation_validation():
    """Test AsyncTrace annotation validation."""
    # Test empty annotation
    with pytest.raises(ValueError):
        async_trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")
        await async_trace.annotate()
    
    # Test empty email for assign
    with pytest.raises(ValueError):
        async_trace = AsyncTrace(response="test", span_id=123, function_uuid="test-uuid")
        await async_trace.assign()


@pytest.mark.asyncio
@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_function_by_version_async")
@patch("lilypad.traces.get_cached_closure")
async def test_trace_decorator_version_async_exception(
    mock_get_cached_closure, mock_get_function_by_version_async, mock_get_settings
):
    """Test trace decorator version method with async function when exception occurs."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    # Mock exception during function retrieval
    mock_get_function_by_version_async.side_effect = Exception("Function not found")
    
    @trace(versioning="automatic")
    async def test_async_function():
        return "test"
    
    # Should raise RemoteFunctionError
    with pytest.raises(RemoteFunctionError) as exc_info:
        await test_async_function.version(1)
    
    assert "Failed to retrieve function" in str(exc_info.value)


@pytest.mark.asyncio
@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_deployed_function_async")
@patch("lilypad.traces.get_cached_closure")
async def test_trace_decorator_remote_async_exception(
    mock_get_cached_closure, mock_get_deployed_function_async, mock_get_settings
):
    """Test trace decorator remote method with async function when exception occurs."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    # Mock exception during function retrieval
    mock_get_deployed_function_async.side_effect = Exception("Function not found")
    
    @trace(versioning="automatic")
    async def test_async_function():
        return "test"
    
    # Should raise RemoteFunctionError
    with pytest.raises(RemoteFunctionError) as exc_info:
        await test_async_function.remote()
    
    assert "Failed to retrieve function" in str(exc_info.value)


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_function_by_version_sync")
@patch("lilypad.traces.get_cached_closure")
def test_trace_decorator_version_sync_exception(
    mock_get_cached_closure, mock_get_function_by_version_sync, mock_get_settings
):
    """Test trace decorator version method with sync function when exception occurs."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    # Mock exception during function retrieval
    mock_get_function_by_version_sync.side_effect = Exception("Function not found")
    
    @trace(versioning="automatic")
    def test_sync_function():
        return "test"
    
    # Should raise RemoteFunctionError
    with pytest.raises(RemoteFunctionError) as exc_info:
        test_sync_function.version(1)
    
    assert "Failed to retrieve function" in str(exc_info.value)


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_deployed_function_sync")
@patch("lilypad.traces.get_cached_closure")
def test_trace_decorator_remote_sync_exception(
    mock_get_cached_closure, mock_get_deployed_function_sync, mock_get_settings
):
    """Test trace decorator remote method with sync function when exception occurs."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    # Mock exception during function retrieval
    mock_get_deployed_function_sync.side_effect = Exception("Function not found")
    
    @trace(versioning="automatic")
    def test_sync_function():
        return "test"
    
    # Should raise RemoteFunctionError
    with pytest.raises(RemoteFunctionError) as exc_info:
        test_sync_function.remote()
    
    assert "Failed to retrieve function" in str(exc_info.value)


@pytest.mark.asyncio
@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.SubprocessSandboxRunner")
@patch("lilypad.traces.get_function_by_version_async")
@patch("lilypad.traces.get_cached_closure")
async def test_trace_decorator_version_async_with_sandbox(
    mock_get_cached_closure, mock_get_function_by_version_async, mock_sandbox_runner, mock_get_settings
):
    """Test trace decorator version method with async function and default sandbox."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    mock_function = Mock()
    mock_get_function_by_version_async.return_value = mock_function
    mock_closure = Mock()
    mock_get_cached_closure.return_value = mock_closure
    
    mock_sandbox_instance = Mock()
    mock_sandbox_instance.execute_function.return_value = {
        "result": "sandbox_result",
        "trace_context": {"span_id": 456, "function_uuid": "test-uuid"}
    }
    mock_sandbox_runner.return_value = mock_sandbox_instance
    
    @trace(versioning="automatic")
    async def test_async_function():
        return "test"
    
    # Test with default sandbox (None)
    versioned_fn = await test_async_function.version(1)
    result = versioned_fn()
    
    # Should use SubprocessSandboxRunner with os.environ.copy()
    mock_sandbox_runner.assert_called_once()
    assert result == "sandbox_result"


@pytest.mark.asyncio
@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.SubprocessSandboxRunner")
@patch("lilypad.traces.get_deployed_function_async")
@patch("lilypad.traces.get_cached_closure")
async def test_trace_decorator_remote_async_with_sandbox(
    mock_get_cached_closure, mock_get_deployed_function_async, mock_sandbox_runner, mock_get_settings
):
    """Test trace decorator remote method with async function and default sandbox."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    mock_function = Mock()
    mock_get_deployed_function_async.return_value = mock_function
    mock_closure = Mock()
    mock_get_cached_closure.return_value = mock_closure
    
    mock_sandbox_instance = Mock()
    mock_sandbox_instance.execute_function.return_value = {
        "result": "sandbox_result",
        "trace_context": {"span_id": 456, "function_uuid": "test-uuid"}
    }
    mock_sandbox_runner.return_value = mock_sandbox_instance
    
    @trace(versioning="automatic")
    async def test_async_function():
        return "test"
    
    # Test with default sandbox (None)
    result = await test_async_function.remote()
    
    # Should use SubprocessSandboxRunner with os.environ.copy()
    mock_sandbox_runner.assert_called_once()
    assert result == "sandbox_result"


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.SubprocessSandboxRunner")
@patch("lilypad.traces.get_function_by_version_sync")
@patch("lilypad.traces.get_cached_closure")
def test_trace_decorator_version_sync_with_sandbox(
    mock_get_cached_closure, mock_get_function_by_version_sync, mock_sandbox_runner, mock_get_settings
):
    """Test trace decorator version method with sync function and default sandbox."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    mock_function = Mock()
    mock_get_function_by_version_sync.return_value = mock_function
    mock_closure = Mock()
    mock_get_cached_closure.return_value = mock_closure
    
    mock_sandbox_instance = Mock()
    mock_sandbox_instance.execute_function.return_value = {
        "result": "sandbox_result",
        "trace_context": {"span_id": 456, "function_uuid": "test-uuid"}
    }
    mock_sandbox_runner.return_value = mock_sandbox_instance
    
    @trace(versioning="automatic")
    def test_sync_function():
        return "test"
    
    # Test with default sandbox (None)
    versioned_fn = test_sync_function.version(1)
    result = versioned_fn()
    
    # Should use SubprocessSandboxRunner with os.environ.copy()
    mock_sandbox_runner.assert_called_once()
    assert result == "sandbox_result"


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.SubprocessSandboxRunner")
@patch("lilypad.traces.get_deployed_function_sync")
@patch("lilypad.traces.get_cached_closure")
def test_trace_decorator_remote_sync_with_sandbox(
    mock_get_cached_closure, mock_get_deployed_function_sync, mock_sandbox_runner, mock_get_settings
):
    """Test trace decorator remote method with sync function and default sandbox."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_get_settings.return_value = mock_settings
    
    mock_function = Mock()
    mock_get_deployed_function_sync.return_value = mock_function
    mock_closure = Mock()
    mock_get_cached_closure.return_value = mock_closure
    
    mock_sandbox_instance = Mock()
    mock_sandbox_instance.execute_function.return_value = {
        "result": "sandbox_result",
        "trace_context": {"span_id": 456, "function_uuid": "test-uuid"}
    }
    mock_sandbox_runner.return_value = mock_sandbox_instance
    
    @trace(versioning="automatic")
    def test_sync_function():
        return "test"
    
    # Test with default sandbox (None)
    result = test_sync_function.remote()
    
    # Should use SubprocessSandboxRunner with os.environ.copy()
    mock_sandbox_runner.assert_called_once()
    assert result == "sandbox_result"


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.create_mirascope_middleware")
@patch("lilypad.traces.get_function_by_hash_sync")
@patch("lilypad.traces.get_sync_client")
@patch("lilypad.traces.Closure")
@patch("lilypad.traces.Span")
def test_trace_decorator_mirascope_call_sync(
    mock_span_class, mock_closure_class, mock_get_sync_client, mock_get_function_by_hash_sync,
    mock_create_mirascope_middleware, mock_get_settings
):
    """Test trace decorator with mirascope call (sync)."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_settings.api_key = "test-api-key"
    mock_get_settings.return_value = mock_settings
    
    mock_span = Mock()
    mock_span.span_id = 123
    mock_span.opentelemetry_span = Mock()
    mock_span_class.return_value.__enter__ = Mock(return_value=mock_span)
    mock_span_class.return_value.__exit__ = Mock(return_value=False)
    
    mock_closure = Mock()
    mock_closure.hash = "test-hash"
    mock_closure_class.from_fn.return_value = mock_closure
    
    mock_function = Mock()
    mock_function.uuid_ = "test-function-uuid"
    mock_get_function_by_hash_sync.return_value = mock_function
    
    mock_middleware = Mock()
    mock_middleware.return_value.return_value = "mirascope_result"
    mock_create_mirascope_middleware.return_value = mock_middleware
    
    # Create a function with mirascope call attribute
    def test_fn():
        return "test"
    
    test_fn.__mirascope_call__ = True
    
    decorated = trace(versioning="automatic")(test_fn)
    result = decorated()
    
    # Should use mirascope middleware
    mock_create_mirascope_middleware.assert_called_once()
    assert result == "mirascope_result"


@pytest.mark.asyncio
@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.create_mirascope_middleware")
@patch("lilypad.traces.get_function_by_hash_async")
@patch("lilypad.traces.get_async_client")
@patch("lilypad.traces.Closure")
@patch("lilypad.traces.Span")
async def test_trace_decorator_mirascope_call_async(
    mock_span_class, mock_closure_class, mock_get_async_client, mock_get_function_by_hash_async,
    mock_create_mirascope_middleware, mock_get_settings
):
    """Test trace decorator with mirascope call (async)."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_settings.api_key = "test-api-key"
    mock_get_settings.return_value = mock_settings
    
    mock_span = Mock()
    mock_span.span_id = 123
    mock_span.opentelemetry_span = Mock()
    mock_span_class.return_value.__aenter__ = AsyncMock(return_value=mock_span)
    mock_span_class.return_value.__aexit__ = AsyncMock(return_value=False)
    
    mock_closure = Mock()
    mock_closure.hash = "test-hash"
    mock_closure_class.from_fn.return_value = mock_closure
    
    mock_function = Mock()
    mock_function.uuid_ = "test-function-uuid"
    mock_get_function_by_hash_async.return_value = mock_function
    
    # Create a mock that returns a callable that returns the result
    mock_middleware_fn = AsyncMock(return_value="mirascope_result")
    mock_middleware = Mock(return_value=mock_middleware_fn)
    mock_create_mirascope_middleware.return_value = mock_middleware
    
    # Create an async function with mirascope call attribute
    async def test_async_fn():
        return "test"
    
    test_async_fn.__mirascope_call__ = True
    
    decorated = trace(versioning="automatic")(test_async_fn)
    result = await decorated()
    
    # Should use mirascope middleware
    mock_create_mirascope_middleware.assert_called_once()
    assert result == "mirascope_result"


def test_trace_base_create_request():
    """Test _TraceBase._create_request method."""
    trace = _TraceBase(response="test", span_id=123, function_uuid="test-uuid")
    
    annotations = (
        Annotation(
            data={"key": "value"},
            label="pass",
            reasoning="test reasoning",
            type="manual"
        ),
        Annotation(
            data={"key2": "value2"},
            label="fail",
            reasoning="test reasoning 2",
            type="verified"
        ),
    )
    
    result = trace._create_request("project-id", "span-uuid", annotations)
    
    assert len(result) == 2
    assert result[0].data == {"key": "value"}
    assert result[0].function_uuid == "test-uuid"
    assert result[0].span_uuid == "span-uuid"
    assert result[0].project_uuid == "project-id"
    assert result[0].label == "pass"
    assert result[0].reasoning == "test reasoning"
    assert result[0].type == "manual"
    
    assert result[1].data == {"key2": "value2"}
    assert result[1].label == "fail"
    assert result[1].reasoning == "test reasoning 2"
    assert result[1].type == "verified"