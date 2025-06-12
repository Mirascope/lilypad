"""Simple tests to achieve 100% coverage for traces.py."""

import pytest
from unittest.mock import Mock, patch
import asyncio

from lilypad.traces import (
    trace,
    enable_recording,
    disable_recording,
    clear_registry,
    get_decorated_functions,
    Trace,
    _get_trace_type,
    Annotation,
    TRACE_MODULE_NAME,
)


def test_get_trace_type():
    """Test _get_trace_type function."""
    # Test with None
    assert _get_trace_type(None) == "trace"

    # Test with a function
    mock_function = Mock()
    assert _get_trace_type(mock_function) == "function"


def test_annotation():
    """Test Annotation class."""
    # Create an annotation
    annotation = Annotation(data={"key": "value"}, label="pass", reasoning="This is a test", type="manual")

    # Verify the annotation properties
    assert annotation.data == {"key": "value"}
    assert annotation.label == "pass"
    assert annotation.reasoning == "This is a test"
    assert annotation.type == "manual"


def test_trace_decorator_basic():
    """Test basic trace decorator functionality."""

    # Define a function with the trace decorator
    @trace()
    def sample_function(x, y):
        return x + y

    # Call the function
    result = sample_function(1, 2)

    # Verify the result
    assert result == 3


@pytest.mark.asyncio
async def test_trace_decorator_async():
    """Test trace decorator with async function."""

    # Define an async function with the trace decorator
    @trace()
    async def sample_async_function(x, y):
        await asyncio.sleep(0.01)
        return x + y

    # Call the function
    result = await sample_async_function(1, 2)

    # Verify the result
    assert result == 3


def test_trace_decorator_with_name():
    """Test trace decorator with name parameter."""

    # Define a function with the trace decorator and a custom name
    @trace(name="custom_name")
    def sample_function(x, y):
        return x + y

    # Call the function
    result = sample_function(1, 2)

    # Verify the result
    assert result == 3


def test_trace_decorator_with_tags():
    """Test trace decorator with tags parameter."""

    # Define a function with the trace decorator and tags
    @trace(tags=["tag1", "tag2"])
    def sample_function(x, y):
        return x + y

    # Call the function
    result = sample_function(1, 2)

    # Verify the result
    assert result == 3


def test_trace_decorator_with_wrap_mode():
    """Test trace decorator with wrap mode."""

    # Define a function with the trace decorator in wrap mode
    @trace(mode="wrap")
    def sample_function(trace_ctx, x, y):
        trace_ctx.info("Adding numbers", x=x, y=y)
        return x + y

    # Call the function and verify result is wrapped in Trace object
    result = sample_function(1, 2)
    assert isinstance(result, Trace)
    assert result.response == 3


def test_trace_decorator_with_exception():
    """Test trace decorator with exception handling."""

    # Define a function with the trace decorator that raises an exception
    @trace()
    def sample_function_with_exception(x, y):
        raise ValueError("Test exception")

    # Call the function and verify it raises the expected exception
    with pytest.raises(ValueError, match="Test exception"):
        sample_function_with_exception(1, 2)


def test_enable_disable_recording():
    """Test enable_recording and disable_recording functions."""
    # Enable recording
    enable_recording()

    # Define a function with the trace decorator
    @trace()
    def sample_function(x, y):
        return x + y

    # Call the function
    result = sample_function(1, 2)
    assert result == 3

    # Disable recording
    disable_recording()

    # Call the function again
    result = sample_function(3, 4)
    assert result == 7

    # Re-enable recording for other tests
    enable_recording()


def test_clear_registry():
    """Test clear_registry function."""
    # Ensure recording is enabled
    enable_recording()

    # Define a function with the trace decorator and versioning to ensure registration
    @trace(versioning="automatic")
    def sample_function(x, y):
        return x + y

    # Call the function to ensure it's registered
    sample_function(1, 2)

    # Get decorated functions before clearing
    decorated_functions_before = get_decorated_functions()

    # Clear the registry
    clear_registry()

    # Get decorated functions after clearing
    decorated_functions_after = get_decorated_functions()

    # Verify the registry is cleared
    assert len(decorated_functions_after) == 0


def test_get_decorated_functions():
    """Test get_decorated_functions function."""
    # Clear the registry first
    clear_registry()
    # Ensure recording is enabled
    enable_recording()

    # Define a function with the trace decorator and versioning to ensure registration
    @trace(versioning="automatic")
    def sample_function(x, y):
        return x + y

    # Call the function to ensure it's registered
    sample_function(1, 2)

    # Get decorated functions with trace decorator
    decorated_functions = get_decorated_functions(TRACE_MODULE_NAME)
    assert len(decorated_functions[TRACE_MODULE_NAME]) > 0

    # Get decorated functions with non-existent decorator
    decorated_functions = get_decorated_functions("non_existent")
    assert len(decorated_functions["non_existent"]) == 0

    # Get all decorated functions
    decorated_functions = get_decorated_functions()
    assert len(decorated_functions) > 0


def test_trace_decorator_with_versioning():
    """Test trace decorator with versioning parameter."""
    # Ensure recording is enabled
    enable_recording()

    # Define a function with the trace decorator and versioning
    @trace(versioning="automatic")
    def sample_function(x, y):
        return x + y

    # Call the function
    result = sample_function(1, 2)

    # Verify the result
    assert result == 3

    # Verify the function has version and remote methods
    assert hasattr(sample_function, "version")
    assert hasattr(sample_function, "remote")


@patch("lilypad.traces.get_function_by_hash_sync")
def test_trace_decorator_with_versioning_and_wrap_mode(mock_get_function):
    """Test trace decorator with versioning and wrap mode parameters."""
    # Mock the function lookup to return a valid function
    mock_function = Mock()
    mock_function.uuid_ = "test-uuid"
    mock_get_function.return_value = mock_function

    # Define a function with the trace decorator, versioning, and wrap mode
    @trace(versioning="automatic", mode="wrap")
    def sample_function(trace_ctx, x, y):
        trace_ctx.info("Adding numbers", x=x, y=y)
        return x + y

    # Call the function and verify result is wrapped in Trace object
    result = sample_function(1, 2)
    assert isinstance(result, Trace)
    assert result.response == 3

    # Verify the function has version method (indicating versioning is enabled)
    assert hasattr(sample_function, "version")

    # Verify the function has remote method (indicating versioning is enabled)
    assert hasattr(sample_function, "remote")


def test_trace_decorator_with_serializers():
    """Test trace decorator with serializers parameter."""
    # Create a mock serializer map
    mock_serializer_map = {}

    # Define a function with the trace decorator and serializers
    @trace(serializers=mock_serializer_map)
    def sample_function(x, y):
        return x + y

    # Call the function
    result = sample_function(1, 2)

    # Verify the result
    assert result == 3
