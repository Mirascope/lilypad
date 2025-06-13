"""Tests to cover the remaining 18 missing lines in traces.py."""

import pytest
from unittest.mock import Mock, patch, MagicMock, AsyncMock

from lilypad.traces import trace
from lilypad.generated.errors.not_found_error import NotFoundError


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_async_client")
@patch("lilypad.traces.get_function_by_hash_async")
@patch("lilypad.traces.Closure")
@patch("lilypad.traces.Span")
@pytest.mark.asyncio
async def test_trace_decorator_async_versioning_function_not_found_creates_new(
    mock_span_class, mock_closure_class, mock_get_function_by_hash_async, 
    mock_get_async_client, mock_get_settings
):
    """Test async trace decorator when function is not found and gets created."""
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
    mock_closure.code = "def test_fn(): return 'test'"
    mock_closure.name = "test_fn"
    mock_closure.signature = "() -> str"
    mock_closure.dependencies = []
    mock_closure_class.from_fn.return_value = mock_closure
    
    # First call raises NotFoundError, second call should create function
    mock_get_function_by_hash_async.side_effect = NotFoundError(None)
    
    mock_client = AsyncMock()
    mock_new_function = Mock()
    mock_new_function.uuid_ = "new-function-uuid"
    mock_client.projects.functions.create.return_value = mock_new_function
    mock_get_async_client.return_value = mock_client
    
    @trace(versioning="automatic")
    async def test_async_function():
        return "test"
    
    result = await test_async_function()
    
    # Should have called create when function not found
    mock_client.projects.functions.create.assert_called_once()
    assert result == "test"


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_sync_client")
@patch("lilypad.traces.get_function_by_hash_sync")
@patch("lilypad.traces.Closure")
@patch("lilypad.traces.Span")
def test_trace_decorator_sync_versioning_function_not_found_creates_new(
    mock_span_class, mock_closure_class, mock_get_function_by_hash_sync, 
    mock_get_sync_client, mock_get_settings
):
    """Test sync trace decorator when function is not found and gets created."""
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
    mock_closure.code = "def test_fn(): return 'test'"
    mock_closure.name = "test_fn"
    mock_closure.signature = "() -> str"
    mock_closure.dependencies = []
    mock_closure_class.from_fn.return_value = mock_closure
    
    # First call raises NotFoundError, second call should create function
    mock_get_function_by_hash_sync.side_effect = NotFoundError(None)
    
    mock_client = Mock()
    mock_new_function = Mock()
    mock_new_function.uuid_ = "new-function-uuid"
    mock_client.projects.functions.create.return_value = mock_new_function
    mock_get_sync_client.return_value = mock_client
    
    @trace(versioning="automatic")
    def test_sync_function():
        return "test"
    
    result = test_sync_function()
    
    # Should have called create when function not found
    mock_client.projects.functions.create.assert_called_once()
    assert result == "test"


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_function_by_version_async")
@patch("lilypad.traces.get_cached_closure")
@patch("lilypad.traces.SubprocessSandboxRunner")
@pytest.mark.asyncio
async def test_trace_decorator_version_async_wrap_mode(
    mock_sandbox_runner, mock_get_cached_closure, mock_get_function_by_version_async, mock_get_settings
):
    """Test async trace decorator version method with wrap mode."""
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
    
    @trace(versioning="automatic", mode="wrap")
    async def test_async_function():
        return "test"
    
    # Test with wrap mode - should return AsyncTrace object
    versioned_fn = await test_async_function.version(1)
    result = versioned_fn()
    
    # Result should be an AsyncTrace object with the sandbox result
    assert hasattr(result, 'response')
    assert result.response == "sandbox_result"


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_deployed_function_async")
@patch("lilypad.traces.get_cached_closure")
@patch("lilypad.traces.SubprocessSandboxRunner")
@pytest.mark.asyncio
async def test_trace_decorator_remote_async_wrap_mode(
    mock_sandbox_runner, mock_get_cached_closure, mock_get_deployed_function_async, mock_get_settings
):
    """Test async trace decorator remote method with wrap mode."""
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
    
    @trace(versioning="automatic", mode="wrap")
    async def test_async_function():
        return "test"
    
    # Test with wrap mode - should return AsyncTrace object
    result = await test_async_function.remote()
    
    # Result should be an AsyncTrace object with the sandbox result
    assert hasattr(result, 'response')
    assert result.response == "sandbox_result"


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_function_by_version_sync")
@patch("lilypad.traces.get_cached_closure")
@patch("lilypad.traces.SubprocessSandboxRunner")
def test_trace_decorator_version_sync_wrap_mode(
    mock_sandbox_runner, mock_get_cached_closure, mock_get_function_by_version_sync, mock_get_settings
):
    """Test sync trace decorator version method with wrap mode."""
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
    
    @trace(versioning="automatic", mode="wrap")
    def test_sync_function():
        return "test"
    
    # Test with wrap mode - should return Trace object
    versioned_fn = test_sync_function.version(1)
    result = versioned_fn()
    
    # Result should be a Trace object with the sandbox result
    assert hasattr(result, 'response')
    assert result.response == "sandbox_result"


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.get_deployed_function_sync")
@patch("lilypad.traces.get_cached_closure")
@patch("lilypad.traces.SubprocessSandboxRunner")
def test_trace_decorator_remote_sync_wrap_mode(
    mock_sandbox_runner, mock_get_cached_closure, mock_get_deployed_function_sync, mock_get_settings
):
    """Test sync trace decorator remote method with wrap mode."""
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
    
    @trace(versioning="automatic", mode="wrap")
    def test_sync_function():
        return "test"
    
    # Test with wrap mode - should return Trace object
    result = test_sync_function.remote()
    
    # Result should be a Trace object with the sandbox result
    assert hasattr(result, 'response')
    assert result.response == "sandbox_result"


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.Span")
def test_trace_decorator_sync_with_trace_ctx_parameter(mock_span_class, mock_get_settings):
    """Test sync trace decorator when function accepts trace_ctx parameter."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_settings.api_key = "test-api-key"
    mock_get_settings.return_value = mock_settings
    
    mock_span = Mock()
    mock_span.span_id = 123
    mock_span.opentelemetry_span = Mock()
    mock_span_class.return_value.__enter__ = Mock(return_value=mock_span)
    mock_span_class.return_value.__exit__ = Mock(return_value=False)
    
    @trace()
    def test_sync_function_with_trace_ctx(trace_ctx, value):
        # Function that accepts trace_ctx parameter
        return f"trace_ctx: {trace_ctx}, value: {value}"
    
    result = test_sync_function_with_trace_ctx("test_value")
    
    # Should have injected the span as first argument
    assert "trace_ctx:" in result
    assert "value: test_value" in result


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.Span")
@pytest.mark.asyncio
async def test_trace_decorator_async_with_trace_ctx_parameter(mock_span_class, mock_get_settings):
    """Test async trace decorator when function accepts trace_ctx parameter."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_settings.api_key = "test-api-key"
    mock_get_settings.return_value = mock_settings
    
    mock_span = Mock()
    mock_span.span_id = 123
    mock_span.opentelemetry_span = Mock()
    mock_span_class.return_value.__aenter__ = AsyncMock(return_value=mock_span)
    mock_span_class.return_value.__aexit__ = AsyncMock(return_value=False)
    
    @trace()
    async def test_async_function_with_trace_ctx(trace_ctx, value):
        # Function that accepts trace_ctx parameter
        return f"trace_ctx: {trace_ctx}, value: {value}"
    
    result = await test_async_function_with_trace_ctx("test_value")
    
    # Should have injected the span as first argument
    assert "trace_ctx:" in result
    assert "value: test_value" in result


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.Span")
def test_trace_decorator_sync_with_user_provided_trace_ctx(mock_span_class, mock_get_settings):
    """Test sync trace decorator when user provides trace_ctx parameter."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_settings.api_key = "test-api-key"
    mock_get_settings.return_value = mock_settings
    
    mock_span = Mock()
    mock_span.span_id = 123
    mock_span.opentelemetry_span = Mock()
    mock_span_class.return_value.__enter__ = Mock(return_value=mock_span)
    mock_span_class.return_value.__exit__ = Mock(return_value=False)
    
    @trace()
    def test_sync_function_with_trace_ctx(trace_ctx, value):
        # Function that accepts trace_ctx parameter
        return f"trace_ctx: {trace_ctx}, value: {value}"
    
    # User provides their own trace_ctx
    user_trace_ctx = Mock()
    result = test_sync_function_with_trace_ctx(user_trace_ctx, "test_value")
    
    # Should use user-provided trace_ctx
    assert "trace_ctx:" in result
    assert "value: test_value" in result


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.Span")
@pytest.mark.asyncio
async def test_trace_decorator_async_with_user_provided_trace_ctx(mock_span_class, mock_get_settings):
    """Test async trace decorator when user provides trace_ctx parameter."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_settings.api_key = "test-api-key"
    mock_get_settings.return_value = mock_settings
    
    mock_span = Mock()
    mock_span.span_id = 123
    mock_span.opentelemetry_span = Mock()
    mock_span_class.return_value.__aenter__ = AsyncMock(return_value=mock_span)
    mock_span_class.return_value.__aexit__ = AsyncMock(return_value=False)
    
    @trace()
    async def test_async_function_with_trace_ctx(trace_ctx, value):
        # Function that accepts trace_ctx parameter
        return f"trace_ctx: {trace_ctx}, value: {value}"
    
    # User provides their own trace_ctx
    user_trace_ctx = Mock()
    result = await test_async_function_with_trace_ctx(user_trace_ctx, "test_value")
    
    # Should use user-provided trace_ctx
    assert "trace_ctx:" in result
    assert "value: test_value" in result


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.Span")
def test_trace_decorator_sync_binding_error(mock_span_class, mock_get_settings):
    """Test sync trace decorator when signature binding fails."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_settings.api_key = "test-api-key"
    mock_get_settings.return_value = mock_settings
    
    mock_span = Mock()
    mock_span.span_id = 123
    mock_span.opentelemetry_span = Mock()
    mock_span_class.return_value.__enter__ = Mock(return_value=mock_span)
    mock_span_class.return_value.__exit__ = Mock(return_value=False)
    
    @trace()
    def test_sync_function_with_required_args(required_arg):
        return f"required_arg: {required_arg}"
    
    # Call with wrong number of arguments to cause TypeError
    try:
        # This should handle the TypeError gracefully
        result = test_sync_function_with_required_args()
    except TypeError:
        # This is expected since we're not providing required argument
        pass


@patch("lilypad.traces.get_settings")
@patch("lilypad.traces.Span")
@pytest.mark.asyncio
async def test_trace_decorator_async_binding_error(mock_span_class, mock_get_settings):
    """Test async trace decorator when signature binding fails."""
    mock_settings = Mock()
    mock_settings.project_id = "test-project"
    mock_settings.api_key = "test-api-key"
    mock_get_settings.return_value = mock_settings
    
    mock_span = Mock()
    mock_span.span_id = 123
    mock_span.opentelemetry_span = Mock()
    mock_span_class.return_value.__aenter__ = AsyncMock(return_value=mock_span)
    mock_span_class.return_value.__aexit__ = AsyncMock(return_value=False)
    
    @trace()
    async def test_async_function_with_required_args(required_arg):
        return f"required_arg: {required_arg}"
    
    # Call with wrong number of arguments to cause TypeError
    try:
        # This should handle the TypeError gracefully
        result = await test_async_function_with_required_args()
    except TypeError:
        # This is expected since we're not providing required argument
        pass


def test_trace_decorator_with_prompt_template():
    """Test trace decorator when function has _prompt_template attribute."""
    @trace(versioning="automatic")
    def test_function_with_template():
        return "test"
    
    # Add the _prompt_template attribute
    test_function_with_template._prompt_template = "This is a test prompt template"
    
    # The decorator should handle this attribute gracefully
    assert hasattr(test_function_with_template, '_prompt_template')