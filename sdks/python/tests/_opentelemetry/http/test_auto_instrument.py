"""Tests for HTTP auto-instrumentation."""

import sys
from unittest.mock import Mock, patch, MagicMock
import pytest

from lilypad._opentelemetry.http.auto_instrument import (
    _patch_requests,
    _patch_httpx,
    _patch_aiohttp,
    _patch_urllib3,
    instrument_http_clients,
    instrument_requests,
    instrument_httpx,
    instrument_aiohttp,
    instrument_urllib3,
    uninstrument_http_clients,
)


@pytest.fixture(autouse=True)
def reset_instrumentation_state():
    """Reset instrumentation state before and after each test."""
    import lilypad._opentelemetry.http.auto_instrument as auto_instrument

    # Store original state
    original_instrumented = auto_instrument._INSTRUMENTED
    original_methods = auto_instrument._ORIGINAL_METHODS.copy()

    # Reset state
    auto_instrument._INSTRUMENTED = False
    auto_instrument._ORIGINAL_METHODS.clear()

    yield

    # Restore original state
    auto_instrument._INSTRUMENTED = original_instrumented
    auto_instrument._ORIGINAL_METHODS = original_methods


def test_patch_requests():
    """Test patching requests library."""
    # Create mock requests module
    mock_requests = Mock()
    mock_session = Mock()
    mock_requests.Session = mock_session
    original_request = Mock()
    mock_session.request = original_request

    # Temporarily add to sys.modules
    sys.modules["requests"] = mock_requests

    try:
        # Patch requests
        _patch_requests()

        # Verify request method was replaced
        assert mock_session.request != original_request

        # Test the patched method
        patched_request = mock_session.request

        # Mock response
        mock_response = Mock()
        original_request.return_value = mock_response

        # Call patched method
        with patch("lilypad._opentelemetry.http.auto_instrument.inject_context") as mock_inject:
            result = patched_request(mock_session, "GET", "http://example.com", headers={"test": "header"})

            # Verify inject_context was called
            mock_inject.assert_called_once()
            # Verify original method was called
            original_request.assert_called_once()
            assert result == mock_response

    finally:
        # Clean up
        del sys.modules["requests"]


def test_patch_requests_no_headers():
    """Test patching requests when no headers provided."""
    mock_requests = Mock()
    mock_session = Mock()
    mock_requests.Session = mock_session
    original_request = Mock()
    mock_session.request = original_request

    sys.modules["requests"] = mock_requests

    try:
        _patch_requests()
        patched_request = mock_session.request

        with patch("lilypad._opentelemetry.http.auto_instrument.inject_context") as mock_inject:
            patched_request(mock_session, "GET", "http://example.com")
            mock_inject.assert_called_once_with({})

    finally:
        del sys.modules["requests"]


def test_patch_requests_not_installed():
    """Test patching when requests is not installed."""
    # Ensure requests is not in sys.modules
    if "requests" in sys.modules:
        del sys.modules["requests"]

    # Should not raise error
    _patch_requests()


def test_patch_httpx_sync():
    """Test patching httpx sync client."""
    mock_httpx = Mock()
    mock_client = Mock()
    mock_httpx.Client = mock_client
    original_request = Mock()
    mock_client.request = original_request

    sys.modules["httpx"] = mock_httpx

    try:
        _patch_httpx()
        patched_request = mock_client.request

        # Test sync client
        with patch("lilypad._opentelemetry.http.auto_instrument.inject_context") as mock_inject:
            mock_response = Mock()
            original_request.return_value = mock_response

            result = patched_request(mock_client, "GET", "http://example.com", headers={"test": "header"})

            mock_inject.assert_called_once()
            assert result == mock_response

    finally:
        del sys.modules["httpx"]


@pytest.mark.asyncio
async def test_patch_httpx_async():
    """Test patching httpx async client."""
    mock_httpx = Mock()
    mock_async_client = Mock()
    mock_httpx.AsyncClient = mock_async_client

    # Create async mock
    async def async_request_mock(*args, **kwargs):
        return Mock()

    original_async_request = MagicMock()
    original_async_request.side_effect = async_request_mock
    mock_async_client.request = original_async_request

    sys.modules["httpx"] = mock_httpx

    try:
        _patch_httpx()
        patched_request = mock_async_client.request

        with patch("lilypad._opentelemetry.http.auto_instrument.inject_context") as mock_inject:
            # Call the patched async method
            result = await patched_request(mock_async_client, "GET", "http://example.com")

            mock_inject.assert_called_once()
            assert result is not None

    finally:
        del sys.modules["httpx"]


def test_patch_httpx_not_installed():
    """Test patching when httpx is not installed."""
    if "httpx" in sys.modules:
        del sys.modules["httpx"]

    # Should not raise error
    _patch_httpx()


@pytest.mark.asyncio
async def test_patch_aiohttp():
    """Test patching aiohttp ClientSession."""
    mock_aiohttp = Mock()
    mock_session = Mock()
    mock_aiohttp.ClientSession = mock_session

    # Create async mock for _request
    async def async_request_mock(*args, **kwargs):
        return Mock()

    original_request = MagicMock()
    original_request.side_effect = async_request_mock
    mock_session._request = original_request

    sys.modules["aiohttp"] = mock_aiohttp

    try:
        _patch_aiohttp()
        patched_request = mock_session._request

        with patch("lilypad._opentelemetry.http.auto_instrument.inject_context") as mock_inject:
            result = await patched_request(mock_session, "GET", "http://example.com", headers={"test": "header"})

            mock_inject.assert_called_once()
            assert result is not None

    finally:
        del sys.modules["aiohttp"]


def test_patch_aiohttp_not_installed():
    """Test patching when aiohttp is not installed."""
    if "aiohttp" in sys.modules:
        del sys.modules["aiohttp"]

    # Should not raise error
    _patch_aiohttp()


def test_patch_urllib3():
    """Test patching urllib3 HTTPConnectionPool."""
    mock_urllib3 = Mock()
    mock_pool = Mock()
    mock_urllib3.HTTPConnectionPool = mock_pool
    original_urlopen = Mock()
    mock_pool.urlopen = original_urlopen

    sys.modules["urllib3"] = mock_urllib3

    try:
        _patch_urllib3()
        patched_urlopen = mock_pool.urlopen

        with patch("lilypad._opentelemetry.http.auto_instrument.inject_context") as mock_inject:
            mock_response = Mock()
            original_urlopen.return_value = mock_response

            result = patched_urlopen(mock_pool, "GET", "/path", headers={"test": "header"})

            mock_inject.assert_called_once()
            assert result == mock_response

    finally:
        del sys.modules["urllib3"]


def test_patch_urllib3_not_installed():
    """Test patching when urllib3 is not installed."""
    if "urllib3" in sys.modules:
        del sys.modules["urllib3"]

    # Should not raise error
    _patch_urllib3()


def test_instrument_http_clients():
    """Test instrument_http_clients calls all patch functions."""
    with (
        patch("lilypad._opentelemetry.http.auto_instrument._patch_requests") as mock_requests,
        patch("lilypad._opentelemetry.http.auto_instrument._patch_httpx") as mock_httpx,
        patch("lilypad._opentelemetry.http.auto_instrument._patch_aiohttp") as mock_aiohttp,
        patch("lilypad._opentelemetry.http.auto_instrument._patch_urllib3") as mock_urllib3,
    ):
        instrument_http_clients()

        mock_requests.assert_called_once()
        mock_httpx.assert_called_once()
        mock_aiohttp.assert_called_once()
        mock_urllib3.assert_called_once()

        import lilypad._opentelemetry.http.auto_instrument as auto_instrument

        assert auto_instrument._INSTRUMENTED is True


def test_instrument_http_clients_idempotent():
    """Test that instrument_http_clients is idempotent."""
    with patch("lilypad._opentelemetry.http.auto_instrument._patch_requests") as mock_requests:
        import lilypad._opentelemetry.http.auto_instrument as auto_instrument

        # First call should instrument
        instrument_http_clients()
        assert auto_instrument._INSTRUMENTED is True

        # Reset mocks
        mock_requests.reset_mock()

        # Second call should not patch again
        instrument_http_clients()

        # Should not call patch functions
        mock_requests.assert_not_called()


def test_instrument_requests():
    """Test instrument_requests function."""
    with patch("lilypad._opentelemetry.http.auto_instrument._patch_requests") as mock_patch:
        instrument_requests()
        mock_patch.assert_called_once()


def test_instrument_httpx():
    """Test instrument_httpx function."""
    with patch("lilypad._opentelemetry.http.auto_instrument._patch_httpx") as mock_patch:
        instrument_httpx()
        mock_patch.assert_called_once()


def test_instrument_aiohttp():
    """Test instrument_aiohttp function."""
    with patch("lilypad._opentelemetry.http.auto_instrument._patch_aiohttp") as mock_patch:
        instrument_aiohttp()
        mock_patch.assert_called_once()


def test_instrument_urllib3():
    """Test instrument_urllib3 function."""
    with patch("lilypad._opentelemetry.http.auto_instrument._patch_urllib3") as mock_patch:
        instrument_urllib3()
        mock_patch.assert_called_once()


def test_uninstrument_http_clients():
    """Test uninstrument_http_clients function."""
    import lilypad._opentelemetry.http.auto_instrument as auto_instrument

    # First instrument
    instrument_http_clients()
    assert auto_instrument._INSTRUMENTED is True

    # Then uninstrument
    uninstrument_http_clients()
    assert auto_instrument._INSTRUMENTED is False
