"""Test cases for client utilities."""

import asyncio
import pytest
from unittest.mock import Mock, AsyncMock, patch

from lilypad._utils.client import (
    Lilypad,
    AsyncLilypad,
    get_sync_client,
    get_async_client,
    _sync_singleton,
    _async_singleton,
    _SafeRawClientWrapper,
    _SafeAsyncRawClientWrapper,
    _noop_fallback,
    _async_noop_fallback,
)
from lilypad.generated.core.api_error import ApiError
from lilypad.generated.errors.not_found_error import NotFoundError


def test_safe_wrapper_api_error_404():
    """Test that wrapper handles 404 errors by raising NotFoundError (line 79)."""
    mock_raw_client = Mock()
    api_error = ApiError(status_code=404, body="Not found", headers={})
    mock_raw_client.some_method = Mock(side_effect=api_error)

    wrapper = _SafeRawClientWrapper(mock_raw_client)

    with pytest.raises(NotFoundError):
        wrapper.some_method()


def test_safe_wrapper_api_error_non_404():
    """Test that wrapper re-raises non-404 API errors."""
    mock_raw_client = Mock()
    api_error = ApiError(status_code=500, body="Server error", headers={})
    mock_raw_client.some_method = Mock(side_effect=api_error)

    wrapper = _SafeRawClientWrapper(mock_raw_client)

    with pytest.raises(ApiError) as exc_info:
        wrapper.some_method()
    assert exc_info.value.status_code == 500


@pytest.mark.asyncio
async def test_safe_async_wrapper_api_error_404():
    """Test that async wrapper handles 404 errors by raising NotFoundError."""
    mock_raw_client = Mock()
    api_error = ApiError(status_code=404, body="Not found", headers={})
    mock_raw_client.some_method = AsyncMock(side_effect=api_error)

    wrapper = _SafeAsyncRawClientWrapper(mock_raw_client)

    with pytest.raises(NotFoundError):
        await wrapper.some_method()


@pytest.mark.asyncio
async def test_safe_async_wrapper_api_error_non_404():
    """Test that async wrapper re-raises non-404 API errors."""
    mock_raw_client = Mock()
    api_error = ApiError(status_code=500, body="Server error", headers={})
    mock_raw_client.some_method = AsyncMock(side_effect=api_error)

    wrapper = _SafeAsyncRawClientWrapper(mock_raw_client)

    with pytest.raises(ApiError) as exc_info:
        await wrapper.some_method()
    assert exc_info.value.status_code == 500


def test_lilypad_wrap_clients_without_projects():
    """Test Lilypad client when projects attribute doesn't exist (line 145)."""
    # Create a mock client without projects attribute by mocking hasattr
    with patch("lilypad.generated.client.Lilypad") as mock_base:
        mock_instance = Mock()
        mock_base.return_value = mock_instance

        # Mock hasattr to return False for projects
        with patch("builtins.hasattr") as mock_hasattr:
            mock_hasattr.return_value = False

            client = Lilypad(api_key="test-key")
            # Should not raise an error even without projects


def test_lilypad_wrap_clients_exception_handling():
    """Test Lilypad client exception handling during wrapping (lines 148-149)."""
    with patch("lilypad.generated.client.Lilypad") as mock_base:
        mock_instance = Mock()
        mock_instance.projects = Mock()

        # Mock _wrap_raw_clients to raise an exception
        def side_effect(*args):
            raise Exception("Test exception")

        mock_base.return_value = mock_instance

        with (
            patch("lilypad._utils.client.Lilypad._wrap_raw_clients", side_effect=side_effect),
            patch("lilypad._utils.client.logger") as mock_logger,
        ):
            # Should handle the exception gracefully
            client = Lilypad(api_key="test-key")
            mock_logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_async_lilypad_wrap_clients_exception_handling():
    """Test AsyncLilypad client exception handling during wrapping."""
    with patch("lilypad.generated.client.AsyncLilypad") as mock_base:
        mock_instance = Mock()
        mock_instance.projects = Mock()

        # Mock _wrap_raw_clients to raise an exception
        def side_effect(*args):
            raise Exception("Test exception")

        mock_base.return_value = mock_instance

        with (
            patch("lilypad._utils.client.AsyncLilypad._wrap_raw_clients", side_effect=side_effect),
            patch("lilypad._utils.client.logger") as mock_logger,
        ):
            # Should handle the exception gracefully
            client = AsyncLilypad(api_key="test-key")
            mock_logger.error.assert_called_once()


@pytest.mark.asyncio
async def test_async_lilypad_wrap_clients_success():
    """Test AsyncLilypad client successful wrapping - covers line 235."""
    with patch("lilypad._utils.client.logger") as mock_logger:
        # Create a real client to ensure the success path is tested
        client = AsyncLilypad(api_key="test-key")

        # Verify the success debug message was logged (line 235)
        # Check that the debug call was made with the expected message
        debug_calls = [
            call for call in mock_logger.debug.call_args_list if "Successfully wrapped all AsyncRawClients" in str(call)
        ]
        assert len(debug_calls) > 0, "Expected debug message about successful wrapping not found"


def test_sync_lilypad_wrap_clients_success():
    """Test Lilypad client successful wrapping - covers line 146."""
    with patch("lilypad._utils.client.logger") as mock_logger:
        # Create a real client to ensure the success path is tested
        client = Lilypad(api_key="test-key")

        # Verify the success debug message was logged (line 146)
        # Check that the debug call was made with the expected message
        debug_calls = [
            call for call in mock_logger.debug.call_args_list if "Successfully wrapped all RawClients" in str(call)
        ]
        assert len(debug_calls) > 0, "Expected debug message about successful wrapping not found"


def test_noop_fallback():
    """Test the noop fallback function."""
    result = _noop_fallback(1, 2, 3, a=4, b=5)
    assert result is None


@pytest.mark.asyncio
async def test_async_noop_fallback():
    """Test the async noop fallback function."""
    result = await _async_noop_fallback(1, 2, 3, a=4, b=5)
    assert result is None


def test_wrapper_basic_attribute_access():
    """Test that wrapper passes through attributes."""
    mock_raw_client = Mock()
    mock_raw_client.some_attribute = "test_value"

    wrapper = _SafeRawClientWrapper(mock_raw_client)
    assert wrapper.some_attribute == "test_value"


def test_wrapper_method_call_success():
    """Test that wrapper passes through successful method calls."""
    mock_raw_client = Mock()
    mock_raw_client.some_method = Mock(return_value="success")

    wrapper = _SafeRawClientWrapper(mock_raw_client)
    result = wrapper.some_method("arg1", key="value")

    assert result == "success"
    mock_raw_client.some_method.assert_called_once_with("arg1", key="value")


def test_wrapper_404_conversion():
    """Test that wrapper converts 404 ApiError to NotFoundError."""
    mock_raw_client = Mock()
    api_error = ApiError(status_code=404, body="Not Found", headers={})
    mock_raw_client.get_resource = Mock(side_effect=api_error)

    wrapper = _SafeRawClientWrapper(mock_raw_client)

    with pytest.raises(NotFoundError) as exc_info:
        wrapper.get_resource("123")

    assert exc_info.value.body == "Not Found"


def test_wrapper_other_api_errors():
    """Test that wrapper passes through non-404 ApiErrors."""
    mock_raw_client = Mock()
    api_error = ApiError(status_code=500, body="Server Error", headers={})
    mock_raw_client.get_resource = Mock(side_effect=api_error)

    wrapper = _SafeRawClientWrapper(mock_raw_client)

    with pytest.raises(ApiError) as exc_info:
        wrapper.get_resource("123")

    assert exc_info.value.status_code == 500
    assert exc_info.value.body == "Server Error"


@pytest.mark.asyncio
async def test_async_wrapper_basic_attribute_access():
    """Test that async wrapper passes through attributes."""
    mock_raw_client = Mock()
    mock_raw_client.some_attribute = "test_value"

    wrapper = _SafeAsyncRawClientWrapper(mock_raw_client)
    assert wrapper.some_attribute == "test_value"


@pytest.mark.asyncio
async def test_async_wrapper_method_call_success():
    """Test that async wrapper passes through successful method calls."""
    mock_raw_client = Mock()
    mock_raw_client.some_method = AsyncMock(return_value="success")

    wrapper = _SafeAsyncRawClientWrapper(mock_raw_client)
    result = await wrapper.some_method("arg1", key="value")

    assert result == "success"
    mock_raw_client.some_method.assert_called_once_with("arg1", key="value")


@pytest.mark.asyncio
async def test_async_wrapper_404_conversion():
    """Test that async wrapper converts 404 ApiError to NotFoundError."""
    mock_raw_client = Mock()
    api_error = ApiError(status_code=404, body="Not Found", headers={})
    mock_raw_client.get_resource = AsyncMock(side_effect=api_error)

    wrapper = _SafeAsyncRawClientWrapper(mock_raw_client)

    with pytest.raises(NotFoundError) as exc_info:
        await wrapper.get_resource("123")

    assert exc_info.value.body == "Not Found"


@patch("lilypad._utils.client._BaseLilypad.__init__")
def test_client_initialization(mock_super_init):
    """Test Lilypad client initialization."""
    mock_super_init.return_value = None

    client = Lilypad(api_key="test_key", base_url="https://api.test.com", timeout=30.0)

    mock_super_init.assert_called_once_with(
        base_url="https://api.test.com",
        api_key="test_key",
        token=None,
        timeout=30.0,
        follow_redirects=True,
        httpx_client=None,
    )


@patch("lilypad._utils.client._BaseLilypad.__init__")
def test_client_initialization_failure(mock_super_init):
    """Test client initialization with failure."""
    mock_super_init.side_effect = Exception("Init failed")

    with pytest.raises(RuntimeError) as exc_info:
        Lilypad(api_key="test_key")

    assert "Client initialization failed" in str(exc_info.value)


@patch("lilypad._utils.client._BaseLilypad.__init__")
def test_wrap_raw_clients(mock_super_init):
    """Test _wrap_raw_clients method."""
    mock_super_init.return_value = None

    # Create a mock client structure
    mock_projects = Mock()
    mock_projects._raw_client = Mock()

    mock_functions = Mock()
    mock_functions._raw_client = Mock()
    mock_projects.functions = mock_functions

    client = Lilypad(api_key="test_key")
    client.projects = mock_projects

    # Manually call _wrap_raw_clients
    client._wrap_raw_clients(client.projects)

    # Verify raw clients were wrapped
    assert isinstance(mock_projects._raw_client, _SafeRawClientWrapper)
    assert isinstance(mock_functions._raw_client, _SafeRawClientWrapper)


@patch("lilypad._utils.client._BaseAsyncLilypad.__init__")
def test_async_client_initialization(mock_super_init):
    """Test AsyncLilypad client initialization."""
    mock_super_init.return_value = None

    client = AsyncLilypad(api_key="test_key", base_url="https://api.test.com", timeout=30.0)

    mock_super_init.assert_called_once_with(
        base_url="https://api.test.com",
        api_key="test_key",
        token=None,
        timeout=30.0,
        follow_redirects=True,
        httpx_client=None,
    )


@patch("lilypad._utils.client.get_settings")
@patch("lilypad._utils.client.Lilypad")
def test_get_sync_client_with_api_key(mock_lilypad, mock_get_settings):
    """Test get_sync_client with explicit API key."""
    mock_instance = Mock()
    mock_lilypad.return_value = mock_instance

    # Setup mock settings for timeout
    mock_settings = Mock()
    mock_settings.timeout = 10.0
    mock_get_settings.return_value = mock_settings

    result = get_sync_client(api_key="test_key", base_url="https://test.com")

    assert result == mock_instance
    # Now get_settings is called to get the timeout
    mock_get_settings.assert_called()


@patch("lilypad._utils.client.get_settings")
def test_get_sync_client_no_api_key(mock_get_settings):
    """Test get_sync_client without API key."""
    mock_settings = Mock()
    mock_settings.api_key = None
    mock_settings.timeout = 10.0
    mock_get_settings.return_value = mock_settings

    with pytest.raises(RuntimeError) as exc_info:
        get_sync_client()

    assert "API key not provided" in str(exc_info.value)


@patch("lilypad._utils.client.get_settings")
@patch("lilypad._utils.client._sync_singleton")
def test_get_sync_client_from_env(mock_singleton, mock_get_settings):
    """Test get_sync_client using environment settings."""
    mock_settings = Mock()
    mock_settings.api_key = "env_key"
    mock_settings.base_url = "https://env.com"
    mock_settings.timeout = 10.0
    mock_get_settings.return_value = mock_settings

    mock_instance = Mock()
    mock_singleton.return_value = mock_instance

    result = get_sync_client()

    assert result == mock_instance
    mock_singleton.assert_called_once_with("env_key", "https://env.com", 10.0)


@pytest.mark.asyncio
async def test_get_async_client_outside_loop():
    """Test get_async_client called outside event loop."""
    # Simulate being outside an event loop
    with (
        patch("asyncio.get_running_loop", side_effect=RuntimeError("No running loop")),
        pytest.raises(RuntimeError) as exc_info,
    ):
        get_async_client(api_key="test_key")

    assert "must be called from within an active event loop" in str(exc_info.value)


@pytest.mark.asyncio
@patch("lilypad._utils.client.get_settings")
@patch("lilypad._utils.client._async_singleton")
async def test_get_async_client_success(mock_singleton, mock_get_settings):
    """Test successful async client creation."""
    mock_settings = Mock()
    mock_settings.api_key = "test_key"
    mock_settings.base_url = "https://test.com"
    mock_settings.timeout = 10.0
    mock_get_settings.return_value = mock_settings

    mock_instance = Mock()
    mock_singleton.return_value = mock_instance

    result = get_async_client()

    assert result == mock_instance
    # Verify singleton was called with correct loop ID and timeout
    loop = asyncio.get_running_loop()
    mock_singleton.assert_called_once_with("test_key", id(loop), "https://test.com", 10.0)


@patch("lilypad._utils.client.Lilypad")
def test_sync_singleton_caching(mock_lilypad):
    """Test that _sync_singleton caches clients."""
    mock_instance1 = Mock()
    mock_instance2 = Mock()
    mock_lilypad.side_effect = [mock_instance1, mock_instance2]

    # Clear cache first
    _sync_singleton.cache_clear()

    # First call
    result1 = _sync_singleton("key1", "https://test.com", 10.0)
    assert result1 == mock_instance1

    # Second call with same key - should return cached
    result2 = _sync_singleton("key1", "https://test.com", 10.0)
    assert result2 == mock_instance1

    # Call with different key - should create new
    result3 = _sync_singleton("key2", "https://test.com", 10.0)
    assert result3 == mock_instance2

    # Verify Lilypad was only called twice
    assert mock_lilypad.call_count == 2


@pytest.mark.asyncio
@patch("lilypad._utils.client.AsyncLilypad")
async def test_async_singleton_caching(mock_async_lilypad):
    """Test that _async_singleton caches clients per loop."""
    mock_instance = Mock()
    mock_async_lilypad.return_value = mock_instance

    # Clear cache first
    _async_singleton.cache_clear()

    loop_id = id(asyncio.get_running_loop())

    # First call
    result1 = _async_singleton("key1", loop_id, "https://test.com", 10.0)
    assert result1 == mock_instance

    # Second call with same key and loop - should return cached
    result2 = _async_singleton("key1", loop_id, "https://test.com", 10.0)
    assert result2 == mock_instance

    # Verify AsyncLilypad was only called once
    assert mock_async_lilypad.call_count == 1


def test_client_initialization_with_token():
    """Test client initialization with token parameter."""
    with patch("lilypad._utils.client._BaseLilypad.__init__") as mock_super_init:
        mock_super_init.return_value = None

        client = Lilypad(api_key="test_key", token="test_token")

        mock_super_init.assert_called_once_with(
            base_url=None,
            api_key="test_key",
            token="test_token",
            timeout=None,
            follow_redirects=True,
            httpx_client=None,
        )


def test_client_initialization_with_all_params():
    """Test client initialization with all parameters."""
    with patch("lilypad._utils.client._BaseLilypad.__init__") as mock_super_init:
        mock_super_init.return_value = None

        client = Lilypad(
            api_key="test_key", base_url="https://custom.api.com", token="test_token", timeout=60.0, httpx_client=Mock()
        )

        assert mock_super_init.called


def test_async_client_initialization_with_token():
    """Test async client initialization with token parameter."""
    with patch("lilypad._utils.client._BaseAsyncLilypad.__init__") as mock_super_init:
        mock_super_init.return_value = None

        client = AsyncLilypad(api_key="test_key", token="test_token")

        mock_super_init.assert_called_once_with(
            base_url=None,
            api_key="test_key",
            token="test_token",
            timeout=None,
            follow_redirects=True,
            httpx_client=None,
        )


def test_async_client_initialization_with_all_params():
    """Test async client initialization with all parameters."""
    with patch("lilypad._utils.client._BaseAsyncLilypad.__init__") as mock_super_init:
        mock_super_init.return_value = None

        client = AsyncLilypad(
            api_key="test_key", base_url="https://custom.api.com", token="test_token", timeout=60.0, httpx_client=Mock()
        )

        assert mock_super_init.called


def test_sync_client_initialization_missing_api_key():
    """Test sync client creation without API key."""
    with patch("lilypad._utils.client.get_settings") as mock_get_settings:
        mock_settings = Mock()
        mock_settings.api_key = None
        mock_get_settings.return_value = mock_settings

        with pytest.raises(RuntimeError, match="API key not provided"):
            get_sync_client()


def test_sync_client_with_custom_params():
    """Test sync client creation with custom parameters."""
    with (
        patch("lilypad._utils.client.get_settings") as mock_get_settings,
        patch("lilypad._utils.client.Lilypad") as mock_lilypad,
    ):
        mock_settings = Mock()
        mock_settings.api_key = "env_key"
        mock_settings.base_url = "https://env.com"
        mock_settings.timeout = 10.0
        mock_get_settings.return_value = mock_settings

        mock_instance = Mock()
        mock_lilypad.return_value = mock_instance

        # Call with custom base_url to override env settings
        result = get_sync_client(base_url="https://custom.com")

        # Should use custom base_url instead of env base_url, with default timeout
        mock_lilypad.assert_called_once_with(api_key="env_key", base_url="https://custom.com", timeout=10.0)
        assert result == mock_instance


@pytest.mark.asyncio
async def test_async_client_initialization_missing_api_key():
    """Test async client creation without API key."""
    with patch("lilypad._utils.client.get_settings") as mock_get_settings:
        mock_settings = Mock()
        mock_settings.api_key = None
        mock_get_settings.return_value = mock_settings

        with pytest.raises(RuntimeError, match="API key not provided"):
            get_async_client()


@pytest.mark.asyncio
async def test_async_client_with_custom_params():
    """Test async client creation with custom parameters."""
    with (
        patch("lilypad._utils.client.get_settings") as mock_get_settings,
        patch("lilypad._utils.client.AsyncLilypad") as mock_async_lilypad,
    ):
        mock_settings = Mock()
        mock_settings.api_key = "env_key"
        mock_settings.base_url = "https://env.com"
        mock_settings.timeout = 10.0
        mock_get_settings.return_value = mock_settings

        mock_instance = Mock()
        mock_async_lilypad.return_value = mock_instance

        # Call with custom base_url to override env settings
        result = get_async_client(base_url="https://custom.com")

        # Should use custom base_url instead of env base_url, with default timeout
        mock_async_lilypad.assert_called_once_with(api_key="env_key", base_url="https://custom.com", timeout=10.0)
        assert result == mock_instance


def test_wrap_raw_clients_recursive():
    """Test _wrap_raw_clients with nested clients."""
    with patch("lilypad._utils.client._BaseLilypad.__init__") as mock_super_init:
        mock_super_init.return_value = None

        # Create nested mock structure
        mock_root = Mock()
        mock_root._raw_client = Mock()

        mock_child1 = Mock()
        mock_child1._raw_client = Mock()
        mock_root.child1 = mock_child1

        mock_child2 = Mock()
        mock_child2._raw_client = Mock()
        mock_child1.child2 = mock_child2

        client = Lilypad(api_key="test_key")
        client.projects = mock_root

        # Manually call _wrap_raw_clients
        client._wrap_raw_clients(client.projects)

        # Should wrap all nested raw clients
        from lilypad._utils.client import _SafeRawClientWrapper

        assert isinstance(mock_root._raw_client, _SafeRawClientWrapper)
        assert isinstance(mock_child1._raw_client, _SafeRawClientWrapper)
        assert isinstance(mock_child2._raw_client, _SafeRawClientWrapper)


def test_async_wrap_raw_clients_recursive():
    """Test AsyncLilypad _wrap_raw_clients with nested clients."""
    with patch("lilypad._utils.client._BaseAsyncLilypad.__init__") as mock_super_init:
        mock_super_init.return_value = None

        # Create nested mock structure
        mock_root = Mock()
        mock_root._raw_client = Mock()

        mock_child1 = Mock()
        mock_child1._raw_client = Mock()
        mock_root.child1 = mock_child1

        client = AsyncLilypad(api_key="test_key")
        client.projects = mock_root

        # Manually call _wrap_raw_clients
        client._wrap_raw_clients(client.projects)

        # Should wrap all nested raw clients
        from lilypad._utils.client import _SafeAsyncRawClientWrapper

        assert isinstance(mock_root._raw_client, _SafeAsyncRawClientWrapper)
        assert isinstance(mock_child1._raw_client, _SafeAsyncRawClientWrapper)


def test_sync_singleton_cache_different_base_urls():
    """Test _sync_singleton caches separately for different base URLs."""
    with patch("lilypad._utils.client.Lilypad") as mock_lilypad:
        mock_instance1 = Mock()
        mock_instance2 = Mock()
        mock_lilypad.side_effect = [mock_instance1, mock_instance2]

        # Clear cache first
        _sync_singleton.cache_clear()

        # Same key, different base URLs should create different instances
        result1 = _sync_singleton("key1", "https://api1.com", 10.0)
        result2 = _sync_singleton("key1", "https://api2.com", 10.0)

        assert result1 == mock_instance1
        assert result2 == mock_instance2
        assert result1 != result2
        assert mock_lilypad.call_count == 2


@pytest.mark.asyncio
async def test_async_singleton_cache_different_loops():
    """Test _async_singleton caches separately for different event loops."""
    import asyncio

    with patch("lilypad._utils.client.AsyncLilypad") as mock_async_lilypad:
        mock_instance1 = Mock()
        mock_instance2 = Mock()
        mock_async_lilypad.side_effect = [mock_instance1, mock_instance2]

        # Clear cache first
        _async_singleton.cache_clear()

        loop1_id = id(asyncio.get_running_loop())

        # Same key, same loop should return cached
        result1 = _async_singleton("key1", loop1_id, "https://api.com", 10.0)
        result2 = _async_singleton("key1", loop1_id, "https://api.com", 10.0)

        assert result1 == mock_instance1
        assert result2 == mock_instance1  # Should be cached
        assert mock_async_lilypad.call_count == 1

        # Different loop ID should create new instance
        fake_loop_id = 999999
        result3 = _async_singleton("key1", fake_loop_id, "https://api.com", 10.0)

        assert result3 == mock_instance2
        assert mock_async_lilypad.call_count == 2


def test_client_attribute_error_handling():
    """Test client handles missing attributes gracefully."""
    with patch("lilypad._utils.client._BaseLilypad.__init__") as mock_super_init:
        mock_super_init.return_value = None

        client = Lilypad(api_key="test_key")

        # Mock client that doesn't have projects attribute
        with patch("builtins.hasattr", return_value=False):
            # Should not raise when projects doesn't exist
            client._wrap_raw_clients(None)  # Should handle None gracefully


def test_async_client_attribute_error_handling():
    """Test async client handles missing attributes gracefully."""
    with patch("lilypad._utils.client._BaseAsyncLilypad.__init__") as mock_super_init:
        mock_super_init.return_value = None

        client = AsyncLilypad(api_key="test_key")

        # Mock client that doesn't have projects attribute
        with patch("builtins.hasattr", return_value=False):
            # Should not raise when projects doesn't exist
            client._wrap_raw_clients(None)  # Should handle None gracefully


def test_sync_singleton_creation_failure():
    """Test _sync_singleton handles client creation failure - covers lines 279-281."""
    with patch("lilypad._utils.client.Lilypad") as mock_lilypad:
        mock_lilypad.side_effect = Exception("Client creation failed")

        # Clear cache first
        _sync_singleton.cache_clear()

        with pytest.raises(RuntimeError, match="Failed to create cached client"):
            _sync_singleton("test_key", "https://api.com", 10.0)


@pytest.mark.asyncio
async def test_async_singleton_creation_failure():
    """Test _async_singleton handles client creation failure - covers lines 330-332."""
    with patch("lilypad._utils.client.AsyncLilypad") as mock_async_lilypad:
        mock_async_lilypad.side_effect = Exception("Async client creation failed")

        # Clear cache first
        _async_singleton.cache_clear()

        loop_id = id(asyncio.get_running_loop())

        with pytest.raises(RuntimeError, match="Failed to create cached async client"):
            _async_singleton("test_key", loop_id, "https://api.com", 10.0)


def test_async_lilypad_init_error_handling():
    """Test error handling in AsyncLilypad.__init__ - covers lines 221-223."""
    with patch("lilypad._utils.client._BaseAsyncLilypad.__init__") as mock_super_init:
        # Mock super().__init__ to raise an exception
        mock_super_init.side_effect = Exception("Base initialization failed")

        # Should catch exception and re-raise as RuntimeError
        with pytest.raises(RuntimeError, match="Async client initialization failed: Base initialization failed"):
            AsyncLilypad(api_key="test-key")
