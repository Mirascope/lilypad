"""Tests for missing traces.py coverage, specifically mirascope-related code."""

import asyncio
from unittest.mock import Mock, patch, MagicMock
from typing import Callable, Any
import pytest

from src.lilypad.traces import trace
from src.lilypad.exceptions import RemoteFunctionError

# Mock settings to prevent network calls
mock_settings = Mock()
mock_settings.project_id = "test-project"
mock_settings.base_url = "http://test.example.com"
mock_settings.api_key = "test-key"

# Apply global patches to prevent network calls
@pytest.fixture(autouse=True)
def mock_global_settings():
    with patch("src.lilypad._utils.settings.get_settings", return_value=mock_settings):
        with patch("src.lilypad.traces.get_settings", return_value=mock_settings):
            yield

# Mock client to prevent network calls when versioning=True
@pytest.fixture(autouse=True)
def mock_clients():
    mock_sync_client = Mock()
    mock_async_client = Mock()
    
    # Mock the closure creation which happens during versioning
    mock_closure = Mock()
    mock_closure.hash = "test_hash_12345"
    mock_closure.code = "def test(): pass"
    
    with patch("src.lilypad.traces.get_sync_client", return_value=mock_sync_client):
        with patch("src.lilypad.traces.get_async_client", return_value=mock_async_client):
            with patch("src.lilypad._utils.client.get_sync_client", return_value=mock_sync_client):
                with patch("src.lilypad._utils.client.get_async_client", return_value=mock_async_client):
                    with patch("src.lilypad._utils.closure.Closure.from_fn", return_value=mock_closure):
                        yield


def test_trace_decorator_sync_mirascope_call():
    """Test trace decorator with mirascope call - covers lines 956-966."""
    # Mock the necessary functions
    mock_middleware = Mock()
    
    # Create a wrapper that returns the expected result
    def mock_middleware_wrapper(fn):
        def wrapper(*args, **kwargs):
            return "mirascope result"
        return wrapper
    
    mock_middleware.return_value = mock_middleware_wrapper
    
    # Create a function with __mirascope_call__ attribute
    def mirascope_function(arg1: str, prompt_template: str) -> str:
        return f"Result: {arg1}"
    
    # Add __mirascope_call__ attribute to make it a mirascope call
    mirascope_function.__mirascope_call__ = True
    
    with patch("src.lilypad.traces.get_function_by_hash_sync") as mock_get_function, \
         patch("src.lilypad.traces.create_mirascope_middleware", mock_middleware):
        
        mock_function = Mock()
        mock_function.closure.hash = "test_hash"
        mock_get_function.return_value = mock_function
        
        # Create decorated function
        decorated = trace(name="test_mirascope", tags=["mirascope", "test"])(mirascope_function)
        
        # Call the function
        result = decorated("test", "template")
        
        # Verify middleware was created and result is correct
        assert mock_middleware.called
        assert result == "mirascope result"


@pytest.mark.asyncio
async def test_trace_decorator_async_mirascope_call():
    """Test async trace decorator with mirascope call - covers lines 787-796."""
    # Mock the necessary functions
    mock_middleware = Mock()
    
    # Create an async wrapper that returns the expected result
    def mock_middleware_wrapper(fn):
        async def wrapper(*args, **kwargs):
            return "async mirascope result"
        return wrapper
    
    mock_middleware.return_value = mock_middleware_wrapper
    
    async def async_mirascope_function(arg1: str, prompt_template: str) -> str:
        return f"Result: {arg1}"
    
    # Add __mirascope_call__ attribute to make it a mirascope call
    async_mirascope_function.__mirascope_call__ = True

    with patch("src.lilypad.traces.get_function_by_hash_async") as mock_get_function, \
         patch("src.lilypad.traces.create_mirascope_middleware", mock_middleware):
        
        mock_function = Mock()
        mock_function.closure.hash = "test_hash"
        mock_get_function.return_value = mock_function
        
        # Create decorated async function
        decorated = trace(name="test_mirascope_async")(async_mirascope_function)
        
        # Call the function
        result = await decorated("test", "template")
        
        # Verify middleware was created and result is correct
        assert mock_middleware.called
        assert result == "async mirascope result"


def test_trace_decorator_sync_version_function_retrieval_error():
    """Test sync version method when function retrieval fails - covers lines 1001-1002."""
    with patch("src.lilypad.traces.get_function_by_version_sync", side_effect=Exception("Retrieval error")):
        
        @trace(name="test_version_error", versioning=True)
        def versioned_function(x: int) -> int:
            return x * 2
        
        # Try to get a specific version
        with pytest.raises(RemoteFunctionError) as exc_info:
            versioned_function.version(1)
        
        assert "Failed to retrieve function versioned_function" in str(exc_info.value)
        assert "Retrieval error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_trace_decorator_async_version_function_retrieval_error():
    """Test async version method when function retrieval fails - covers lines 826-827."""
    with patch("src.lilypad.traces.get_function_by_version_async", side_effect=Exception("Async retrieval error")):
        
        @trace(name="test_version_error_async", versioning=True)
        async def versioned_function_async(x: int) -> int:
            return x * 2
        
        # Try to get a specific version
        with pytest.raises(RemoteFunctionError) as exc_info:
            await versioned_function_async.version(1)
        
        assert "Failed to retrieve function versioned_function_async" in str(exc_info.value)
        assert "Async retrieval error" in str(exc_info.value)


def test_trace_decorator_sync_remote_execution_error():
    """Test sync remote method when execution fails - covers lines 1045-1046."""
    # First test when function retrieval fails
    with patch("src.lilypad.traces.get_deployed_function_sync", side_effect=Exception("Retrieval failed")):
        @trace(name="test_remote_error", versioning=True)
        def remote_function(x: int) -> int:
            return x * 2
        
        # Try to execute remotely
        with pytest.raises(RemoteFunctionError) as exc_info:
            remote_function.remote()
        
        assert "Failed to retrieve function remote_function" in str(exc_info.value)
        assert "Retrieval failed" in str(exc_info.value)
    
    # Now test when sandbox execution fails
    mock_function = Mock()
    mock_function.uuid_ = "test-uuid"
    mock_function.name = "test_func"
    mock_function.code = "def test_func(): return 42"
    mock_function.signature = "def test_func(): ..."
    mock_function.hash = "test_hash"
    mock_function.dependencies = {}
    
    # Mock the closure that will be used
    mock_closure = Mock()
    mock_closure.code = "def test_func(): return 42"
    mock_closure.hash = "test_hash"
    
    with patch("src.lilypad.traces.get_deployed_function_sync", return_value=mock_function), \
         patch("src.lilypad.traces.SubprocessSandboxRunner") as mock_sandbox_class, \
         patch("src.lilypad.traces.get_cached_closure", return_value=mock_closure):
        
        mock_sandbox = Mock()
        mock_sandbox.execute_function.side_effect = Exception("Sandbox execution failed")
        mock_sandbox_class.return_value = mock_sandbox
        
        @trace(name="test_remote_exec_error", versioning=True)
        def remote_exec_function(x: int) -> int:
            return x * 2
        
        # Try to execute remotely
        with pytest.raises(Exception) as exc_info:
            remote_exec_function.remote()
        
        assert "Sandbox execution failed" in str(exc_info.value)


@pytest.mark.asyncio
async def test_trace_decorator_async_remote_execution_error():
    """Test async remote method when execution fails - covers lines 870-871."""
    # First test when function retrieval fails
    with patch("src.lilypad.traces.get_deployed_function_async", side_effect=Exception("Async retrieval failed")):
        @trace(name="test_remote_error_async", versioning=True)
        async def remote_function_async(x: int) -> int:
            return x * 2
        
        # Try to execute remotely
        with pytest.raises(RemoteFunctionError) as exc_info:
            await remote_function_async.remote()
        
        assert "Failed to retrieve function remote_function_async" in str(exc_info.value)
        assert "Async retrieval failed" in str(exc_info.value)
    
    # Now test when sandbox execution fails
    mock_function = Mock()
    mock_function.uuid_ = "test-uuid-async"
    mock_function.name = "test_func_async"
    mock_function.code = "async def test_func(): return 42"
    mock_function.signature = "async def test_func(): ..."
    mock_function.hash = "test_hash_async"
    mock_function.dependencies = {}
    
    # Mock the closure that will be used
    mock_closure = Mock()
    mock_closure.code = "async def test_func(): return 42"
    mock_closure.hash = "test_hash_async"
    
    with patch("src.lilypad.traces.get_deployed_function_async", return_value=mock_function), \
         patch("src.lilypad.traces.SubprocessSandboxRunner") as mock_sandbox_class, \
         patch("src.lilypad.traces.get_cached_closure", return_value=mock_closure):
        
        mock_sandbox = Mock()
        mock_sandbox.execute_function.side_effect = Exception("Async sandbox execution failed")
        mock_sandbox_class.return_value = mock_sandbox
        
        @trace(name="test_remote_exec_error_async", versioning=True)
        async def remote_exec_function_async(x: int) -> int:
            return x * 2
        
        # Try to execute remotely
        with pytest.raises(Exception) as exc_info:
            await remote_exec_function_async.remote()
        
        assert "Async sandbox execution failed" in str(exc_info.value)


def test_trace_decorator_sync_version_with_sandbox_error():
    """Test sync version method with sandbox execution error - covers line 1024."""
    mock_versioned_function = Mock()
    mock_versioned_function.uuid_ = "version-uuid"
    mock_versioned_function.name = "versioned_func"
    mock_versioned_function.code = "def versioned_func(x): return x * 3"
    mock_versioned_function.signature = "def versioned_func(x): ..."
    mock_versioned_function.hash = "version_hash"
    mock_versioned_function.dependencies = {}
    
    with patch("src.lilypad.traces.get_function_by_version_sync", return_value=mock_versioned_function), \
         patch("src.lilypad.traces.get_cached_closure") as mock_get_cached_closure:
        
        mock_closure = Mock()
        mock_closure.code = "def versioned_func(x): return x * 3"
        mock_get_cached_closure.return_value = mock_closure
        
        mock_sandbox = Mock()
        mock_sandbox.execute_function.side_effect = Exception("Version sandbox error")
        
        @trace(name="test_version_sandbox", versioning=True)
        def versioned_with_sandbox(x: int) -> int:
            return x * 2
        
        # Get version with custom sandbox that fails
        version_func = versioned_with_sandbox.version(1, sandbox=mock_sandbox)
        
        # Try to execute the versioned function
        with pytest.raises(Exception) as exc_info:
            version_func(5)
        
        assert "Version sandbox error" in str(exc_info.value)


@pytest.mark.asyncio
async def test_trace_decorator_async_version_with_sandbox_error():
    """Test async version method with sandbox execution error - covers line 849."""
    mock_versioned_function = Mock()
    mock_versioned_function.uuid_ = "version-uuid-async"
    mock_versioned_function.name = "versioned_func_async"
    mock_versioned_function.code = "async def versioned_func(x): return x * 3"
    mock_versioned_function.signature = "async def versioned_func(x): ..."
    mock_versioned_function.hash = "version_hash_async"
    mock_versioned_function.dependencies = {}
    
    with patch("src.lilypad.traces.get_function_by_version_async", return_value=mock_versioned_function), \
         patch("src.lilypad.traces.get_cached_closure") as mock_get_cached_closure:
        
        mock_closure = Mock()
        mock_closure.code = "async def versioned_func(x): return x * 3"
        mock_get_cached_closure.return_value = mock_closure
        
        mock_sandbox = Mock()
        mock_sandbox.execute_function.side_effect = Exception("Async version sandbox error")
        
        @trace(name="test_version_sandbox_async", versioning=True)
        async def versioned_with_sandbox_async(x: int) -> int:
            return x * 2
        
        # Get version with custom sandbox that fails
        version_func = await versioned_with_sandbox_async.version(1, sandbox=mock_sandbox)
        
        # Try to execute the versioned function
        with pytest.raises(Exception) as exc_info:
            await version_func(5)
        
        assert "Async version sandbox error" in str(exc_info.value)


def test_trace_sync_with_function_not_found_error():
    """Test sync trace when function is not found - covers lines 891, 899."""
    with patch("src.lilypad.traces.get_function_by_hash_sync", return_value=None):
        
        @trace(name="test_function_not_found")
        def missing_function(x: int) -> int:
            return x * 2
        
        # Function should still work when not found in registry
        result = missing_function(5)
        assert result == 10


@pytest.mark.asyncio
async def test_trace_async_with_function_not_found_error():
    """Test async trace when function is not found - covers line 728."""
    with patch("src.lilypad.traces.get_function_by_hash_async", return_value=None):
        
        @trace(name="test_function_not_found_async")
        async def missing_function_async(x: int) -> int:
            return x * 2
        
        # Function should still work when not found in registry
        result = await missing_function_async(5)
        assert result == 10


def test_trace_sync_remote_with_provided_sandbox():
    """Test sync remote method with provided sandbox - covers line 1066."""
    mock_function = Mock()
    mock_function.uuid_ = "remote-uuid"
    mock_function.name = "test_func"
    mock_function.code = "def test_func(x=42): return x * 2"
    mock_function.signature = "def test_func(x=42): ..."
    mock_function.hash = "test_hash"
    mock_function.dependencies = {}
    
    # Mock the closure
    mock_closure = Mock()
    mock_closure.code = "def test_func(x=42): return x * 2"
    mock_closure.hash = "test_hash"
    
    with patch("src.lilypad.traces.get_deployed_function_sync", return_value=mock_function), \
         patch("src.lilypad.traces.get_cached_closure", return_value=mock_closure):
        
        mock_sandbox = Mock()
        # Mock sandbox should return a dict with 'result' key
        mock_sandbox.execute_function.return_value = {"result": 84}
        
        @trace(name="test_remote_sandbox", versioning=True)
        def remote_with_sandbox(x: int = 42) -> int:
            return x * 2
        
        # Execute remotely with custom sandbox
        result = remote_with_sandbox.remote(sandbox=mock_sandbox)
        
        assert result == 84
        mock_sandbox.execute_function.assert_called_once()


@pytest.mark.asyncio
async def test_trace_async_remote_with_provided_sandbox():
    """Test async remote method with provided sandbox - covers line 891."""
    mock_function = Mock()
    mock_function.uuid_ = "remote-uuid-async"
    mock_function.name = "test_func_async"
    mock_function.code = "async def test_func(x=42): return x * 2"
    mock_function.signature = "async def test_func(x=42): ..."
    mock_function.hash = "test_hash_async"
    mock_function.dependencies = {}
    
    # Mock the closure
    mock_closure = Mock()
    mock_closure.code = "async def test_func(x=42): return x * 2"
    mock_closure.hash = "test_hash_async"
    
    with patch("src.lilypad.traces.get_deployed_function_async", return_value=mock_function), \
         patch("src.lilypad.traces.get_cached_closure", return_value=mock_closure):
        
        mock_sandbox = Mock()
        # Mock sandbox should return a dict with 'result' key
        mock_sandbox.execute_function.return_value = {"result": 84}
        
        @trace(name="test_remote_sandbox_async", versioning=True)
        async def remote_with_sandbox_async(x: int = 42) -> int:
            return x * 2
        
        # Execute remotely with custom sandbox
        result = await remote_with_sandbox_async.remote(sandbox=mock_sandbox)
        
        assert result == 84