"""Comprehensive tests to achieve 100% coverage for spans.py."""

import pytest
import datetime
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import Any

from src.lilypad.spans import Span
from opentelemetry.trace import StatusCode
from opentelemetry.sdk.trace import TracerProvider


class TestSpanInitialization:
    """Tests for Span initialization."""
    
    def test_span_init(self):
        """Test Span initialization."""
        span = Span("test_span")
        
        assert span.name == "test_span"
        assert span._span is None
        assert span._span_cm is None
        assert span._order_cm is None
        assert span._finished is False
        assert span._token is None
        assert span._noop is False
        assert span._span_id == 0


class TestSpanContextManager:
    """Tests for Span context manager functionality."""
    
    @patch('src.lilypad.spans.get_tracer_provider')
    @patch('src.lilypad.spans.logging.getLogger')
    def test_enter_not_configured_warning(self, mock_get_logger, mock_get_tracer_provider):
        """Test __enter__ when tracer is not configured (first time warning)."""
        # Mock non-TracerProvider
        mock_provider = Mock()
        mock_provider.__class__ = object  # Not TracerProvider
        mock_get_tracer_provider.return_value = mock_provider
        
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        
        # Reset the class variable to ensure warning is shown
        Span._warned_not_configured = False
        
        span = Span("test_span")
        
        with span as s:
            assert s is span
            assert span._noop is True
            
        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        assert Span._warned_not_configured is True

    @patch('src.lilypad.spans.get_tracer_provider')
    def test_enter_not_configured_no_warning_second_time(self, mock_get_tracer_provider):
        """Test __enter__ when tracer is not configured (no warning second time)."""
        # Mock non-TracerProvider
        mock_provider = Mock()
        mock_provider.__class__ = object  # Not TracerProvider
        mock_get_tracer_provider.return_value = mock_provider
        
        # Set the class variable to indicate warning already shown
        Span._warned_not_configured = True
        
        span = Span("test_span")
        
        with patch('src.lilypad.spans.logging.getLogger') as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger
            
            with span as s:
                assert s is span
                assert span._noop is True
                
            # Verify no warning was logged this time
            mock_logger.warning.assert_not_called()

    @patch('src.lilypad.spans.get_tracer_provider')
    @patch('src.lilypad.spans.get_tracer')
    @patch('src.lilypad.spans.SESSION_CONTEXT')
    @patch('src.lilypad.spans.context_api')
    @patch('src.lilypad.spans.set_span_in_context')
    def test_enter_configured_with_session(
        self, mock_set_span, mock_context_api, mock_session_context, 
        mock_get_tracer, mock_get_tracer_provider
    ):
        """Test __enter__ when properly configured with session."""
        # Mock TracerProvider
        mock_provider = TracerProvider()
        mock_get_tracer_provider.return_value = mock_provider
        
        # Mock tracer and span
        mock_tracer = Mock()
        mock_otel_span = Mock()
        mock_tracer.start_span.return_value = mock_otel_span
        mock_get_tracer.return_value = mock_tracer
        
        # Mock session
        mock_session = Mock()
        mock_session.id = "session-123"
        mock_session_context.get.return_value = mock_session
        
        # Mock context operations
        mock_current_context = Mock()
        mock_context_api.get_current.return_value = mock_current_context
        mock_new_context = Mock()
        mock_set_span.return_value = mock_new_context
        mock_token = "test-token"
        mock_context_api.attach.return_value = mock_token
        
        span = Span("test_span")
        
        with patch.object(span, 'metadata') as mock_metadata:
            with span as s:
                assert s is span
                assert span._noop is False
                
                # Verify span setup
                mock_tracer.start_span.assert_called_once_with("test_span")
                mock_otel_span.set_attribute.assert_any_call("lilypad.type", "trace")
                mock_otel_span.set_attribute.assert_any_call("lilypad.session_id", "session-123")
                
                # Verify context operations
                mock_context_api.get_current.assert_called_once()
                mock_set_span.assert_called_once_with(mock_otel_span, mock_current_context)
                mock_context_api.attach.assert_called_once_with(mock_new_context)
                
                # Verify metadata call
                mock_metadata.assert_called_once()
                call_args = mock_metadata.call_args[1]
                assert 'timestamp' in call_args
                
                assert span._token == mock_token

    @patch('src.lilypad.spans.get_tracer_provider')
    @patch('src.lilypad.spans.get_tracer')
    @patch('src.lilypad.spans.SESSION_CONTEXT')
    @patch('src.lilypad.spans.context_api')
    @patch('src.lilypad.spans.set_span_in_context')
    def test_enter_configured_no_session(
        self, mock_set_span, mock_context_api, mock_session_context,
        mock_get_tracer, mock_get_tracer_provider
    ):
        """Test __enter__ when properly configured but no session."""
        # Mock TracerProvider
        mock_provider = TracerProvider()
        mock_get_tracer_provider.return_value = mock_provider
        
        # Mock tracer and span
        mock_tracer = Mock()
        mock_otel_span = Mock()
        mock_tracer.start_span.return_value = mock_otel_span
        mock_get_tracer.return_value = mock_tracer
        
        # Mock no session
        mock_session_context.get.return_value = None
        
        # Mock context operations
        mock_current_context = Mock()
        mock_context_api.get_current.return_value = mock_current_context
        mock_new_context = Mock()
        mock_set_span.return_value = mock_new_context
        mock_token = "test-token"
        mock_context_api.attach.return_value = mock_token
        
        span = Span("test_span")
        
        with patch.object(span, 'metadata'):
            with span as s:
                assert s is span
                
                # Should not set session_id attribute
                mock_otel_span.set_attribute.assert_called_once_with("lilypad.type", "trace")

    @patch('src.lilypad.spans.get_tracer_provider')
    @patch('src.lilypad.spans.get_tracer')
    @patch('src.lilypad.spans.SESSION_CONTEXT')
    @patch('src.lilypad.spans.context_api')
    @patch('src.lilypad.spans.set_span_in_context')
    def test_enter_configured_session_no_id(
        self, mock_set_span, mock_context_api, mock_session_context,
        mock_get_tracer, mock_get_tracer_provider
    ):
        """Test __enter__ when session exists but has no ID."""
        # Mock TracerProvider
        mock_provider = TracerProvider()
        mock_get_tracer_provider.return_value = mock_provider
        
        # Mock tracer and span
        mock_tracer = Mock()
        mock_otel_span = Mock()
        mock_tracer.start_span.return_value = mock_otel_span
        mock_get_tracer.return_value = mock_tracer
        
        # Mock session without ID
        mock_session = Mock()
        mock_session.id = None
        mock_session_context.get.return_value = mock_session
        
        # Mock context operations
        mock_current_context = Mock()
        mock_context_api.get_current.return_value = mock_current_context
        mock_new_context = Mock()
        mock_set_span.return_value = mock_new_context
        mock_context_api.attach.return_value = "test-token"
        
        span = Span("test_span")
        
        with patch.object(span, 'metadata'):
            with span as s:
                assert s is span
                
                # Should not set session_id attribute
                mock_otel_span.set_attribute.assert_called_once_with("lilypad.type", "trace")

    def test_exit_noop(self):
        """Test __exit__ when span is noop."""
        span = Span("test_span")
        span._noop = True
        
        # Should not raise any exceptions
        span.__exit__(None, None, None)
        assert span._finished is False  # Not set when noop

    @patch('src.lilypad.spans.context_api')
    def test_exit_with_exception(self, mock_context_api):
        """Test __exit__ when an exception occurred."""
        span = Span("test_span")
        span._noop = False
        
        # Mock span
        mock_otel_span = Mock()
        span._span = mock_otel_span
        span._token = "test-token"
        
        # Mock exception
        exc_type = ValueError
        exc_val = ValueError("Test exception")
        exc_tb = None
        
        span.__exit__(exc_type, exc_val, exc_tb)
        
        # Verify exception was recorded and span was ended
        mock_otel_span.record_exception.assert_called_once_with(exc_val)
        mock_otel_span.end.assert_called_once()
        mock_context_api.detach.assert_called_once_with("test-token")
        assert span._finished is True

    @patch('src.lilypad.spans.context_api')
    def test_exit_no_exception(self, mock_context_api):
        """Test __exit__ when no exception occurred."""
        span = Span("test_span")
        span._noop = False
        
        # Mock span
        mock_otel_span = Mock()
        span._span = mock_otel_span
        span._token = "test-token"
        
        span.__exit__(None, None, None)
        
        # Verify span was ended but no exception recorded
        mock_otel_span.record_exception.assert_not_called()
        mock_otel_span.end.assert_called_once()
        mock_context_api.detach.assert_called_once_with("test-token")
        assert span._finished is True

    @patch('src.lilypad.spans.context_api')
    def test_exit_no_token(self, mock_context_api):
        """Test __exit__ when no token was set."""
        span = Span("test_span")
        span._noop = False
        span._token = None
        
        # Mock span
        mock_otel_span = Mock()
        span._span = mock_otel_span
        
        span.__exit__(None, None, None)
        
        # Verify detach was not called
        mock_context_api.detach.assert_not_called()
        assert span._finished is True

    def test_exit_exception_type_but_no_value(self):
        """Test __exit__ when exception type exists but no value."""
        span = Span("test_span")
        span._noop = False
        
        # Mock span
        mock_otel_span = Mock()
        span._span = mock_otel_span
        
        span.__exit__(ValueError, None, None)
        
        # Should not record exception since exc_val is None
        mock_otel_span.record_exception.assert_not_called()
        mock_otel_span.end.assert_called_once()

    def test_exit_no_span(self):
        """Test __exit__ when span is None."""
        span = Span("test_span")
        span._noop = False
        span._span = None
        
        # Should not raise any exceptions
        span.__exit__(None, None, None)
        assert span._finished is True


class TestSpanAsyncContextManager:
    """Tests for Span async context manager functionality."""
    
    @pytest.mark.asyncio
    async def test_aenter(self):
        """Test async __aenter__."""
        span = Span("test_span")
        
        with patch.object(span, '__enter__', return_value=span) as mock_enter:
            result = await span.__aenter__()
            
            mock_enter.assert_called_once()
            assert result is span

    @pytest.mark.asyncio
    async def test_aexit(self):
        """Test async __aexit__."""
        span = Span("test_span")
        
        with patch.object(span, '__exit__') as mock_exit:
            exc_value = ValueError("test")
            await span.__aexit__(ValueError, exc_value, None)
            
            mock_exit.assert_called_once_with(ValueError, exc_value, None)


class TestSpanLogging:
    """Tests for Span logging methods."""
    
    def test_log_event_with_span(self):
        """Test _log_event when span exists."""
        span = Span("test_span")
        
        # Mock span
        mock_otel_span = Mock()
        span._span = mock_otel_span
        
        span._log_event("info", "Test message", key1="value1", key2="value2")
        
        # Verify event was added
        mock_otel_span.add_event.assert_called_once_with(
            "info",
            attributes={
                "info.message": "Test message",
                "key1": "value1",
                "key2": "value2"
            }
        )
        # Should not set error status for info level
        mock_otel_span.set_status.assert_not_called()

    def test_log_event_error_level(self):
        """Test _log_event with error level."""
        span = Span("test_span")
        
        # Mock span
        mock_otel_span = Mock()
        span._span = mock_otel_span
        
        span._log_event("error", "Error message")
        
        # Verify error status was set
        mock_otel_span.set_status.assert_called_once_with(StatusCode.ERROR)
        mock_otel_span.add_event.assert_called_once_with(
            "error",
            attributes={"error.message": "Error message"}
        )

    def test_log_event_critical_level(self):
        """Test _log_event with critical level."""
        span = Span("test_span")
        
        # Mock span
        mock_otel_span = Mock()
        span._span = mock_otel_span
        
        span._log_event("critical", "Critical message")
        
        # Verify error status was set
        mock_otel_span.set_status.assert_called_once_with(StatusCode.ERROR)

    def test_log_event_no_span(self):
        """Test _log_event when span is None."""
        span = Span("test_span")
        span._span = None
        
        # Should not raise any exceptions
        span._log_event("info", "Test message")

    def test_debug_method(self):
        """Test debug logging method."""
        span = Span("test_span")
        
        with patch.object(span, '_log_event') as mock_log_event:
            span.debug("Debug message", key="value")
            
            mock_log_event.assert_called_once_with("debug", "Debug message", key="value")

    def test_info_method(self):
        """Test info logging method."""
        span = Span("test_span")
        
        with patch.object(span, '_log_event') as mock_log_event:
            span.info("Info message", key="value")
            
            mock_log_event.assert_called_once_with("info", "Info message", key="value")

    def test_warning_method(self):
        """Test warning logging method."""
        span = Span("test_span")
        
        with patch.object(span, '_log_event') as mock_log_event:
            span.warning("Warning message", key="value")
            
            mock_log_event.assert_called_once_with("warning", "Warning message", key="value")

    def test_error_method(self):
        """Test error logging method."""
        span = Span("test_span")
        
        with patch.object(span, '_log_event') as mock_log_event:
            span.error("Error message", key="value")
            
            mock_log_event.assert_called_once_with("error", "Error message", key="value")

    def test_critical_method(self):
        """Test critical logging method."""
        span = Span("test_span")
        
        with patch.object(span, '_log_event') as mock_log_event:
            span.critical("Critical message", key="value")
            
            mock_log_event.assert_called_once_with("critical", "Critical message", key="value")

    def test_log_method(self):
        """Test log method."""
        span = Span("test_span")
        
        with patch.object(span, '_log_event') as mock_log_event:
            span.log("Log message", key="value")
            
            mock_log_event.assert_called_once_with("info", "Log message", key="value")


class TestSpanMetadata:
    """Tests for Span metadata functionality."""
    
    def test_metadata_with_span(self):
        """Test metadata when span exists."""
        span = Span("test_span")
        
        # Mock span
        mock_otel_span = Mock()
        span._span = mock_otel_span
        
        span.metadata(key1="value1", key2="value2")
        
        # Verify attributes were set
        mock_otel_span.set_attribute.assert_any_call("key1", "value1")
        mock_otel_span.set_attribute.assert_any_call("key2", "value2")

    def test_metadata_no_span(self):
        """Test metadata when span is None."""
        span = Span("test_span")
        span._span = None
        
        # Should not raise any exceptions
        span.metadata("arg1", key1="value1")

    def test_metadata_only_kwargs(self):
        """Test metadata with only keyword arguments."""
        span = Span("test_span")
        
        # Mock span
        mock_otel_span = Mock()
        span._span = mock_otel_span
        
        span.metadata(key1="value1", key2="value2")
        
        # Should not set lilypad.metadata for empty args
        mock_otel_span.set_attribute.assert_any_call("key1", "value1")
        mock_otel_span.set_attribute.assert_any_call("key2", "value2")
        
        # Check that lilypad.metadata was called with empty list
        calls = mock_otel_span.set_attribute.call_args_list
        metadata_calls = [call for call in calls if call[0][0] == "lilypad.metadata"]
        assert len(metadata_calls) == 1
        assert metadata_calls[0][0][1] == "[]"

    def test_metadata_only_args(self):
        """Test metadata with only positional arguments."""
        span = Span("test_span")
        
        # Mock span
        mock_otel_span = Mock()
        span._span = mock_otel_span
        
        span.metadata("arg1", "arg2")
        
        # Should only set lilypad.metadata
        mock_otel_span.set_attribute.assert_called_once_with("lilypad.metadata", '["arg1","arg2"]')


class TestSpanFinish:
    """Tests for Span finish functionality."""
    
    def test_finish_with_span(self):
        """Test finish when span exists."""
        span = Span("test_span")
        
        # Mock span
        mock_otel_span = Mock()
        span._span = mock_otel_span
        
        span.finish()
        
        # Verify span was ended
        mock_otel_span.end.assert_called_once()
        assert span._finished is True

    def test_finish_no_span(self):
        """Test finish when span is None."""
        span = Span("test_span")
        span._span = None
        
        # Should not raise any exceptions
        span.finish()
        assert span._finished is True

    def test_finish_already_finished(self):
        """Test finish when already finished."""
        span = Span("test_span")
        span._finished = True
        
        # Mock span
        mock_otel_span = Mock()
        span._span = mock_otel_span
        
        span.finish()
        
        # Should not end span again
        mock_otel_span.end.assert_not_called()


class TestSpanProperties:
    """Tests for Span properties."""
    
    def test_span_id_with_span(self):
        """Test span_id property when span exists."""
        span = Span("test_span")
        
        # Mock span with span_id
        mock_otel_span = Mock()
        mock_otel_span.get_span_context.return_value.span_id = 12345
        span._span = mock_otel_span
        
        result = span.span_id
        
        assert result == 12345

    def test_span_id_no_span(self):
        """Test span_id property when span is None."""
        span = Span("test_span")
        span._span = None
        
        result = span.span_id
        
        assert result == 0

    def test_opentelemetry_span_property(self):
        """Test opentelemetry_span property."""
        span = Span("test_span")
        
        # Mock span
        mock_otel_span = Mock()
        span._span = mock_otel_span
        
        result = span.opentelemetry_span
        
        assert result is mock_otel_span

    def test_opentelemetry_span_property_none(self):
        """Test opentelemetry_span property when None."""
        span = Span("test_span")
        span._span = None
        
        result = span.opentelemetry_span
        
        assert result is None


class TestSpanClassVariable:
    """Tests for Span class variables."""
    
    def test_warned_not_configured_default(self):
        """Test _warned_not_configured default value."""
        # Reset to default
        Span._warned_not_configured = False
        assert Span._warned_not_configured is False


class TestSpanIntegration:
    """Integration tests for Span functionality."""
    
    @patch('src.lilypad.spans.get_tracer_provider')
    @patch('src.lilypad.spans.get_tracer')
    @patch('src.lilypad.spans.SESSION_CONTEXT')
    @patch('src.lilypad.spans.context_api')
    @patch('src.lilypad.spans.set_span_in_context')
    def test_full_span_lifecycle(
        self, mock_set_span, mock_context_api, mock_session_context,
        mock_get_tracer, mock_get_tracer_provider
    ):
        """Test full span lifecycle with logging and metadata."""
        # Setup mocks
        mock_provider = TracerProvider()
        mock_get_tracer_provider.return_value = mock_provider
        
        mock_tracer = Mock()
        mock_otel_span = Mock()
        mock_tracer.start_span.return_value = mock_otel_span
        mock_get_tracer.return_value = mock_tracer
        
        mock_session_context.get.return_value = None
        mock_context_api.get_current.return_value = Mock()
        mock_set_span.return_value = Mock()
        mock_context_api.attach.return_value = "token"
        
        # Test full lifecycle
        span = Span("integration_test")
        
        with span:
            # Test logging
            span.debug("Debug message")
            span.info("Info message")
            span.warning("Warning message")
            span.error("Error message")
            span.critical("Critical message")
            span.log("Log message")
            
            # Test metadata
            span.metadata("meta1", "meta2", custom_key="custom_value")
            
            # Test properties
            mock_otel_span.get_span_context.return_value.span_id = 54321
            assert span.span_id == 54321
            assert span.opentelemetry_span is mock_otel_span
            
            # Test finish (manual)
            span.finish()
        
        # Verify all interactions
        assert mock_otel_span.set_attribute.call_count >= 3  # At least timestamp, metadata, custom_key
        assert mock_otel_span.add_event.call_count == 6  # All log events
        assert mock_otel_span.set_status.call_count == 2  # Error and critical levels
        assert mock_otel_span.end.call_count == 2  # Manual finish + context manager exit