"""Test to achieve 100% coverage in spans.py"""

import pytest
from unittest.mock import Mock, patch
from src.lilypad.spans import Span


class TestSpansFinalCoverage:
    """Target the missing lines in spans.py for 100% coverage."""
    
    def test_span_metadata_exception_handling_lines_145_146(self):
        """Test lines 145-146: JSON serialization exception handling."""
        span = Span("test-span")
        # Need to manually set up the span since we can't easily test the context manager
        span._span = Mock()
        
        # Create object that can't be JSON serialized
        class UnserializableObject:
            def __init__(self):
                self.circular_ref = self
        
        unserializable = UnserializableObject()
        
        # This should trigger the JSON exception and fallback to str()
        span.metadata(unserializable)
        
        # Verify fallback was used
        span._span.set_attribute.assert_called_with("lilypad.metadata", str([unserializable]))
    
    def test_span_metadata_empty_case_line_155(self):
        """Test line 155: Early return when no args or kwargs."""
        span = Span("test-span")
        span._span = Mock()
        
        # Call metadata with no arguments - should return early
        span.metadata()
        
        # Should not have called set_attribute
        span._span.set_attribute.assert_not_called()
    
    def test_span_metadata_value_serialization_exception_lines_160_163(self):
        """Test lines 160-163: Value serialization exception handling."""
        span = Span("test-span")
        span._span = Mock()
        
        # Create an object that can't be JSON serialized
        class UnserializableValue:
            def __init__(self):
                self.circular_ref = self
        
        unserializable_value = UnserializableValue()
        
        # Pass as kwargs to trigger individual attribute processing
        span.metadata(test_key=unserializable_value)
        
        # Should have two calls: one for the key and one for lilypad.metadata
        # Check that the key was set with the str() fallback
        calls = span._span.set_attribute.call_args_list
        assert len(calls) >= 1
        # Look for the call with our test_key
        key_call = next((call for call in calls if call[0][0] == "test_key"), None)
        assert key_call is not None
        assert key_call[0][1] == str(unserializable_value)
    
    def test_span_metadata_dict_copy_lines_138_139(self):
        """Test lines 138-139: Normal dict copy and merge with kwargs."""
        span = Span("test-span")
        span._span = Mock()
        
        # Pass a normal dict that can be copied
        test_dict = {"arg_key": "arg_value"}
        
        span.metadata(test_dict, kwarg_key="kwarg_value")
        
        # Should have called set_attribute for both the dict and kwargs
        calls = span._span.set_attribute.call_args_list
        call_keys = [call[0][0] for call in calls]
        assert "arg_key" in call_keys
        assert "kwarg_key" in call_keys
    
    def test_span_id_noop_line_183(self):
        """Test line 183: Span ID when noop is True."""
        span = Span("test-span")
        span._noop = True
        span._span_id = 12345
        
        # Should return the _span_id when noop
        assert span.span_id == 12345
    
    def test_span_id_with_span_line_187(self):
        """Test line 187: Span ID from actual span context."""
        span = Span("test-span")
        span._noop = False
        
        # Mock span with context
        mock_span = Mock()
        mock_context = Mock()
        mock_context.span_id = 98765
        mock_span.get_span_context.return_value = mock_context
        span._span = mock_span
        
        # Should get span_id from context
        assert span.span_id == 98765
    
    def test_opentelemetry_span_noop_line_192(self):
        """Test line 192: OpenTelemetry span when noop."""
        span = Span("test-span")
        span._noop = True
        span._span = Mock()  # This should be ignored
        
        # Should return None when noop
        assert span.opentelemetry_span is None
    
    def test_span_function_line_197(self):
        """Test line 197: Convenience span function."""
        from src.lilypad.spans import span as span_func
        
        # Should create a Span instance
        result = span_func("test-span")
        assert isinstance(result, Span)
        assert result.name == "test-span"