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

    result = get_sync_client(api_key="test_key", base_url="https://test.com")

    assert result == mock_instance
    # Should not call get_settings when key is provided
    mock_get_settings.assert_not_called()


@patch("lilypad._utils.client.get_settings")
def test_get_sync_client_no_api_key(mock_get_settings):
    """Test get_sync_client without API key."""
    mock_settings = Mock()
    mock_settings.api_key = None
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
    mock_get_settings.return_value = mock_settings

    mock_instance = Mock()
    mock_singleton.return_value = mock_instance

    result = get_sync_client()

    assert result == mock_instance
    mock_singleton.assert_called_once_with("env_key", "https://env.com")


@pytest.mark.asyncio
async def test_get_async_client_outside_loop():
    """Test get_async_client called outside event loop."""
    # Simulate being outside an event loop
    with patch("asyncio.get_running_loop", side_effect=RuntimeError("No running loop")):
        with pytest.raises(RuntimeError) as exc_info:
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
    mock_get_settings.return_value = mock_settings

    mock_instance = Mock()
    mock_singleton.return_value = mock_instance

    result = get_async_client()

    assert result == mock_instance
    # Verify singleton was called with correct loop ID
    loop = asyncio.get_running_loop()
    mock_singleton.assert_called_once_with("test_key", id(loop), "https://test.com")


@patch("lilypad._utils.client.Lilypad")
def test_sync_singleton_caching(mock_lilypad):
    """Test that _sync_singleton caches clients."""
    mock_instance1 = Mock()
    mock_instance2 = Mock()
    mock_lilypad.side_effect = [mock_instance1, mock_instance2]

    # Clear cache first
    _sync_singleton.cache_clear()

    # First call
    result1 = _sync_singleton("key1", "https://test.com")
    assert result1 == mock_instance1

    # Second call with same key - should return cached
    result2 = _sync_singleton("key1", "https://test.com")
    assert result2 == mock_instance1

    # Call with different key - should create new
    result3 = _sync_singleton("key2", "https://test.com")
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
    result1 = _async_singleton("key1", loop_id, "https://test.com")
    assert result1 == mock_instance

    # Second call with same key and loop - should return cached
    result2 = _async_singleton("key1", loop_id, "https://test.com")
    assert result2 == mock_instance

    # Verify AsyncLilypad was only called once
    assert mock_async_lilypad.call_count == 1
