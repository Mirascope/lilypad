"""Comprehensive tests for traces.py module.

This file consolidates all traces-related tests to achieve 100% coverage.
Tests are organized by functionality using pytest's functional style.
"""

import asyncio
import inspect
import os
import sys
from datetime import datetime
from typing import Any, Optional
from unittest.mock import AsyncMock, Mock, PropertyMock, mock_open, patch

import pytest

from src.lilypad.exceptions import RemoteFunctionError, SpanNotFoundError
from src.lilypad.generated.errors.not_found_error import NotFoundError
from src.lilypad.generated.types.annotation_create import AnnotationCreate
from src.lilypad.generated.types.evaluation_type import EvaluationType
from src.lilypad.generated.types.function_public import FunctionPublic
from src.lilypad.generated.types.label import Label
from src.lilypad.generated.types.paginated_span_public import PaginatedSpanPublic
from src.lilypad.generated.types.span_public import SpanPublic
from src.lilypad.traces import (
    Annotation,
    AsyncTrace,
    AsyncVersionedFunction,
    SyncVersionedFunction,
    Trace,
    TraceDecoratedFunctionWithContext,
    TraceDecorator,
    VersionedFunctionTraceDecorator,
    WrappedTraceDecorator,
    WrappedVersionedFunctionTraceDecorator,
    _get_trace_type,
    _register_decorated_function,
    _set_span_attributes,
    trace,
)


# =============================================================================
# Basic Functionality Tests
# =============================================================================


def test_get_trace_type():
    """Test _get_trace_type function."""
    # With function
    mock_function = Mock(spec=FunctionPublic)
    assert _get_trace_type(mock_function) == "function"
    
    # Without function
    assert _get_trace_type(None) == "trace"


def test_annotation_class():
    """Test Annotation class initialization."""
    ann = Annotation(
        data={"key": "value"},
        label=Label.POSITIVE,
        reasoning="Good response",
        type=EvaluationType.BOOLEAN
    )
    
    assert ann.data == {"key": "value"}
    assert ann.label == Label.POSITIVE
    assert ann.reasoning == "Good response"
    assert ann.type == EvaluationType.BOOLEAN


def test_trace_base_initialization():
    """Test _TraceBase initialization and properties."""
    from src.lilypad.traces import _TraceBase
    
    trace = _TraceBase(response="test response", span_id=12345, function_uuid="uuid-123")
    
    assert trace.response == "test response"
    assert trace.function_uuid == "uuid-123"
    assert trace.formated_span_id == format_span_id(12345)
    assert trace._flush is False


def test_trace_base_force_flush():
    """Test _TraceBase._force_flush method."""
    from src.lilypad.traces import _TraceBase
    
    trace = _TraceBase(response="test", span_id=12345, function_uuid="uuid-123")
    
    # Test with tracer provider that has force_flush
    with patch('src.lilypad.traces.get_tracer_provider') as mock_provider:
        mock_tracer = Mock()
        mock_tracer.force_flush = Mock(return_value=True)
        mock_provider.return_value = mock_tracer
        
        trace._force_flush()
        mock_tracer.force_flush.assert_called_with(timeout_millis=5000)
    
    # Test with tracer provider without force_flush
    with patch('src.lilypad.traces.get_tracer_provider') as mock_provider:
        mock_tracer = Mock(spec=[])  # No force_flush method
        mock_provider.return_value = mock_tracer
        
        # Should not raise error
        trace._force_flush()


# =============================================================================
# Trace and AsyncTrace Methods Tests
# =============================================================================


def test_trace_get_span_uuid_success():
    """Test successful span UUID retrieval."""
    mock_span = SpanPublic(
        span_id="00000000075bcd15",  # format_span_id(123456789)
        uuid_="test-span-uuid",
        project_uuid="test-project",
        scope="lilypad",
        annotations=[],
        child_spans=[],
        created_at=datetime.now(),
        tags=[],
    )
    
    mock_response = PaginatedSpanPublic(items=[mock_span], limit=10, offset=0, total=1)
    
    mock_client = Mock()
    mock_client.projects.functions.spans.list_paginated.return_value = mock_response
    
    trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")
    result = trace._get_span_uuid(mock_client)
    
    assert result == "test-span-uuid"
    mock_client.projects.functions.spans.list_paginated.assert_called_once()


def test_trace_get_span_uuid_no_match():
    """Test that None is returned when no matching span is found."""
    mock_span = SpanPublic(
        span_id="different-span-id",
        uuid_="test-span-uuid",
        project_uuid="test-project",
        scope="lilypad",
        annotations=[],
        child_spans=[],
        created_at=datetime.now(),
        tags=[],
    )
    
    mock_response = PaginatedSpanPublic(items=[mock_span], limit=10, offset=0, total=1)
    
    mock_client = Mock()
    mock_client.projects.functions.spans.list_paginated.return_value = mock_response
    
    trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")
    result = trace._get_span_uuid(mock_client)
    
    assert result is None


def test_trace_flush_behavior():
    """Test that _force_flush is called when _flush is False."""
    trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")
    assert trace._flush is False  # Default state
    
    mock_response = PaginatedSpanPublic(items=[], limit=10, offset=0, total=0)
    mock_client = Mock()
    mock_client.projects.functions.spans.list_paginated.return_value = mock_response
    
    with patch.object(trace, "_force_flush") as mock_force_flush:
        trace._get_span_uuid(mock_client)
        mock_force_flush.assert_called_once()


def test_trace_annotate():
    """Test Trace.annotate method."""
    trace = Trace(response="sync response", span_id=111, function_uuid="func-111")
    
    with patch('src.lilypad.traces.get_sync_client') as mock_client:
        mock_lilypad = Mock()
        mock_client.return_value = mock_lilypad
        
        # Mock _get_span_uuid to return a UUID
        with patch.object(trace, '_get_span_uuid', return_value="span-uuid"):
            # Test with label and reasoning
            trace.annotate(label="POSITIVE", reasoning="Good")
            mock_lilypad.annotations.create.assert_called_once()
            
            # Test with flush
            trace.annotate(label="NEGATIVE", reasoning="Bad", flush=True)
            assert mock_lilypad.annotations.create.call_count == 2


def test_trace_annotate_span_not_found():
    """Test annotate() raises SpanNotFoundError when span not found."""
    trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")
    
    with patch.object(trace, "_get_span_uuid", return_value=None):
        with pytest.raises(SpanNotFoundError) as exc_info:
            trace.annotate(label="POSITIVE")
        
        assert "Cannot annotate: span not found" in str(exc_info.value)
        assert "test-func-uuid" in str(exc_info.value)


def test_trace_assign():
    """Test Trace.assign method."""
    trace = Trace(response="test", span_id=123, function_uuid="func-123")
    
    with patch('src.lilypad.traces.get_sync_client') as mock_client:
        mock_lilypad = Mock()
        mock_client.return_value = mock_lilypad
        
        with patch.object(trace, '_get_span_uuid', return_value="span-uuid"):
            trace.assign("user@example.com", "other@example.com")
            mock_lilypad.projects.functions.spans.update.assert_called_once()
            
            call_args = mock_lilypad.projects.functions.spans.update.call_args
            assert call_args[1]['assigned_to'] == ["other@example.com", "user@example.com"]


def test_trace_assign_empty_emails():
    """Test assignment with no email addresses raises ValueError."""
    trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")
    
    with pytest.raises(ValueError) as exc_info:
        trace.assign()
    
    assert "At least one email address must be provided" in str(exc_info.value)


def test_trace_tag():
    """Test Trace.tag method."""
    trace = Trace(response="test", span_id=123, function_uuid="func-123")
    
    with patch('src.lilypad.traces.get_sync_client') as mock_client:
        mock_lilypad = Mock()
        mock_client.return_value = mock_lilypad
        
        with patch.object(trace, '_get_span_uuid', return_value="span-uuid"):
            trace.tag("tag1", "tag2")
            mock_lilypad.projects.functions.spans.update.assert_called_once()
            
            call_args = mock_lilypad.projects.functions.spans.update.call_args
            assert call_args[1]['tags'] == ["tag1", "tag2"]


def test_trace_tag_empty_returns_early():
    """Test that tag() returns early when no tags provided."""
    trace = Trace(response="test", span_id=123456789, function_uuid="test-func-uuid")
    
    with patch("src.lilypad.traces.get_settings") as mock_settings:
        with patch("src.lilypad.traces.get_sync_client") as mock_client:
            result = trace.tag()
            
            # Verify no API calls were made
            mock_settings.assert_not_called()
            mock_client.assert_not_called()
            assert result is None


@pytest.mark.asyncio
async def test_async_trace_methods():
    """Test AsyncTrace methods."""
    async_trace = AsyncTrace(response="async response", span_id=222, function_uuid="func-222")
    
    with patch('src.lilypad.traces.get_async_client') as mock_client:
        mock_lilypad = AsyncMock()
        mock_client.return_value = mock_lilypad
        
        # Mock async _get_span_uuid
        with patch.object(async_trace, '_get_span_uuid', new_callable=AsyncMock, return_value="span-uuid"):
            # Test annotate
            await async_trace.annotate(label="POSITIVE", reasoning="Good")
            mock_lilypad.annotations.create.assert_called_once()
            
            # Test assign
            await async_trace.assign("user@example.com")
            mock_lilypad.projects.functions.spans.update.assert_called()
            
            # Test tag
            await async_trace.tag("async-tag")
            assert mock_lilypad.projects.functions.spans.update.call_count == 2


# =============================================================================
# Decorator Tests
# =============================================================================


def test_simple_sync_trace():
    """Test basic synchronous trace decorator."""
    @trace()
    def simple_func(x: int) -> int:
        return x * 2
    
    # Test with proper settings and client setup
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project", api_key="test-key")
        
        with patch('src.lilypad.traces.get_sync_client') as mock_client:
            mock_lilypad = Mock()
            mock_client.return_value = mock_lilypad
            
            with patch('src.lilypad.traces.Span') as mock_span_class:
                mock_span = Mock()
                mock_span.span_id = 12345
                mock_span.opentelemetry_span = Mock()
                mock_span_context = Mock()
                mock_span_context.__enter__ = Mock(return_value=mock_span)
                mock_span_context.__exit__ = Mock(return_value=None)
                mock_span_class.return_value = mock_span_context
                
                result = simple_func(5)
                assert result == 10


@pytest.mark.asyncio
async def test_simple_async_trace():
    """Test basic asynchronous trace decorator."""
    @trace()
    async def async_func(x: int) -> int:
        return x * 3
    
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project", api_key="test-key")
        
        with patch('src.lilypad.traces.get_async_client') as mock_client:
            mock_lilypad = AsyncMock()
            mock_client.return_value = mock_lilypad
            
            with patch('src.lilypad.traces.Span') as mock_span_class:
                mock_span = Mock()
                mock_span.span_id = 12345
                mock_span.opentelemetry_span = Mock()
                mock_span_context = Mock()
                mock_span_context.__enter__ = Mock(return_value=mock_span)
                mock_span_context.__exit__ = Mock(return_value=None)
                mock_span_class.return_value = mock_span_context
                
                result = await async_func(5)
                assert result == 15


def test_trace_with_versioning():
    """Test trace decorator with versioning enabled."""
    @trace(versioning="automatic")
    def versioned_func():
        return "versioned"
    
    # Test version method exists
    assert hasattr(versioned_func, 'version')
    assert hasattr(versioned_func, 'remote')
    
    # Test with proper setup
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project", api_key="test-key")
        
        with patch('src.lilypad.traces.get_sync_client') as mock_client:
            with patch('src.lilypad.traces.Closure') as mock_closure_class:
                mock_closure = Mock(hash="test-hash", code="code", name="func", signature="sig", dependencies=[])
                mock_closure_class.from_fn.return_value = mock_closure
                
                with patch('src.lilypad.traces.get_function_by_hash_sync') as mock_get_hash:
                    mock_get_hash.return_value = Mock(uuid_="existing-id")
                    
                    with patch('src.lilypad.traces.Span') as mock_span_class:
                        mock_span = Mock(span_id=12345, opentelemetry_span=Mock())
                        mock_span_context = Mock()
                        mock_span_context.__enter__ = Mock(return_value=mock_span)
                        mock_span_context.__exit__ = Mock(return_value=None)
                        mock_span_class.return_value = mock_span_context
                        
                        result = versioned_func()
                        assert result == "versioned"


def test_trace_with_wrap_mode():
    """Test trace decorator with wrap mode."""
    @trace(mode="wrap")
    def wrapped_func():
        return "wrapped"
    
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project", api_key="test-key")
        
        with patch('src.lilypad.traces.get_sync_client') as mock_client:
            with patch('src.lilypad.traces.Span') as mock_span_class:
                mock_span = Mock(span_id=12345, opentelemetry_span=Mock())
                mock_span_context = Mock()
                mock_span_context.__enter__ = Mock(return_value=mock_span)
                mock_span_context.__exit__ = Mock(return_value=None)
                mock_span_class.return_value = mock_span_context
                
                result = wrapped_func()
                
                # In wrap mode, should return Trace object
                assert isinstance(result, Trace)
                assert result.response == "wrapped"


def test_trace_with_mirascope():
    """Test trace decorator with Mirascope integration."""
    @trace(versioning="automatic")
    def mirascope_func():
        return "mirascope"
    
    # Add mirascope attributes
    mirascope_func.__mirascope_call__ = True
    mirascope_func._prompt_template = "Test prompt"
    
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project", api_key="test-key")
        
        with patch('src.lilypad.traces.get_sync_client') as mock_client:
            with patch('src.lilypad.traces.Closure') as mock_closure_class:
                mock_closure = Mock(hash="test-hash", code="code", name="func", signature="sig", dependencies=[])
                mock_closure_class.from_fn.return_value = mock_closure
                
                with patch('src.lilypad.traces.get_function_by_hash_sync') as mock_get_hash:
                    mock_get_hash.return_value = Mock(uuid_="existing-id")
                    
                    with patch('src.lilypad.traces.create_mirascope_middleware') as mock_mirascope:
                        mock_middleware = Mock(return_value=lambda fn: lambda *a, **k: "mirascope_result")
                        mock_mirascope.return_value = mock_middleware
                        
                        with patch('src.lilypad.traces.Span') as mock_span_class:
                            mock_span = Mock(span_id=12345, opentelemetry_span=Mock())
                            mock_span_context = Mock()
                            mock_span_context.__enter__ = Mock(return_value=mock_span)
                            mock_span_context.__exit__ = Mock(return_value=None)
                            mock_span_class.return_value = mock_span_context
                            
                            result = mirascope_func()
                            assert result == "mirascope_result"
                            mock_mirascope.assert_called_once()


def test_trace_with_tags():
    """Test trace decorator with tags."""
    @trace(tags=["tag1", "tag2"])
    def tagged_func():
        return "tagged"
    
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project", api_key="test-key")
        
        with patch('src.lilypad.traces.get_sync_client') as mock_client:
            with patch('src.lilypad.traces.Span') as mock_span_class:
                mock_span = Mock(span_id=12345, opentelemetry_span=Mock())
                mock_span_context = Mock()
                mock_span_context.__enter__ = Mock(return_value=mock_span)
                mock_span_context.__exit__ = Mock(return_value=None)
                mock_span_class.return_value = mock_span_context
                
                with patch('src.lilypad.traces._set_span_attributes') as mock_set_attrs:
                    mock_ctx = Mock()
                    mock_ctx.__enter__ = Mock()
                    mock_ctx.__exit__ = Mock(return_value=None)
                    mock_set_attrs.return_value = mock_ctx
                    
                    result = tagged_func()
                    assert result == "tagged"
                    
                    # Check tags were passed
                    call_args = mock_set_attrs.call_args
                    assert call_args[1]['tags'] == ["tag1", "tag2"]


# =============================================================================
# Version and Remote Method Tests
# =============================================================================


def test_sync_version_method():
    """Test synchronous version method."""
    @trace(versioning="automatic")
    def versioned_func():
        return "v1"
    
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project")
        
        with patch('src.lilypad.traces.get_function_by_version_sync') as mock_get_version:
            mock_function = Mock(uuid_="version-uuid")
            mock_get_version.return_value = mock_function
            
            with patch('src.lilypad.traces.get_cached_closure') as mock_get_cached:
                mock_closure = Mock()
                mock_get_cached.return_value = mock_closure
                
                with patch('src.lilypad.traces.SubprocessSandboxRunner') as mock_sandbox_class:
                    mock_sandbox = Mock()
                    mock_sandbox.execute_function.return_value = {"result": "version_result"}
                    mock_sandbox_class.return_value = mock_sandbox
                    
                    version_func = versioned_func.version(1)
                    result = version_func()
                    assert result == "version_result"


def test_sync_remote_method():
    """Test synchronous remote method."""
    @trace(versioning="automatic")
    def remote_func():
        return "remote"
    
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project")
        
        with patch('src.lilypad.traces.get_deployed_function_sync') as mock_get_deployed:
            mock_function = Mock(uuid_="deployed-uuid")
            mock_get_deployed.return_value = mock_function
            
            with patch('src.lilypad.traces.get_cached_closure') as mock_get_cached:
                mock_closure = Mock()
                mock_get_cached.return_value = mock_closure
                
                with patch('src.lilypad.traces.SubprocessSandboxRunner') as mock_sandbox_class:
                    mock_sandbox = Mock()
                    mock_sandbox.execute_function.return_value = {"result": "remote_result"}
                    mock_sandbox_class.return_value = mock_sandbox
                    
                    result = remote_func.remote()
                    assert result == "remote_result"


@pytest.mark.asyncio
async def test_async_version_method():
    """Test asynchronous version method."""
    @trace(versioning="automatic")
    async def async_versioned_func():
        return "async_v1"
    
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project")
        
        with patch('src.lilypad.traces.get_function_by_version_async') as mock_get_version:
            mock_function = Mock(uuid_="async-version-uuid")
            mock_get_version.return_value = mock_function
            
            with patch('src.lilypad.traces.get_cached_closure') as mock_get_cached:
                mock_closure = Mock()
                mock_get_cached.return_value = mock_closure
                
                with patch('src.lilypad.traces.SubprocessSandboxRunner') as mock_sandbox_class:
                    mock_sandbox = Mock()
                    mock_sandbox.execute_function.return_value = {"result": "async_version_result"}
                    mock_sandbox_class.return_value = mock_sandbox
                    
                    version_func = await async_versioned_func.version(1)
                    result = version_func()
                    assert result == "async_version_result"


@pytest.mark.asyncio
async def test_async_remote_method():
    """Test asynchronous remote method."""
    @trace(versioning="automatic")
    async def async_remote_func():
        return "async_remote"
    
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project")
        
        with patch('src.lilypad.traces.get_deployed_function_async') as mock_get_deployed:
            mock_function = Mock(uuid_="async-deployed-uuid")
            mock_get_deployed.return_value = mock_function
            
            with patch('src.lilypad.traces.get_cached_closure') as mock_get_cached:
                mock_closure = Mock()
                mock_get_cached.return_value = mock_closure
                
                with patch('src.lilypad.traces.SubprocessSandboxRunner') as mock_sandbox_class:
                    mock_sandbox = Mock()
                    mock_sandbox.execute_function.return_value = {"result": "async_remote_result"}
                    mock_sandbox_class.return_value = mock_sandbox
                    
                    result = await async_remote_func.remote()
                    assert result == "async_remote_result"


def test_version_with_wrap_mode():
    """Test version method with wrap mode returns Trace object."""
    @trace(versioning="automatic", mode="wrap")
    def wrapped_version_func():
        return "test"
    
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project")
        
        with patch('src.lilypad.traces.get_function_by_version_sync') as mock_get_version:
            mock_get_version.return_value = Mock()
            
            with patch('src.lilypad.traces.get_cached_closure') as mock_cached:
                mock_cached.return_value = Mock()
                
                with patch('src.lilypad.traces.SubprocessSandboxRunner') as mock_sandbox_class:
                    mock_sandbox = Mock()
                    mock_sandbox.execute_function.return_value = {
                        "result": "wrapped_value",
                        "trace_context": {"span_id": 55555, "function_uuid": "wrap-func-uuid"}
                    }
                    mock_sandbox_class.return_value = mock_sandbox
                    
                    version_func = wrapped_version_func.version(1)
                    result = version_func()
                    
                    # Should return Trace object
                    assert isinstance(result, Trace)
                    assert result.response == "wrapped_value"
                    assert result.function_uuid == "wrap-func-uuid"


# =============================================================================
# Error Handling and Edge Cases
# =============================================================================


def test_register_decorated_function_errors():
    """Test _register_decorated_function error handling."""
    # Test with TypeError from getfile
    with patch('src.lilypad.traces._RECORDING_ENABLED', True):
        with patch('src.lilypad.traces._DECORATOR_REGISTRY', {}):
            with patch('inspect.getfile', side_effect=TypeError("Cannot get file")):
                result = _register_decorated_function(
                    decorator_name="test",
                    fn=print,  # Built-in function
                    function_name="print",
                    context=None
                )
                assert result is None
    
    # Test with OSError from abspath
    with patch('src.lilypad.traces._RECORDING_ENABLED', True):
        with patch('src.lilypad.traces._DECORATOR_REGISTRY', {}):
            with patch('inspect.getfile', return_value="/test/file.py"):
                with patch('os.path.abspath', side_effect=OSError("Path error")):
                    def test_func():
                        pass
                    
                    result = _register_decorated_function(
                        decorator_name="test",
                        fn=test_func,
                        function_name="test_func",
                        context=None
                    )
                    assert result is None


def test_set_span_attributes_error_handling():
    """Test _set_span_attributes error cases."""
    mock_span = Mock()
    mock_span.set_attribute.side_effect = Exception("Attribute error")
    
    # Should not raise exception
    with _set_span_attributes(
        span=mock_span,
        trace_type="trace",
        project_id="test-project",
        function=None,
        function_hash="hash123",
        versioning="automatic",
        version_name="v1",
        version_id=1,
        tags=["tag1"],
        args_dict={"arg1": "value1"},
        return_value="result"
    ):
        pass  # Context manager should handle errors gracefully


def test_trace_with_exception():
    """Test trace decorator with exception handling."""
    @trace()
    def failing_func():
        raise ValueError("Test error")
    
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project", api_key="test-key")
        
        with patch('src.lilypad.traces.get_sync_client') as mock_client:
            with patch('src.lilypad.traces.Span') as mock_span_class:
                mock_span = Mock(span_id=12345, opentelemetry_span=Mock())
                mock_span_context = Mock()
                mock_span_context.__enter__ = Mock(return_value=mock_span)
                mock_span_context.__exit__ = Mock(return_value=None)
                mock_span_class.return_value = mock_span_context
                
                with pytest.raises(ValueError) as exc_info:
                    failing_func()
                
                assert str(exc_info.value) == "Test error"


def test_trace_fallback_on_error():
    """Test trace decorator fallback when setup fails."""
    @trace()
    def fallback_func(x: int) -> int:
        return x + 1000
    
    # Mock settings to cause failure
    with patch('src.lilypad.traces.get_settings', side_effect=Exception("Settings error")):
        # Should fallback to original function
        result = fallback_func(1)
        assert result == 1001


@pytest.mark.asyncio
async def test_async_trace_fallback():
    """Test async trace fallback on error."""
    @trace()
    async def async_fallback_func(x: int) -> int:
        return x + 2000
    
    with patch('src.lilypad.traces.get_settings', side_effect=Exception("Async settings error")):
        result = await async_fallback_func(1)
        assert result == 2001


def test_trace_with_trace_ctx_parameter():
    """Test trace decorator with trace_ctx parameter."""
    @trace()
    def func_with_trace_ctx(x: int, trace_ctx=None) -> int:
        return x * 2
    
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project", api_key="test-key")
        
        with patch('src.lilypad.traces.get_sync_client') as mock_client:
            with patch('src.lilypad.traces.Span') as mock_span_class:
                mock_span = Mock(span_id=12345, opentelemetry_span=Mock())
                mock_span_context = Mock()
                mock_span_context.__enter__ = Mock(return_value=mock_span)
                mock_span_context.__exit__ = Mock(return_value=None)
                mock_span_class.return_value = mock_span_context
                
                # Call without trace_ctx
                result = func_with_trace_ctx(5)
                assert result == 10
                
                # Call with trace_ctx
                result = func_with_trace_ctx(5, trace_ctx=Mock())
                assert result == 10


def test_trace_with_binding_error():
    """Test trace decorator handling TypeError in argument binding."""
    @trace()
    def bind_error_func(trace_ctx, x: int) -> int:
        return x * 2
    
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project", api_key="test-key")
        
        with patch('src.lilypad.traces.get_sync_client') as mock_client:
            with patch('src.lilypad.traces.Span') as mock_span_class:
                mock_span = Mock(span_id=12345, opentelemetry_span=Mock())
                mock_span_context = Mock()
                mock_span_context.__enter__ = Mock(return_value=mock_span)
                mock_span_context.__exit__ = Mock(return_value=None)
                mock_span_class.return_value = mock_span_context
                
                with patch('src.lilypad.traces.get_signature') as mock_get_sig:
                    mock_sig = Mock()
                    mock_sig.parameters = {"trace_ctx": Mock(), "x": Mock()}
                    mock_sig.bind.side_effect = TypeError("Binding failed")
                    mock_get_sig.return_value = mock_sig
                    
                    with patch('src.lilypad.traces._set_span_attributes') as mock_set_attrs:
                        mock_ctx = Mock()
                        mock_ctx.__enter__ = Mock()
                        mock_ctx.__exit__ = Mock(return_value=None)
                        mock_set_attrs.return_value = mock_ctx
                        
                        # Should still work despite binding error
                        result = bind_error_func(10)
                        assert result == 20


def test_function_creation_when_not_found():
    """Test function creation when not found in API."""
    @trace(versioning="automatic")
    def new_func():
        return "new"
    
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project", api_key="test-key")
        
        with patch('src.lilypad.traces.get_sync_client') as mock_client:
            mock_lilypad = Mock()
            mock_client.return_value = mock_lilypad
            
            with patch('src.lilypad.traces.Closure') as mock_closure_class:
                mock_closure = Mock(hash="new-hash", code="code", name="new_func", signature="sig", dependencies=[])
                mock_closure_class.from_fn.return_value = mock_closure
                
                with patch('src.lilypad.traces.get_function_by_hash_sync', side_effect=NotFoundError("Not found")):
                    # Should create new function
                    mock_lilypad.projects.functions.create.return_value = Mock(uuid_="new-uuid")
                    
                    with patch('src.lilypad.traces.Span') as mock_span_class:
                        mock_span = Mock(span_id=12345, opentelemetry_span=Mock())
                        mock_span_context = Mock()
                        mock_span_context.__enter__ = Mock(return_value=mock_span)
                        mock_span_context.__exit__ = Mock(return_value=None)
                        mock_span_class.return_value = mock_span_context
                        
                        result = new_func()
                        assert result == "new"
                        
                        # Verify function was created
                        mock_lilypad.projects.functions.create.assert_called_once()


def test_remote_function_error():
    """Test RemoteFunctionError handling."""
    @trace(versioning="automatic")
    def error_func():
        return "error"
    
    with patch('src.lilypad.traces.get_settings') as mock_settings:
        mock_settings.return_value = Mock(project_id="test-project")
        
        with patch('src.lilypad.traces.get_deployed_function_sync') as mock_get_deployed:
            mock_get_deployed.return_value = Mock()
            
            with patch('src.lilypad.traces.get_cached_closure') as mock_get_cached:
                mock_get_cached.return_value = Mock()
                
                with patch('src.lilypad.traces.SubprocessSandboxRunner') as mock_sandbox_class:
                    mock_sandbox = Mock()
                    mock_sandbox.execute_function.return_value = {"error": "Test execution error"}
                    mock_sandbox_class.return_value = mock_sandbox
                    
                    with pytest.raises(RemoteFunctionError) as exc_info:
                        error_func.remote()
                    
                    assert "Test execution error" in str(exc_info.value)


# =============================================================================
# Protocol Type Tests
# =============================================================================


def test_protocol_type_imports():
    """Test that protocol types can be imported."""
    # These are Protocol types with ... implementations
    assert SyncVersionedFunction is not None
    assert AsyncVersionedFunction is not None
    assert TraceDecoratedFunctionWithContext is not None
    assert WrappedTraceDecorator is not None
    assert TraceDecorator is not None
    assert VersionedFunctionTraceDecorator is not None
    assert WrappedVersionedFunctionTraceDecorator is not None


# =============================================================================
# Helper Functions
# =============================================================================


def format_span_id(span_id: int) -> str:
    """Helper to format span ID."""
    from opentelemetry.trace import format_span_id
    return format_span_id(span_id)