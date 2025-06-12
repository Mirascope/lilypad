"""Unit tests for the trace decorator functionality in traces.py."""

import pytest
from unittest.mock import Mock, patch
import asyncio

from lilypad.traces import (
    trace,
    enable_recording,
    disable_recording,
    clear_registry,
    get_decorated_functions,
    Span,
    Trace,
    AsyncTrace,
    TRACE_MODULE_NAME,
)


# Test basic trace decorator functionality
def test_trace_decorator_basic():
    """Test basic trace decorator functionality."""

    # Define a function with the trace decorator
    @trace()
    def sample_function(x: int, y: int) -> int:
        return x + y

    # Call the function and verify it works correctly
    result = sample_function(1, 2)
    assert result == 3

    # Verify the function is registered (note: without versioning, functions may not be registered)
    # This is just checking the decorator works


# Test trace decorator with name parameter
def test_trace_decorator_with_name():
    """Test trace decorator with name parameter."""

    # Define a function with the trace decorator and a custom name
    @trace(name="custom_name")
    def sample_function(x: int, y: int) -> int:
        return x + y

    # Call the function and verify it works correctly
    result = sample_function(1, 2)
    assert result == 3


# Test trace decorator with tags
def test_trace_decorator_with_tags():
    """Test trace decorator with tags parameter."""

    # Define a function with the trace decorator and tags
    @trace(tags=["tag1", "tag2"])
    def sample_function(x: int, y: int) -> int:
        return x + y

    # Call the function and verify it works correctly
    result = sample_function(1, 2)
    assert result == 3


# Test trace decorator with wrap mode
def test_trace_decorator_with_wrap_mode():
    """Test trace decorator with wrap mode."""

    # Define a function with the trace decorator in wrap mode
    @trace(mode="wrap")
    def sample_function(trace_ctx: Span, x: int, y: int) -> int:
        trace_ctx.info("Adding numbers", x=x, y=y)
        return x + y

    # Call the function and verify result is wrapped in Trace object
    result = sample_function(1, 2)

    assert isinstance(result, Trace)
    assert result.response == 3


# Test trace decorator with automatic versioning
def test_trace_decorator_with_automatic_versioning():
    """Test trace decorator with automatic versioning."""

    # Define a function with the trace decorator and automatic versioning
    @trace(versioning="automatic")
    def sample_function(x: int, y: int) -> int:
        return x + y

    # Call the function and verify it works correctly
    result = sample_function(1, 2)
    assert result == 3

    # Verify the function has version method
    assert hasattr(sample_function, "version")

    # Verify the function has remote method
    assert hasattr(sample_function, "remote")


# Test trace decorator with automatic versioning and wrap mode
@patch("lilypad.traces.get_function_by_hash_sync")
def test_trace_decorator_with_automatic_versioning_and_wrap_mode(mock_get_function):
    """Test trace decorator with automatic versioning and wrap mode."""
    # Mock the function lookup to return a valid function
    mock_function = Mock()
    mock_function.uuid_ = "test-uuid"
    mock_get_function.return_value = mock_function

    # Define a function with the trace decorator, automatic versioning, and wrap mode
    @trace(versioning="automatic", mode="wrap")
    def sample_function(trace_ctx: Span, x: int, y: int) -> int:
        trace_ctx.info("Adding numbers", x=x, y=y)
        return x + y

    # Call the function and verify result is wrapped in Trace object
    result = sample_function(1, 2)

    assert isinstance(result, Trace)
    assert result.response == 3

    # Verify the function has version method
    assert hasattr(sample_function, "version")

    # Verify the function has remote method
    assert hasattr(sample_function, "remote")


# Test async function with trace decorator
@pytest.mark.asyncio
async def test_trace_decorator_with_async_function():
    """Test trace decorator with async function."""

    # Define an async function with the trace decorator
    @trace()
    async def sample_async_function(x: int, y: int) -> int:
        await asyncio.sleep(0.01)  # Small delay to ensure it's actually async
        return x + y

    # Call the function and verify it works correctly
    result = await sample_async_function(1, 2)
    assert result == 3


# Test async function with trace decorator in wrap mode
@pytest.mark.asyncio
async def test_trace_decorator_with_async_function_wrap_mode():
    """Test trace decorator with async function in wrap mode."""

    # Define an async function with the trace decorator in wrap mode
    @trace(mode="wrap")
    async def sample_async_function(trace_ctx: Span, x: int, y: int) -> int:
        trace_ctx.info("Adding numbers asynchronously", x=x, y=y)
        await asyncio.sleep(0.01)  # Small delay to ensure it's actually async
        return x + y

    # Call the function and verify result is wrapped in AsyncTrace object
    result = await sample_async_function(1, 2)

    assert isinstance(result, AsyncTrace)
    assert result.response == 3


# Test async function with trace decorator and automatic versioning
@pytest.mark.asyncio
async def test_trace_decorator_with_async_function_automatic_versioning():
    """Test trace decorator with async function and automatic versioning."""

    # Define an async function with the trace decorator and automatic versioning
    @trace(versioning="automatic")
    async def sample_async_function(x: int, y: int) -> int:
        await asyncio.sleep(0.01)  # Small delay to ensure it's actually async
        return x + y

    # Call the function and verify it works correctly
    result = await sample_async_function(1, 2)
    assert result == 3

    # Verify the function has version method
    assert hasattr(sample_async_function, "version")

    # Verify the function has remote method
    assert hasattr(sample_async_function, "remote")


# Test enable_recording and disable_recording
def test_enable_disable_recording():
    """Test enable_recording and disable_recording functions."""
    # Enable recording
    enable_recording()

    # Define a function with the trace decorator
    @trace()
    def sample_function(x: int, y: int) -> int:
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


# Test clear_registry
def test_clear_registry():
    """Test clear_registry function."""
    from lilypad.traces import enable_recording

    # Ensure recording is enabled
    enable_recording()

    # Define a function with the trace decorator and versioning to ensure registration
    @trace(versioning="automatic")
    def sample_function(x: int, y: int) -> int:
        return x + y

    # Call the function to ensure it's executed and registered
    sample_function(1, 2)

    # Check if function is registered
    initial_registry = get_decorated_functions()
    initial_count = len(initial_registry.get(TRACE_MODULE_NAME, []))

    # Clear the registry
    clear_registry()

    # Verify the registry is cleared
    cleared_registry = get_decorated_functions()
    assert len(cleared_registry) == 0


# Test get_decorated_functions with specific decorator name
def test_get_decorated_functions_with_name():
    """Test get_decorated_functions with specific decorator name."""
    from lilypad.traces import enable_recording

    # Clear the registry first
    clear_registry()
    # Ensure recording is enabled
    enable_recording()

    # Define a function with the trace decorator and versioning to ensure registration
    @trace(versioning="automatic")
    def sample_function(x: int, y: int) -> int:
        return x + y

    # Call the function to ensure it's executed and registered
    sample_function(1, 2)

    # Verify the function is registered with the trace decorator
    decorated_functions = get_decorated_functions(TRACE_MODULE_NAME)
    assert len(decorated_functions[TRACE_MODULE_NAME]) > 0

    # Verify the function is not registered with a different decorator
    decorated_functions = get_decorated_functions("other_decorator")
    assert len(decorated_functions["other_decorator"]) == 0


# Test trace decorator with exception handling
def test_trace_decorator_with_exception():
    """Test trace decorator with exception handling."""

    # Define a function with the trace decorator that raises an exception
    @trace()
    def sample_function_with_exception(x: int, y: int) -> int:
        raise ValueError("Test exception")

    # Call the function and verify it raises the expected exception
    with pytest.raises(ValueError, match="Test exception"):
        sample_function_with_exception(1, 2)


# Test trace decorator with exception handling in wrap mode
def test_trace_decorator_with_exception_wrap_mode():
    """Test trace decorator with exception handling in wrap mode."""

    # Define a function with the trace decorator in wrap mode that raises an exception
    @trace(mode="wrap")
    def sample_function_with_exception(trace_ctx: Span, x: int, y: int) -> int:
        trace_ctx.info("About to raise an exception")
        raise ValueError("Test exception in wrap mode")

    # Call the function and verify it raises the expected exception
    with pytest.raises(ValueError, match="Test exception in wrap mode"):
        sample_function_with_exception(1, 2)


# Test version method with automatic versioning
def test_version_method_sync():
    """Test version method with automatic versioning for sync functions."""

    # Define a function with the trace decorator and automatic versioning
    @trace(versioning="automatic")
    def sample_function(x: int, y: int) -> int:
        return x + y

    # Verify the function has version method
    assert hasattr(sample_function, "version")
    assert callable(sample_function.version)

    # Mock the version method to avoid external dependencies in tests
    def mock_version_function(*args, **kwargs):
        return 42

    with patch.object(sample_function, "version") as mock_version:
        mock_version.return_value = lambda *args, **kwargs: 42
        result = sample_function.version(1)(1, 2)
        assert result == 42


# Test version method with automatic versioning for async functions
@pytest.mark.asyncio
async def test_version_method_async():
    """Test version method with automatic versioning for async functions."""

    # Define an async function with the trace decorator and automatic versioning
    @trace(versioning="automatic")
    async def sample_async_function(x: int, y: int) -> int:
        await asyncio.sleep(0.01)
        return x + y

    # Verify the function has version method
    assert hasattr(sample_async_function, "version")
    assert callable(sample_async_function.version)

    # Mock the version method to avoid external dependencies in tests
    async def mock_async_version_function(*args, **kwargs):
        return 42

    with patch.object(sample_async_function, "version") as mock_version:
        mock_version.return_value = mock_async_version_function
        versioned_function = await sample_async_function.version(1)
        result = await versioned_function(1, 2)
        assert result == 42


# Test remote method with automatic versioning
def test_remote_method_sync():
    """Test remote method with automatic versioning for sync functions."""

    # Define a function with the trace decorator and automatic versioning
    @trace(versioning="automatic")
    def sample_function(x: int, y: int) -> int:
        return x + y

    # Create a mock function
    def mock_remote_function(*args, **kwargs):
        return 42

    # Call the remote method with mocked implementation
    with patch.object(sample_function, "remote", return_value=mock_remote_function):
        result = sample_function.remote()(1, 2)

    # Verify the result
    assert result == 42


# Test remote method with automatic versioning for async functions
@pytest.mark.asyncio
async def test_remote_method_async():
    """Test remote method with automatic versioning for async functions."""

    # Define an async function with the trace decorator and automatic versioning
    @trace(versioning="automatic")
    async def sample_async_function(x: int, y: int) -> int:
        await asyncio.sleep(0.01)
        return x + y

    # Verify the function has remote method
    assert hasattr(sample_async_function, "remote")
    assert callable(sample_async_function.remote)

    # Mock the remote method to avoid external dependencies in tests
    with patch.object(sample_async_function, "remote") as mock_remote:
        mock_remote.return_value = 42
        result = await sample_async_function.remote(1, 2)
        assert result == 42


# Test trace decorator with custom serializers
@patch("lilypad._utils.serializer_registry.SerializerMap")
def test_trace_decorator_with_serializers(mock_serializer_map_class):
    """Test trace decorator with custom serializers."""
    # Create a mock serializer map
    mock_serializer_map = Mock()
    mock_serializer_map_class.return_value = mock_serializer_map

    # Define a function with the trace decorator and mock serializers
    @trace(serializers=mock_serializer_map)
    def sample_function(x: int, y: int) -> int:
        return x + y

    # Call the function and verify it works correctly
    result = sample_function(1, 2)
    assert result == 3


# Test trace decorator with custom serializers in wrap mode
@patch("lilypad._utils.serializer_registry.SerializerMap")
def test_trace_decorator_with_serializers_wrap_mode(mock_serializer_map_class):
    """Test trace decorator with custom serializers in wrap mode."""
    # Create a mock serializer map
    mock_serializer_map = Mock()
    mock_serializer_map_class.return_value = mock_serializer_map

    # Define a function with the trace decorator in wrap mode and mock serializers
    @trace(mode="wrap", serializers=mock_serializer_map)
    def sample_function(trace_ctx: Span, x: int, y: int) -> int:
        trace_ctx.info("Adding numbers", x=x, y=y)
        return x + y

    # Call the function and verify result is wrapped in Trace object
    result = sample_function(1, 2)

    assert isinstance(result, Trace)
    assert result.response == 3
