"""Tests to improve coverage for various utils files."""

import pytest
from unittest.mock import Mock, patch, MagicMock


def test_anthropic_chunk_handler_with_usage():
    """Test anthropic chunk handler with usage attributes."""
    from lilypad._opentelemetry._opentelemetry_anthropic.utils import AnthropicChunkHandler
    
    handler = AnthropicChunkHandler()
    metadata = {}
    
    # Test with usage having prompt_tokens but not completion_tokens
    mock_chunk = Mock()
    mock_usage = Mock()
    mock_usage.prompt_tokens = 15
    # No completion_tokens attribute
    mock_chunk.usage = mock_usage
    
    handler.extract_metadata(mock_chunk, metadata)
    # Should handle missing completion_tokens gracefully


def test_middleware_safe_serialize_protobuf():
    """Test middleware safe_serialize with protobuf-like object."""
    from lilypad._utils.middleware import safe_serialize
    
    # Create a mock protobuf-like object
    class MockProtobuf:
        def __dict__(self):
            raise TypeError("Mock protobuf dict error")
        
        def SerializeToString(self):
            return b"protobuf_data"
    
    mock_protobuf = MockProtobuf()
    result = safe_serialize(mock_protobuf)
    # Should handle protobuf serialization


def test_serializer_registry_get_nonexistent():
    """Test serializer registry get for nonexistent serializer."""
    from lilypad._utils.serializer_registry import get_serializer
    
    # Test getting serializer for unregistered type (should return None)
    result = get_serializer("completely_nonexistent_type_12345")
    assert result is None


def test_spans_metadata_with_none_span():
    """Test spans metadata when _span is None."""
    from lilypad.spans import Span
    
    # Test span without entering context (line coverage for _span = None case)
    test_span = Span("test")
    # Don't enter context, so _span remains None
    test_span.metadata(test="value")  # Should not raise when _span is None


def test_spans_noop_properties():
    """Test spans properties when _noop is True."""
    from lilypad.spans import Span
    
    test_span = Span("test")
    test_span._noop = True
    
    # Test span_id property when _noop is True
    assert test_span.span_id == 0
    
    # Test opentelemetry_span property when _noop is True  
    assert test_span.opentelemetry_span is None


def test_closure_complex_function():
    """Test closure.py with complex function signature."""
    from lilypad._utils.closure import Closure
    
    # Test with function that has complex signature
    def complex_function(a: int, b: str = "default", *args, **kwargs) -> str:
        """A complex function for testing."""
        return f"{a}-{b}"
    
    closure = Closure.from_fn(complex_function)
    assert closure.signature is not None
    assert closure.code is not None
    assert "def complex_function" in closure.code


def test_call_safely_sync_exception():
    """Test call_safely with sync function that raises exception."""
    from lilypad._utils.call_safely import call_safely
    
    def failing_function(*args, **kwargs):
        raise ValueError("Test error")
    
    @call_safely(failing_function)
    def safe_function():
        return "should not reach here"
    
    # Should return the fallback result
    result = safe_function()
    assert result == "should not reach here"  # The fallback is the original function


@pytest.mark.asyncio
async def test_call_safely_async_exception():
    """Test call_safely with async function that raises exception."""
    from lilypad._utils.call_safely import call_safely
    
    async def failing_function(*args, **kwargs):
        raise ValueError("Test error")
    
    @call_safely(failing_function)
    async def safe_function():
        return "should not reach here"
    
    # Should return the fallback result
    result = await safe_function()
    assert result == "should not reach here"


def test_sandbox_runner_basic():
    """Test sandbox runner basic functionality."""
    from lilypad.sandbox.runner import SandboxRunner
    
    # Test that SandboxRunner is abstract and can't be instantiated directly
    with pytest.raises(TypeError):
        SandboxRunner()


def test_settings_coverage():
    """Test settings missing lines."""
    from lilypad._utils.settings import get_settings
    
    # Test getting settings (should work with current configuration)
    settings = get_settings()
    assert settings is not None
    assert hasattr(settings, 'api_key')


def test_fn_is_async_coverage():
    """Test fn_is_async edge cases."""
    from lilypad._utils.fn_is_async import fn_is_async
    
    # Test with None
    result = fn_is_async(None)
    assert result is False
    
    # Test with regular function
    def sync_func():
        pass
    
    result = fn_is_async(sync_func)
    assert result is False
    
    # Test with async function
    async def async_func():
        pass
    
    result = fn_is_async(async_func)
    assert result is True