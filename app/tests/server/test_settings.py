"""Tests for the settings module."""

from unittest.mock import patch
from lilypad.server.settings import Settings


def test_remote_client_hostname_with_valid_url():
    """Test remote_client_hostname with valid URL."""
    with patch.dict("os.environ", {"LILYPAD_CLIENT_URL": "https://example.com:8080/path"}):
        settings = Settings()
        assert settings.remote_client_hostname == "example.com"


def test_remote_client_hostname_with_url_no_hostname():
    """Test remote_client_hostname when URL has no hostname (covers line 150)."""
    # Test with URL that would return None for hostname  
    # Use 'local' environment and set remote_client_url to a URL without hostname
    with patch.dict("os.environ", {
        "LILYPAD_ENVIRONMENT": "local",
        "LILYPAD_REMOTE_CLIENT_URL": "file:///local/path"
    }):
        settings = Settings()
        # Should return empty string when hostname is None
        assert settings.remote_client_hostname == ""


def test_remote_client_hostname_with_invalid_url():
    """Test remote_client_hostname with malformed URL."""
    with patch.dict("os.environ", {"LILYPAD_CLIENT_URL": "not-a-valid-url"}):
        settings = Settings()
        # Should handle malformed URLs gracefully
        result = settings.remote_client_hostname
        assert isinstance(result, str)  # Should still return a string