"""Tests to improve coverage for client.py missing lines."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from lilypad._utils.client import (
    Lilypad, 
    AsyncLilypad,
    get_sync_client,
    get_async_client,
    _sync_singleton,
    _async_singleton,
)


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
            api_key="test_key",
            base_url="https://custom.api.com", 
            token="test_token",
            timeout=60.0,
            httpx_client=Mock()
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
            api_key="test_key",
            base_url="https://custom.api.com",
            token="test_token", 
            timeout=60.0,
            httpx_client=Mock()
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
        mock_get_settings.return_value = mock_settings
        
        mock_instance = Mock()
        mock_lilypad.return_value = mock_instance
        
        # Call with custom base_url to override env settings
        result = get_sync_client(base_url="https://custom.com")
        
        # Should use custom base_url instead of env base_url
        mock_lilypad.assert_called_once_with(
            api_key="env_key",
            base_url="https://custom.com"
        )
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
        mock_get_settings.return_value = mock_settings
        
        mock_instance = Mock()
        mock_async_lilypad.return_value = mock_instance
        
        # Call with custom base_url to override env settings
        result = get_async_client(base_url="https://custom.com")
        
        # Should use custom base_url instead of env base_url
        mock_async_lilypad.assert_called_once_with(
            api_key="env_key",
            base_url="https://custom.com"
        )
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
        result1 = _sync_singleton("key1", "https://api1.com")
        result2 = _sync_singleton("key1", "https://api2.com")
        
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
        result1 = _async_singleton("key1", loop1_id, "https://api.com")
        result2 = _async_singleton("key1", loop1_id, "https://api.com")
        
        assert result1 == mock_instance1
        assert result2 == mock_instance1  # Should be cached
        assert mock_async_lilypad.call_count == 1
        
        # Different loop ID should create new instance
        fake_loop_id = 999999
        result3 = _async_singleton("key1", fake_loop_id, "https://api.com")
        
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