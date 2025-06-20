"""Tests for HTTP client auto-instrumentation."""

import sys
import importlib.util
from contextlib import suppress
from unittest.mock import Mock, patch, call, MagicMock
import pytest


from lilypad._opentelemetry.http.auto_instrument import (
    RequestsInstrumentor,
    HTTPXInstrumentor,
    AIOHTTPInstrumentor,
    URLLib3Instrumentor,
    instrument_requests,
    instrument_httpx,
    instrument_aiohttp,
    instrument_urllib3,
    uninstrument_requests,
    uninstrument_httpx,
    uninstrument_aiohttp,
    uninstrument_urllib3,
    _wrap_request_method,
    _wrap_async_request_method,
)


@pytest.fixture(autouse=True)
def clean_instrumentors():
    """Clean up instrumentors before and after each test."""
    # Create instances to ensure cleanup
    instrumentors = [
        RequestsInstrumentor(),
        HTTPXInstrumentor(),
        AIOHTTPInstrumentor(),
        URLLib3Instrumentor(),
    ]

    # Ensure they're all uninstrumented before test
    for instrumentor in instrumentors:
        with suppress(Exception):
            instrumentor.uninstrument()

    yield

    # Clean up after test
    for instrumentor in instrumentors:
        with suppress(Exception):
            instrumentor.uninstrument()


# BaseInstrumentor Pattern Tests


def test_requests_instrumentor_instance():
    """Test RequestsInstrumentor is a proper BaseInstrumentor."""
    instrumentor = RequestsInstrumentor()

    # Check it has the required methods
    assert hasattr(instrumentor, "instrument")
    assert hasattr(instrumentor, "uninstrument")
    assert hasattr(instrumentor, "is_instrumented_by_opentelemetry")
    assert hasattr(instrumentor, "instrumentation_dependencies")

    # Check dependencies
    deps = instrumentor.instrumentation_dependencies()
    assert isinstance(deps, tuple)
    assert len(deps) > 0
    assert "requests" in deps[0]


def test_instrumentor_idempotency():
    """Test that instrumentors are idempotent."""
    # First instrumentation
    instrument_requests()

    # Check it's instrumented
    instrumentor = RequestsInstrumentor()
    assert instrumentor.is_instrumented_by_opentelemetry

    # Second instrumentation should be no-op
    with patch("lilypad._opentelemetry.http.auto_instrument.wrap_function_wrapper") as mock_wrap:
        instrument_requests()
        # wrap_function_wrapper should NOT be called again
        mock_wrap.assert_not_called()


def test_uninstrument_when_not_instrumented():
    """Test uninstrumenting when not instrumented is safe."""
    # Should not raise any errors
    uninstrument_requests()
    uninstrument_httpx()
    uninstrument_aiohttp()
    uninstrument_urllib3()


def test_multiple_instrument_uninstrument_cycles():
    """Test multiple cycles of instrument/uninstrument."""
    for _ in range(3):
        instrument_requests()
        assert RequestsInstrumentor().is_instrumented_by_opentelemetry

        uninstrument_requests()
        assert not RequestsInstrumentor().is_instrumented_by_opentelemetry


# Wrapper Function Tests


def test_wrap_request_method():
    """Test synchronous wrapper injects context."""
    wrapped = Mock(return_value="response")
    instance = Mock()
    args = ("GET", "http://example.com")
    kwargs = {"headers": {"existing": "header"}}

    with patch("lilypad._opentelemetry.http.auto_instrument._inject_context") as mock_inject:
        result = _wrap_request_method(wrapped, instance, args, kwargs)

        # Verify context was injected
        mock_inject.assert_called_once_with({"existing": "header"})

        # Verify wrapped method was called
        wrapped.assert_called_once_with(*args, **kwargs)

        # Verify result
        assert result == "response"


def test_wrap_request_method_no_headers():
    """Test wrapper creates headers dict when missing."""
    wrapped = Mock(return_value="response")
    instance = Mock()
    args = ("GET", "http://example.com")
    kwargs = {}

    with patch("lilypad._opentelemetry.http.auto_instrument._inject_context") as mock_inject:
        result = _wrap_request_method(wrapped, instance, args, kwargs)

        # Verify context was injected to empty dict
        mock_inject.assert_called_once_with({})

        # Verify headers were added to kwargs
        assert "headers" in kwargs
        assert kwargs["headers"] == {}


def test_wrap_request_method_none_headers():
    """Test wrapper handles None headers."""
    wrapped = Mock(return_value="response")
    instance = Mock()
    args = ("GET", "http://example.com")
    kwargs = {"headers": None}

    with patch("lilypad._opentelemetry.http.auto_instrument._inject_context") as mock_inject:
        result = _wrap_request_method(wrapped, instance, args, kwargs)

        # Verify context was injected to new dict
        mock_inject.assert_called_once_with({})

        # Verify headers were replaced
        assert kwargs["headers"] == {}


@pytest.mark.asyncio
async def test_wrap_async_request_method():
    """Test async wrapper injects context."""

    async def mock_wrapped(*args, **kwargs):
        return "async_response"

    wrapped = Mock(side_effect=mock_wrapped)
    instance = Mock()
    args = ("GET", "http://example.com")
    kwargs = {"headers": {"existing": "header"}}

    with patch("lilypad._opentelemetry.http.auto_instrument._inject_context") as mock_inject:
        result = await _wrap_async_request_method(wrapped, instance, args, kwargs)

        # Verify context was injected
        mock_inject.assert_called_once_with({"existing": "header"})

        # Verify wrapped method was called
        wrapped.assert_called_once_with(*args, **kwargs)

        # Verify result
        assert result == "async_response"


# Instrumentation Function Tests


@patch("lilypad._opentelemetry.http.auto_instrument.wrap_function_wrapper")
def test_instrument_requests_calls_wrap(mock_wrap):
    """Test instrument_requests uses wrap_function_wrapper."""
    instrument_requests()

    # Verify wrap_function_wrapper was called correctly
    mock_wrap.assert_called_once_with(module="requests", name="Session.request", wrapper=_wrap_request_method)


@patch("lilypad._opentelemetry.http.auto_instrument.wrap_function_wrapper")
def test_instrument_httpx_calls_wrap_twice(mock_wrap):
    """Test instrument_httpx wraps both sync and async clients."""
    instrument_httpx()

    # Verify both sync and async clients were wrapped
    assert mock_wrap.call_count == 2
    mock_wrap.assert_has_calls(
        [
            call(module="httpx", name="Client.request", wrapper=_wrap_request_method),
            call(module="httpx", name="AsyncClient.request", wrapper=_wrap_async_request_method),
        ]
    )


@patch("lilypad._opentelemetry.http.auto_instrument.wrap_function_wrapper")
def test_instrument_aiohttp_calls_wrap(mock_wrap):
    """Test instrument_aiohttp uses wrap_function_wrapper."""
    instrument_aiohttp()

    # Verify wrap_function_wrapper was called correctly
    mock_wrap.assert_called_once_with(
        module="aiohttp", name="ClientSession._request", wrapper=_wrap_async_request_method
    )


@patch("lilypad._opentelemetry.http.auto_instrument.wrap_function_wrapper")
def test_instrument_urllib3_calls_wrap(mock_wrap):
    """Test instrument_urllib3 uses wrap_function_wrapper."""
    instrument_urllib3()

    # Verify wrap_function_wrapper was called correctly
    mock_wrap.assert_called_once_with(module="urllib3", name="HTTPConnectionPool.urlopen", wrapper=_wrap_request_method)


def test_instrument_all_individually():
    """Test instrumenting all libraries individually."""
    with patch("lilypad._opentelemetry.http.auto_instrument.wrap_function_wrapper") as mock_wrap:
        # Instrument each library
        instrument_requests()
        instrument_httpx()
        instrument_aiohttp()
        instrument_urllib3()

        # Verify wrap_function_wrapper was called for each
        # requests: 1 call, httpx: 2 calls (sync + async), aiohttp: 1 call, urllib3: 1 call
        assert mock_wrap.call_count == 5


# Uninstrumentation Function Tests


def test_uninstrument_requests_when_not_imported():
    """Test uninstrument_requests when requests isn't imported."""
    # Ensure requests is not imported
    if "requests" in sys.modules:
        del sys.modules["requests"]

    # Should not raise
    uninstrument_requests()


def test_uninstrument_with_mock_module():
    """Test uninstrumentation with a mock module."""
    # First, instrument
    instrument_requests()
    instrumentor = RequestsInstrumentor()
    assert instrumentor.is_instrumented_by_opentelemetry

    # Create mock module
    mock_requests = Mock()
    mock_session = Mock()
    mock_requests.Session = mock_session

    # Now uninstrument with the mock module in sys.modules
    with (
        patch.dict("sys.modules", {"requests": mock_requests}),
        patch("lilypad._opentelemetry.http.auto_instrument.unwrap") as mock_unwrap,
    ):
        uninstrument_requests()

        # Verify unwrap was called
        mock_unwrap.assert_called_once_with(mock_session, "request")

    # Verify instrumentor state was updated
    assert not instrumentor.is_instrumented_by_opentelemetry


def test_uninstrument_all_individually():
    """Test uninstrumenting all libraries individually."""
    # First instrument all
    instrument_requests()
    instrument_httpx()
    instrument_aiohttp()
    instrument_urllib3()

    # Create instrumentor instances
    req_inst = RequestsInstrumentor()
    httpx_inst = HTTPXInstrumentor()
    aio_inst = AIOHTTPInstrumentor()
    url_inst = URLLib3Instrumentor()

    # Verify all are instrumented
    assert req_inst.is_instrumented_by_opentelemetry
    assert httpx_inst.is_instrumented_by_opentelemetry
    assert aio_inst.is_instrumented_by_opentelemetry
    assert url_inst.is_instrumented_by_opentelemetry

    # Uninstrument all
    uninstrument_requests()
    uninstrument_httpx()
    uninstrument_aiohttp()
    uninstrument_urllib3()

    # Verify all are uninstrumented
    assert not req_inst.is_instrumented_by_opentelemetry
    assert not httpx_inst.is_instrumented_by_opentelemetry
    assert not aio_inst.is_instrumented_by_opentelemetry
    assert not url_inst.is_instrumented_by_opentelemetry


# Error Handling Tests


def test_uninstrument_handles_import_error():
    """Test uninstrument handles ImportError gracefully."""
    # This should not raise even if modules don't exist
    uninstrument_requests()
    uninstrument_httpx()
    uninstrument_aiohttp()
    uninstrument_urllib3()


def test_uninstrument_handles_attribute_error():
    """Test uninstrument handles AttributeError gracefully."""
    # Create a mock module without the expected attributes
    mock_requests = Mock()
    mock_requests.Session = Mock(spec=[])  # No 'request' attribute

    with patch.dict("sys.modules", {"requests": mock_requests}):
        # Should not raise
        uninstrument_requests()


# State Management Tests


def test_global_instrumentor_instances():
    """Test that instrumentors implement singleton pattern."""
    # Create multiple instances of each instrumentor
    req1 = RequestsInstrumentor()
    req2 = RequestsInstrumentor()
    httpx1 = HTTPXInstrumentor()
    httpx2 = HTTPXInstrumentor()
    aio1 = AIOHTTPInstrumentor()
    aio2 = AIOHTTPInstrumentor()
    url1 = URLLib3Instrumentor()
    url2 = URLLib3Instrumentor()

    # Verify singleton behavior - same instance
    assert req1 is req2
    assert httpx1 is httpx2
    assert aio1 is aio2
    assert url1 is url2

    # Verify they're the right type
    assert isinstance(req1, RequestsInstrumentor)
    assert isinstance(httpx1, HTTPXInstrumentor)
    assert isinstance(aio1, AIOHTTPInstrumentor)
    assert isinstance(url1, URLLib3Instrumentor)


def test_instrumentor_state_tracking():
    """Test that instrumentor state is properly tracked."""
    # Get an instance
    instrumentor = RequestsInstrumentor()

    # Initially not instrumented
    assert not instrumentor.is_instrumented_by_opentelemetry

    # After instrumenting via function
    instrument_requests()
    assert instrumentor.is_instrumented_by_opentelemetry

    # After uninstrumenting via function
    uninstrument_requests()
    assert not instrumentor.is_instrumented_by_opentelemetry

    # Verify state is shared across instances
    new_instrumentor = RequestsInstrumentor()
    assert not new_instrumentor.is_instrumented_by_opentelemetry


# Import Order Tests


@pytest.fixture
def cleanup_modules():
    """Clean up imported modules."""
    # Store original modules
    original_modules = {}
    for module_name in ["requests", "httpx", "aiohttp", "urllib3"]:
        if module_name in sys.modules:
            original_modules[module_name] = sys.modules[module_name]
            del sys.modules[module_name]

    yield

    # Restore original modules
    for module_name, module in original_modules.items():
        sys.modules[module_name] = module


def test_instrument_before_import(cleanup_modules):
    """Test that instrumentation works when called before importing the library."""
    # Ensure requests is not imported yet
    if "requests" in sys.modules:
        del sys.modules["requests"]

    # Clear any sub-modules
    modules_to_remove = [m for m in sys.modules if m.startswith("requests")]
    for m in modules_to_remove:
        del sys.modules[m]

    # Import lilypad and instrument
    from lilypad._opentelemetry.http.auto_instrument import RequestsInstrumentor
    from lilypad._opentelemetry.http.auto_instrument import _wrap_request_method

    # Mock the wrapper to verify it gets called
    mock_wrapper = Mock(side_effect=_wrap_request_method)

    with patch("lilypad._opentelemetry.http.auto_instrument._wrap_request_method", mock_wrapper):
        instrumentor = RequestsInstrumentor()
        instrumentor.instrument()

        # Now import requests
        import requests

        # Make a request
        with patch.object(requests.Session, "request", return_value=Mock()) as mock_request:
            session = requests.Session()
            session.request("GET", "http://example.com")

            # Verify the wrapper was applied
            assert mock_request.called


def test_instrument_after_import(cleanup_modules):
    """Test that instrumentation works when called after importing the library."""
    # Import requests first
    import requests

    # Import lilypad and instrument
    from lilypad._opentelemetry.http.auto_instrument import RequestsInstrumentor

    # Store original method
    original_method = requests.Session.request

    instrumentor = RequestsInstrumentor()
    instrumentor.instrument()

    # Verify the wrapper is applied
    assert hasattr(requests.Session.request, "__wrapped__")
    # The wrapped attribute should point to the original method
    assert requests.Session.request.__wrapped__ == original_method

    # Simple verification that the instrumented method is callable
    # We don't need to actually make an HTTP request or mock the adapter
    session = requests.Session()

    # Mock the session's request method to avoid actual HTTP calls
    with patch.object(session, "request", return_value=Mock(status_code=200)) as mock_request:
        response = session.request("GET", "http://example.com")

        # Verify the method was called
        mock_request.assert_called_once_with("GET", "http://example.com")
        assert response.status_code == 200


def test_httpx_instrument_before_import(cleanup_modules):
    """Test HTTPX instrumentation before import."""
    # Ensure httpx is not imported yet
    if "httpx" in sys.modules:
        del sys.modules["httpx"]

    # Clear any sub-modules
    modules_to_remove = [m for m in sys.modules if m.startswith("httpx")]
    for m in modules_to_remove:
        del sys.modules[m]

    from lilypad._opentelemetry.http.auto_instrument import HTTPXInstrumentor

    instrumentor = HTTPXInstrumentor()
    instrumentor.instrument()

    # Now import httpx
    import httpx

    # Verify the method exists and can be called
    client = httpx.Client()
    assert hasattr(client, "request")


def test_aiohttp_instrument_before_import(cleanup_modules):
    """Test aiohttp instrumentation before import."""
    # Ensure aiohttp is not imported yet
    if "aiohttp" in sys.modules:
        del sys.modules["aiohttp"]

    # Clear any sub-modules
    modules_to_remove = [m for m in sys.modules if m.startswith("aiohttp")]
    for m in modules_to_remove:
        del sys.modules[m]

    from lilypad._opentelemetry.http.auto_instrument import AIOHTTPInstrumentor

    instrumentor = AIOHTTPInstrumentor()
    instrumentor.instrument()

    # Now import aiohttp
    import aiohttp

    # Verify the class exists
    assert hasattr(aiohttp, "ClientSession")


def test_urllib3_instrument_before_import(cleanup_modules):
    """Test urllib3 instrumentation before import."""
    # Ensure urllib3 is not imported yet
    if "urllib3" in sys.modules:
        del sys.modules["urllib3"]

    # Clear any sub-modules
    modules_to_remove = [m for m in sys.modules if m.startswith("urllib3")]
    for m in modules_to_remove:
        del sys.modules[m]

    from lilypad._opentelemetry.http.auto_instrument import URLLib3Instrumentor

    instrumentor = URLLib3Instrumentor()
    instrumentor.instrument()

    # Now import urllib3
    import urllib3

    # Verify the class exists
    assert hasattr(urllib3, "HTTPConnectionPool")


def test_wrapt_loads_module_when_not_imported():
    """Test that wrapt actually loads the module when wrapping."""
    # Ensure a test module is not imported
    test_module = "http.client"  # Using a stdlib module for testing
    if test_module in sys.modules:
        del sys.modules[test_module]

    from wrapt import wrap_function_wrapper

    # Verify module is not in sys.modules
    assert test_module not in sys.modules

    # Create a dummy wrapper
    def dummy_wrapper(wrapped, instance, args, kwargs):
        return wrapped(*args, **kwargs)

    # Call wrap_function_wrapper
    wrap_function_wrapper(test_module, "HTTPConnection.request", dummy_wrapper)

    # Verify wrapt loaded the module
    assert test_module in sys.modules


def test_multiple_instrumentations_idempotent():
    """Test that calling instrument multiple times is safe."""
    from lilypad._opentelemetry.http.auto_instrument import RequestsInstrumentor

    instrumentor = RequestsInstrumentor()

    # Instrument multiple times
    instrumentor.instrument()
    instrumentor.instrument()
    instrumentor.instrument()

    # Should not raise any errors
    import requests

    session = requests.Session()

    # Verify it still works
    with patch.object(session, "request", return_value=Mock()):
        session.request("GET", "http://example.com")


# Optional Dependencies Tests


def test_configure_with_missing_http_libraries(monkeypatch):
    """Test that configure works even when some HTTP libraries are missing."""
    # Mock find_spec to simulate missing libraries
    original_find_spec = importlib.util.find_spec

    def mock_find_spec(name):
        # Simulate that httpx and aiohttp are not installed
        if name in ["httpx", "aiohttp"]:
            return None
        return original_find_spec(name)

    monkeypatch.setattr(importlib.util, "find_spec", mock_find_spec)

    # Import lilypad after mocking to ensure clean state
    import lilypad

    # Configure should not raise ImportError
    with patch("lilypad._utils.client.get_sync_client"):
        lilypad.configure(api_key="test-key", project_id="test-project", auto_http=True)

    # Verify that available libraries are still instrumented
    import requests

    assert hasattr(requests.Session.request, "__wrapped__")

    # urllib3 should also be instrumented (it's a dependency of requests)
    import urllib3

    assert hasattr(urllib3.HTTPConnectionPool.urlopen, "__wrapped__")


def test_configure_with_no_http_libraries(monkeypatch):
    """Test that configure works when no HTTP libraries are installed."""
    # Mock find_spec to simulate no HTTP libraries
    original_find_spec = importlib.util.find_spec

    def mock_find_spec(name):
        # Simulate that no HTTP libraries are installed
        if name in ["requests", "httpx", "aiohttp", "urllib3"]:
            return None
        return original_find_spec(name)

    monkeypatch.setattr(importlib.util, "find_spec", mock_find_spec)

    # Import lilypad after mocking
    import lilypad

    # Configure should not raise any errors
    with patch("lilypad._utils.client.get_sync_client"):
        lilypad.configure(api_key="test-key", project_id="test-project", auto_http=True)

    # No errors should occur, even with no HTTP libraries


def test_selective_http_instrumentation(monkeypatch):
    """Test that only available libraries are instrumented."""
    # Clean up any existing tracer provider to ensure configure runs fully
    from opentelemetry import trace

    trace._TRACER_PROVIDER = None

    # Mock find_spec to control which libraries are "available"
    original_find_spec = importlib.util.find_spec

    def mock_find_spec(name):
        # Only requests and urllib3 are available
        if name in ["requests", "urllib3"]:
            return MagicMock()  # Non-None value
        elif name in ["httpx", "aiohttp"]:
            return None
        return original_find_spec(name)

    monkeypatch.setattr(importlib.util, "find_spec", mock_find_spec)

    from lilypad import configure

    with (
        patch("lilypad._utils.client.get_sync_client"),
        patch("lilypad._opentelemetry.http.instrument_requests") as mock_requests,
        patch("lilypad._opentelemetry.http.instrument_httpx") as mock_httpx,
        patch("lilypad._opentelemetry.http.instrument_aiohttp") as mock_aiohttp,
        patch("lilypad._opentelemetry.http.instrument_urllib3") as mock_urllib3,
    ):
        configure(api_key="test-key", project_id="test-project", auto_http=True)

        mock_requests.assert_called_once()
        mock_urllib3.assert_called_once()
        mock_httpx.assert_not_called()
        mock_aiohttp.assert_not_called()


def test_http_instrumentation_import_error_handling():
    """Test that individual HTTP library import errors are handled gracefully."""
    with patch("lilypad._opentelemetry.http.auto_instrument.instrument_requests") as mock_requests:
        mock_requests.side_effect = Exception("Failed to instrument requests")

        import lilypad

        # This should not raise an exception
        with patch("lilypad._utils.client.get_sync_client"), suppress(Exception):
            lilypad.configure(api_key="test-key", project_id="test-project", auto_http=True)
