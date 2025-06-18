"""Tests for propagator configuration in _configure.py."""

import os
from unittest.mock import Mock, patch
import pytest
from types import ModuleType

from lilypad._configure import configure


@pytest.fixture(autouse=True)
def setup():
    """Reset environment and mocks before each test."""
    # Clear any existing LILYPAD_PROPAGATOR env var
    if "LILYPAD_PROPAGATOR" in os.environ:
        del os.environ["LILYPAD_PROPAGATOR"]

    # Reset tracer provider
    from opentelemetry import trace

    trace._TRACER_PROVIDER = None


def test_configure_with_propagator():
    """Test configure with propagator parameter."""
    with patch("lilypad._utils.context_propagation.get_propagator") as mock_get_propagator:
        # Mock the propagator to avoid actually setting global state
        mock_propagator = Mock()
        mock_get_propagator.return_value = mock_propagator

        configure(api_key="test-key", project_id="test-project", propagator="b3")

        # Should set environment variable
        assert os.environ.get("LILYPAD_PROPAGATOR") == "b3"

        # Should get propagator
        mock_get_propagator.assert_called_once()


def test_configure_with_preserve_existing_propagator():
    """Test configure with preserve_existing_propagator=True."""
    with (
        patch("lilypad._utils.context_propagation.get_propagator") as mock_get_propagator,
        patch("opentelemetry.propagate.get_global_textmap") as mock_get_global,
        patch("opentelemetry.propagate.set_global_textmap") as mock_set_global,
        patch("lilypad._configure.CompositePropagator") as mock_composite,
    ):
        # Setup mocks
        existing_propagator = Mock()
        lilypad_propagator = Mock()
        composite_propagator = Mock()

        mock_get_global.return_value = existing_propagator
        mock_get_propagator.return_value = lilypad_propagator
        mock_composite.return_value = composite_propagator

        configure(
            api_key="test-key",
            project_id="test-project",
            propagator="tracecontext",
            preserve_existing_propagator=True,
        )

        # Should create composite propagator
        mock_composite.assert_called_once_with([existing_propagator, lilypad_propagator])
        # Should set composite propagator
        mock_set_global.assert_called_once_with(composite_propagator)


def test_configure_with_auto_http_triggers_propagator_init():
    """Test that auto_http=True triggers propagator initialization."""
    with (
        patch("lilypad._utils.context_propagation.get_propagator") as mock_get_propagator,
        patch("lilypad._opentelemetry.http.instrument_http_clients") as mock_instrument,
    ):
        mock_propagator = Mock()
        mock_get_propagator.return_value = mock_propagator

        configure(api_key="test-key", project_id="test-project", auto_http=True)

        # Should initialize propagator even without explicit propagator param
        mock_get_propagator.assert_called_once()
        # Should instrument HTTP clients
        mock_instrument.assert_called_once()


def test_configure_with_instrument_list():
    """Test configure with instrument parameter."""
    with (
        patch("lilypad._utils.context_propagation.get_propagator") as mock_get_propagator,
        patch("lilypad._opentelemetry.http.instrument_requests") as mock_req,
        patch("lilypad._opentelemetry.http.instrument_httpx") as mock_httpx,
        patch("lilypad._opentelemetry.http.instrument_aiohttp") as mock_aio,
        patch("lilypad._opentelemetry.http.instrument_urllib3") as mock_urllib,
    ):
        mock_propagator = Mock()
        mock_get_propagator.return_value = mock_propagator

        # Create mock module objects with the expected __name__ attributes
        mock_requests_module = Mock(spec=ModuleType)
        mock_requests_module.__name__ = "requests"
        mock_httpx_module = Mock(spec=ModuleType)
        mock_httpx_module.__name__ = "httpx"

        configure(
            api_key="test-key",
            project_id="test-project",
            instrument=[mock_requests_module, mock_httpx_module],
        )

        # Should initialize propagator
        mock_get_propagator.assert_called_once()
        # Should only instrument specified clients
        mock_req.assert_called_once()
        mock_httpx.assert_called_once()
        mock_aio.assert_not_called()
        mock_urllib.assert_not_called()


def test_configure_with_unknown_instrument_client():
    """Test configure with unknown client in instrument list."""
    with (
        patch("lilypad._utils.context_propagation.get_propagator") as mock_get_propagator,
        patch("logging.getLogger") as mock_get_logger,
    ):
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger
        mock_propagator = Mock()
        mock_get_propagator.return_value = mock_propagator

        # Create mock module with unknown name
        mock_unknown_module = Mock(spec=ModuleType)
        mock_unknown_module.__name__ = "unknown_client"

        configure(api_key="test-key", project_id="test-project", instrument=[mock_unknown_module])

        # Should log warning
        mock_logger.warning.assert_called_once_with("Unknown HTTP client module: unknown_client")


def test_configure_all_instrument_clients():
    """Test configure with all supported clients in instrument list."""
    with (
        patch("lilypad._utils.context_propagation.get_propagator"),
        patch("lilypad._opentelemetry.http.instrument_requests") as mock_req,
        patch("lilypad._opentelemetry.http.instrument_httpx") as mock_httpx,
        patch("lilypad._opentelemetry.http.instrument_aiohttp") as mock_aio,
        patch("lilypad._opentelemetry.http.instrument_urllib3") as mock_urllib,
    ):
        # Create mock modules for all supported clients
        mock_requests = Mock(spec=ModuleType)
        mock_requests.__name__ = "requests"
        mock_httpx_module = Mock(spec=ModuleType)
        mock_httpx_module.__name__ = "httpx"
        mock_aiohttp = Mock(spec=ModuleType)
        mock_aiohttp.__name__ = "aiohttp"
        mock_urllib3 = Mock(spec=ModuleType)
        mock_urllib3.__name__ = "urllib3"

        configure(
            api_key="test-key",
            project_id="test-project",
            instrument=[mock_requests, mock_httpx_module, mock_aiohttp, mock_urllib3],
        )

        # All should be called
        mock_req.assert_called_once()
        mock_httpx.assert_called_once()
        mock_aio.assert_called_once()
        mock_urllib.assert_called_once()


def test_configure_without_propagator_or_http():
    """Test configure without propagator or HTTP instrumentation."""
    with patch("lilypad._utils.context_propagation.get_propagator") as mock_get_propagator:
        configure(api_key="test-key", project_id="test-project")

        # Should not initialize propagator
        mock_get_propagator.assert_not_called()


def test_configure_propagator_without_preserve_existing():
    """Test configure with propagator but preserve_existing_propagator=False."""
    with patch("lilypad._utils.context_propagation.get_propagator") as mock_get_propagator:
        mock_propagator = Mock()
        mock_get_propagator.return_value = mock_propagator

        configure(
            api_key="test-key",
            project_id="test-project",
            propagator="jaeger",
            preserve_existing_propagator=False,  # Default
        )

        # Should get propagator (which internally sets it via ContextPropagator)
        mock_get_propagator.assert_called_once()


def test_configure_auto_http_and_instrument_together():
    """Test that auto_http takes precedence over instrument."""
    with (
        patch("lilypad._utils.context_propagation.get_propagator"),
        patch("lilypad._opentelemetry.http.instrument_http_clients") as mock_all,
        patch("lilypad._opentelemetry.http.instrument_requests") as mock_req,
    ):
        # Create mock module
        mock_requests = Mock(spec=ModuleType)
        mock_requests.__name__ = "requests"

        configure(
            api_key="test-key",
            project_id="test-project",
            auto_http=True,
            instrument=[mock_requests],  # Should be ignored
        )

        # Should call instrument_http_clients, not individual
        mock_all.assert_called_once()
        mock_req.assert_not_called()
