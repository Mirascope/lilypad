"""Test connection error handling for versioning."""

import pytest
from unittest.mock import Mock, patch
from contextlib import contextmanager

from lilypad.traces import trace
from lilypad.exceptions import LilypadException


@pytest.mark.asyncio
async def test_trace_versioning_automatic_connection_error():
    """Test that LLM calls succeed even when Lilypad server connection fails with versioning=automatic."""
    
    # Create a mock span that works as a context manager
    class MockSpan:
        def __init__(self, name):
            self.name = name
            self.is_noop = False
            self.span_id = 123456789
            self.opentelemetry_span = Mock()
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            pass
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, *args):
            pass
    
    with patch("lilypad.traces.get_tracer_provider") as mock_get_tracer_provider, \
         patch("lilypad.traces.TracerProvider") as mock_tracer_provider_class, \
         patch("lilypad.traces.get_settings") as mock_get_settings, \
         patch("lilypad.traces.get_async_client") as mock_get_async_client, \
         patch("lilypad.traces.Closure") as mock_closure_class, \
         patch("lilypad.traces.get_function_by_hash_async") as mock_get_function_by_hash, \
         patch("lilypad.traces.Span", MockSpan), \
         patch("lilypad.traces._construct_trace_attributes") as mock_construct_attrs, \
         patch("lilypad.traces._set_span_attributes") as mock_set_span_attrs, \
         patch("lilypad.traces._set_trace_context") as mock_set_trace_context:
        
        # Setup tracer provider
        mock_provider_instance = Mock()
        mock_tracer_provider_class.return_value = mock_provider_instance
        mock_get_tracer_provider.return_value = mock_provider_instance
        
        # Setup settings
        mock_get_settings.return_value = Mock(
            api_key="test-key",
            project_id="test-project",
        )
        
        # Mock connection error (OSError with errno -2)
        mock_get_function_by_hash.side_effect = OSError(-2, "Name or service not known")
        
        # Mock closure
        mock_closure = Mock()
        mock_closure.hash = "test-hash"
        mock_closure.code = "test-code"
        mock_closure.name = "test-func"
        mock_closure.signature = "test-signature"
        mock_closure.dependencies = []
        mock_closure_class.from_fn.return_value = mock_closure
        
        # Mock construct attributes
        mock_construct_attrs.return_value = {}
        
        # Mock _set_span_attributes as a context manager
        @contextmanager
        def mock_span_attributes_cm(*args, **kwargs):
            result_holder = Mock()
            yield result_holder
            
        mock_set_span_attrs.side_effect = mock_span_attributes_cm
        
        # Create test function with versioning=automatic
        @trace(versioning="automatic")
        async def test_function(x: int) -> int:
            return x * 2
        
        # Call should succeed despite connection error
        with patch("lilypad.traces.logger") as mock_logger:
            result = await test_function(5)
            
            # Verify function was called and returned correct result
            assert result == 10
            
            # Verify error was logged
            mock_logger.error.assert_called_once()
            assert "Failed to connect to Lilypad server for versioning" in mock_logger.error.call_args[0][0]
            assert "LLM calls will still work" in mock_logger.error.call_args[0][0]


def test_trace_versioning_automatic_connection_error_sync():
    """Test that LLM calls succeed even when Lilypad server connection fails with versioning=automatic (sync version)."""
    
    # Create a mock span that works as a context manager
    class MockSpan:
        def __init__(self, name):
            self.name = name
            self.is_noop = False
            self.span_id = 123456789
            self.opentelemetry_span = Mock()
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            pass
    
    with patch("lilypad.traces.get_tracer_provider") as mock_get_tracer_provider, \
         patch("lilypad.traces.TracerProvider") as mock_tracer_provider_class, \
         patch("lilypad.traces.get_settings") as mock_get_settings, \
         patch("lilypad.traces.get_sync_client") as mock_get_sync_client, \
         patch("lilypad.traces.Closure") as mock_closure_class, \
         patch("lilypad.traces.get_function_by_hash_sync") as mock_get_function_by_hash, \
         patch("lilypad.traces.Span", MockSpan), \
         patch("lilypad.traces._construct_trace_attributes") as mock_construct_attrs, \
         patch("lilypad.traces._set_span_attributes") as mock_set_span_attrs, \
         patch("lilypad.traces._set_trace_context") as mock_set_trace_context:
        
        # Setup tracer provider
        mock_provider_instance = Mock()
        mock_tracer_provider_class.return_value = mock_provider_instance
        mock_get_tracer_provider.return_value = mock_provider_instance
        
        # Setup settings
        mock_get_settings.return_value = Mock(
            api_key="test-key",
            project_id="test-project",
        )
        
        # Mock connection error (OSError with errno -2)
        mock_get_function_by_hash.side_effect = OSError(-2, "Name or service not known")
        
        # Mock closure
        mock_closure = Mock()
        mock_closure.hash = "test-hash"
        mock_closure.code = "test-code"
        mock_closure.name = "test-func"
        mock_closure.signature = "test-signature"
        mock_closure.dependencies = []
        mock_closure_class.from_fn.return_value = mock_closure
        
        # Mock construct attributes
        mock_construct_attrs.return_value = {}
        
        # Mock _set_span_attributes as a context manager
        @contextmanager
        def mock_span_attributes_cm(*args, **kwargs):
            result_holder = Mock()
            yield result_holder
            
        mock_set_span_attrs.side_effect = mock_span_attributes_cm
        
        # Create test function with versioning=automatic
        @trace(versioning="automatic")
        def test_function(x: int) -> int:
            return x * 2
        
        # Call should succeed despite connection error
        with patch("lilypad.traces.logger") as mock_logger:
            result = test_function(5)
            
            # Verify function was called and returned correct result
            assert result == 10
            
            # Verify error was logged
            mock_logger.error.assert_called_once()
            assert "Failed to connect to Lilypad server for versioning" in mock_logger.error.call_args[0][0]
            assert "LLM calls will still work" in mock_logger.error.call_args[0][0]


@pytest.mark.asyncio
async def test_trace_versioning_automatic_lilypad_api_error():
    """Test that LLM calls succeed when Lilypad API returns error (debug logging only)."""
    
    # Create a mock span that works as a context manager
    class MockSpan:
        def __init__(self, name):
            self.name = name
            self.is_noop = False
            self.span_id = 123456789
            self.opentelemetry_span = Mock()
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            pass
            
        async def __aenter__(self):
            return self
            
        async def __aexit__(self, *args):
            pass
    
    with patch("lilypad.traces.get_tracer_provider") as mock_get_tracer_provider, \
         patch("lilypad.traces.TracerProvider") as mock_tracer_provider_class, \
         patch("lilypad.traces.get_settings") as mock_get_settings, \
         patch("lilypad.traces.get_async_client") as mock_get_async_client, \
         patch("lilypad.traces.Closure") as mock_closure_class, \
         patch("lilypad.traces.get_function_by_hash_async") as mock_get_function_by_hash, \
         patch("lilypad.traces.Span", MockSpan), \
         patch("lilypad.traces._construct_trace_attributes") as mock_construct_attrs, \
         patch("lilypad.traces._set_span_attributes") as mock_set_span_attrs, \
         patch("lilypad.traces._set_trace_context") as mock_set_trace_context:
        
        # Setup tracer provider
        mock_provider_instance = Mock()
        mock_tracer_provider_class.return_value = mock_provider_instance
        mock_get_tracer_provider.return_value = mock_provider_instance
        
        # Setup settings
        mock_get_settings.return_value = Mock(
            api_key="test-key",
            project_id="test-project",
        )
        
        # Mock LilypadException
        mock_get_function_by_hash.side_effect = LilypadException("API error")
        
        # Mock closure
        mock_closure = Mock()
        mock_closure.hash = "test-hash"
        mock_closure.code = "test-code"
        mock_closure.name = "test-func"
        mock_closure.signature = "test-signature"
        mock_closure.dependencies = []
        mock_closure_class.from_fn.return_value = mock_closure
        
        # Mock construct attributes
        mock_construct_attrs.return_value = {}
        
        # Mock _set_span_attributes as a context manager
        @contextmanager
        def mock_span_attributes_cm(*args, **kwargs):
            result_holder = Mock()
            yield result_holder
            
        mock_set_span_attrs.side_effect = mock_span_attributes_cm
        
        # Create test function with versioning=automatic
        @trace(versioning="automatic")
        async def test_function(x: int) -> int:
            return x * 2
        
        # Call should succeed despite API error
        with patch("lilypad.traces.logger") as mock_logger:
            result = await test_function(5)
            
            # Verify function was called and returned correct result
            assert result == 10
            
            # Verify error was logged at debug level
            mock_logger.debug.assert_called_once()
            assert "Lilypad API error during versioning" in mock_logger.debug.call_args[0][0]
            assert "Continuing without versioning" in mock_logger.debug.call_args[0][0]