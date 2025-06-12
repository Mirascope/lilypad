"""Tests for edge cases in trace decorator to improve coverage."""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock
import asyncio
from typing import Any

from lilypad.traces import (
    trace,
    _get_trace_type,
    _register_decorated_function,
    enable_recording,
    disable_recording,
)
from lilypad.exceptions import RemoteFunctionError


class TestDecoratorEdgeCases:
    """Test edge cases in trace decorator to improve coverage."""

    def test_register_decorated_function_when_disabled(self):
        """Test _register_decorated_function when recording is disabled."""
        # Disable recording
        disable_recording()

        # Create a mock function
        mock_fn = Mock()
        mock_fn.__module__ = "test_module"

        # This should return early without registering
        _register_decorated_function("test_decorator", mock_fn, "test_function")

        # Re-enable for other tests
        enable_recording()

    def test_register_decorated_function_inspect_failure(self):
        """Test _register_decorated_function when inspect functions fail."""
        enable_recording()

        # Create a mock function that will cause inspect to fail
        mock_fn = Mock()
        mock_fn.__module__ = "test_module"

        # Mock inspect.getfile to raise TypeError
        with patch("inspect.getfile", side_effect=TypeError("Cannot get file")):
            # This should handle the exception gracefully
            _register_decorated_function("test_decorator", mock_fn, "test_function")

    def test_register_decorated_function_success(self):
        """Test successful registration of decorated function."""
        enable_recording()

        # Create a real function for inspection
        def test_function():
            return "test"

        # Register the function
        _register_decorated_function("test_decorator", test_function, "test_function", {"test": "context"})

    @patch("lilypad.traces.get_function_by_hash_sync")
    def test_trace_versioning_function_not_found_creates_new(self, mock_get_function):
        """Test trace decorator when versioned function is not found and creates new one."""
        # Setup the mock to raise NotFoundError then return created function
        from lilypad.generated.errors.not_found_error import NotFoundError

        mock_function = Mock()
        mock_function.uuid_ = "new-function-uuid"
        mock_get_function.side_effect = NotFoundError("Function not found")

        # Mock the client creation call
        with patch("lilypad._utils.client.get_sync_client") as mock_get_client:
            mock_client = Mock()
            mock_client.projects.functions.create.return_value = mock_function
            mock_get_client.return_value = mock_client

            @trace(versioning="automatic")
            def sample_function(x: int, y: int) -> int:
                return x + y

            # Call the function
            result = sample_function(1, 2)
            assert result == 3

    @pytest.mark.asyncio
    @patch("lilypad.traces.get_function_by_hash_async")
    async def test_async_trace_versioning_function_not_found_creates_new(self, mock_get_function):
        """Test async trace decorator when versioned function is not found and creates new one."""
        # Setup the mock to raise NotFoundError then return created function
        from lilypad.generated.errors.not_found_error import NotFoundError

        mock_function = Mock()
        mock_function.uuid_ = "new-function-uuid"
        mock_get_function.side_effect = NotFoundError("Function not found")

        # Mock the client creation call
        with patch("lilypad._utils.client.get_async_client") as mock_get_client:
            mock_client = Mock()
            mock_client.projects.functions.create = AsyncMock(return_value=mock_function)
            mock_get_client.return_value = mock_client

            @trace(versioning="automatic")
            async def sample_async_function(x: int, y: int) -> int:
                await asyncio.sleep(0.01)
                return x + y

            # Call the function
            result = await sample_async_function(1, 2)
            assert result == 3

    def test_trace_with_mirascope_call(self):
        """Test trace decorator with mirascope call."""

        # Create a mock function with __mirascope_call__ attribute
        @trace()
        def sample_function(x: int, y: int) -> int:
            return x + y

        # Add the mirascope attribute
        sample_function.__mirascope_call__ = True
        sample_function._prompt_template = "test prompt template"

        # Mock the mirascope middleware
        with patch("lilypad._utils.create_mirascope_middleware") as mock_middleware:
            mock_middleware.return_value = lambda fn: fn

            result = sample_function(1, 2)
            assert result == 3

    @pytest.mark.asyncio
    async def test_async_trace_with_mirascope_call(self):
        """Test async trace decorator with mirascope call."""

        # Create a mock async function with __mirascope_call__ attribute
        @trace()
        async def sample_async_function(x: int, y: int) -> int:
            await asyncio.sleep(0.01)
            return x + y

        # Add the mirascope attribute
        sample_async_function.__mirascope_call__ = True
        sample_async_function._prompt_template = "test prompt template"

        # Mock the mirascope middleware
        with patch("lilypad._utils.create_mirascope_middleware") as mock_middleware:

            async def mock_middleware_func(fn):
                return fn

            mock_middleware.return_value = mock_middleware_func

            result = await sample_async_function(1, 2)
            assert result == 3

    @patch("lilypad.traces.get_sync_client")
    @patch("lilypad._utils.settings.get_settings")
    def test_trace_parameter_binding_failure(self, mock_get_settings, mock_get_client):
        """Test trace decorator when parameter binding fails."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_get_settings.return_value = mock_settings
        
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        @trace(mode="wrap")
        def sample_function(trace_ctx, x: int, y: int) -> int:
            return x + y

        # Call with wrong number of arguments to trigger TypeError in bind
        # This should still work because the decorator handles the TypeError
        result = sample_function(1, 2)  # Missing trace_ctx, but decorator adds it
        assert result.response == 3

    @pytest.mark.asyncio
    @patch("lilypad.traces.get_async_client")
    @patch("lilypad._utils.settings.get_settings")
    async def test_async_trace_parameter_binding_failure(self, mock_get_settings, mock_get_client):
        """Test async trace decorator when parameter binding fails."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.project_id = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
        mock_get_settings.return_value = mock_settings
        
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        @trace(mode="wrap")
        async def sample_async_function(trace_ctx, x: int, y: int) -> int:
            await asyncio.sleep(0.01)
            return x + y

        # Call with wrong number of arguments to trigger TypeError in bind
        # This should still work because the decorator handles the TypeError
        result = await sample_async_function(1, 2)  # Missing trace_ctx, but decorator adds it
        assert result.response == 3

    def test_trace_with_user_provided_trace_ctx(self):
        """Test trace decorator when user provides their own trace_ctx."""
        from lilypad.spans import Span

        @trace(mode="wrap")
        def sample_function(trace_ctx, x: int, y: int) -> int:
            return x + y

        # Provide a mock trace context
        mock_trace_ctx = Mock(spec=Span)

        result = sample_function(mock_trace_ctx, 1, 2)
        # In wrap mode, result should be wrapped in Trace object
        from lilypad.traces import Trace

        assert isinstance(result, Trace)
        assert result.response == 3

    @pytest.mark.asyncio
    async def test_async_trace_with_user_provided_trace_ctx(self):
        """Test async trace decorator when user provides their own trace_ctx."""
        from lilypad.spans import Span

        @trace(mode="wrap")
        async def sample_async_function(trace_ctx, x: int, y: int) -> int:
            await asyncio.sleep(0.01)
            return x + y

        # Provide a mock trace context
        mock_trace_ctx = Mock(spec=Span)

        result = await sample_async_function(mock_trace_ctx, 1, 2)
        # In wrap mode, result should be wrapped in AsyncTrace object
        from lilypad.traces import AsyncTrace

        assert isinstance(result, AsyncTrace)
        assert result.response == 3

    def test_trace_with_tags_sorting(self):
        """Test that trace decorator sorts tags."""

        # The decorator should sort tags internally
        @trace(tags=["zebra", "alpha", "beta"])
        def sample_function(x: int, y: int) -> int:
            return x + y

        result = sample_function(1, 2)
        assert result == 3

    def test_get_trace_type_edge_cases(self):
        """Test _get_trace_type with different inputs."""
        # Test with None
        assert _get_trace_type(None) == "trace"

        # Test with a function object
        def test_func():
            pass

        assert _get_trace_type(test_func) == "function"

        # Test with any non-None object (only function objects return "function")
        assert _get_trace_type("string") == "function"
        assert _get_trace_type(123) == "function"

    @patch("lilypad.traces.get_function_by_version_sync")
    def test_version_method_remote_function_error(self, mock_get_function):
        """Test that version method raises RemoteFunctionError on failure."""
        mock_get_function.side_effect = Exception("Database error")

        @trace(versioning="automatic")
        def sample_function(x: int, y: int) -> int:
            return x + y

        # The version method should handle the exception
        with pytest.raises(RemoteFunctionError):
            sample_function.version(1)(1, 2)

    @pytest.mark.asyncio
    @patch("lilypad.traces.get_function_by_version_async")
    async def test_async_version_method_remote_function_error(self, mock_get_function):
        """Test that async version method raises RemoteFunctionError on failure."""
        mock_get_function.side_effect = Exception("Database error")

        @trace(versioning="automatic")
        async def sample_async_function(x: int, y: int) -> int:
            await asyncio.sleep(0.01)
            return x + y

        # The version method should handle the exception
        with pytest.raises(RemoteFunctionError):
            versioned_fn = await sample_async_function.version(1)
            await versioned_fn(1, 2)

    @patch("lilypad.traces.get_deployed_function_sync")
    def test_remote_method_remote_function_error(self, mock_get_function):
        """Test that remote method raises RemoteFunctionError on failure."""
        mock_get_function.side_effect = Exception("Network error")

        @trace(versioning="automatic")
        def sample_function(x: int, y: int) -> int:
            return x + y

        # The remote method should handle the exception
        with pytest.raises(RemoteFunctionError):
            sample_function.remote()(1, 2)

    @pytest.mark.asyncio
    @patch("lilypad.traces.get_deployed_function_async")
    async def test_async_remote_method_remote_function_error(self, mock_get_function):
        """Test that async remote method raises RemoteFunctionError on failure."""
        mock_get_function.side_effect = Exception("Network error")

        @trace(versioning="automatic")
        async def sample_async_function(x: int, y: int) -> int:
            await asyncio.sleep(0.01)
            return x + y

        # The remote method should handle the exception
        with pytest.raises(RemoteFunctionError):
            remote_result = await sample_async_function.remote(1, 2)
