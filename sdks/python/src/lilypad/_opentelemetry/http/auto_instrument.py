"""Automatic instrumentation for HTTP clients to enable transparent distributed tracing.

This module provides automatic instrumentation that patches HTTP client libraries
to inject trace context without requiring code changes.

Example:
    Enable automatic instrumentation:

    ```python
    # At the start of your application
    import lilypad

    # Enable automatic trace propagation for all HTTP calls
    lilypad.instrument_http_clients()

    # Now all HTTP calls will automatically propagate trace context
    import requests


    @trace()
    def my_function():
        # This request automatically includes trace headers!
        response = requests.get("https://api.example.com/data")
        return response.json()
    ```
"""

from __future__ import annotations

from contextlib import suppress

import functools
from typing import Any

from ..._utils.context_propagation import inject_context

# Track if we've already instrumented to avoid double-patching
_INSTRUMENTED = False

# Store original methods for restoration
_ORIGINAL_METHODS: dict[str, Any] = {}


def _patch_requests() -> None:
    """Patch the requests library to automatically inject trace context."""
    with suppress(ImportError):
        import requests
        from requests import Session

        # Check if already patched
        if "requests.Session.request" in _ORIGINAL_METHODS:
            return

        # Store original method
        _original_request = Session.request
        _ORIGINAL_METHODS["requests.Session.request"] = _original_request

        @functools.wraps(_original_request)
        def _traced_request(self: Session, method: str, url: str, **kwargs: Any) -> requests.Response:
            # Get or create headers
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}

            # Inject trace context
            inject_context(headers)
            kwargs["headers"] = headers

            # Call original method
            return _original_request(self, method, url, **kwargs)

        # Patch the method
        Session.request = _traced_request


def _patch_httpx() -> None:
    """Patch the httpx library to automatically inject trace context."""
    with suppress(ImportError):
        import httpx

        # Check if already patched
        if "httpx.Client.request" in _ORIGINAL_METHODS:
            return

        # Patch sync client
        _original_request = httpx.Client.request
        _ORIGINAL_METHODS["httpx.Client.request"] = _original_request

        @functools.wraps(_original_request)
        def _traced_request(self: httpx.Client, method: str, url: Any, **kwargs: Any) -> httpx.Response:
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}
            inject_context(headers)
            kwargs["headers"] = headers
            return _original_request(self, method, url, **kwargs)

        httpx.Client.request = _traced_request

        # Patch async client
        _original_async_request = httpx.AsyncClient.request
        _ORIGINAL_METHODS["httpx.AsyncClient.request"] = _original_async_request

        @functools.wraps(_original_async_request)
        async def _traced_async_request(
            self: httpx.AsyncClient, method: str, url: Any, **kwargs: Any
        ) -> httpx.Response:
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}
            inject_context(headers)
            kwargs["headers"] = headers
            return await _original_async_request(self, method, url, **kwargs)

        httpx.AsyncClient.request = _traced_async_request


def _patch_aiohttp() -> None:
    """Patch the aiohttp library to automatically inject trace context."""
    with suppress(ImportError):
        import aiohttp

        # Check if already patched
        if "aiohttp.ClientSession._request" in _ORIGINAL_METHODS:
            return

        _original_request = aiohttp.ClientSession._request
        _ORIGINAL_METHODS["aiohttp.ClientSession._request"] = _original_request

        @functools.wraps(_original_request)
        async def _traced_request(
            self: aiohttp.ClientSession, method: str, str_or_url: Any, **kwargs: Any
        ) -> aiohttp.ClientResponse:
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}
            inject_context(headers)
            kwargs["headers"] = headers
            return await _original_request(self, method, str_or_url, **kwargs)

        aiohttp.ClientSession._request = _traced_request


def _patch_urllib3() -> None:
    """Patch urllib3 to automatically inject trace context."""
    with suppress(ImportError):
        import urllib3

        # Check if already patched
        if "urllib3.HTTPConnectionPool.urlopen" in _ORIGINAL_METHODS:
            return

        _original_urlopen = urllib3.HTTPConnectionPool.urlopen
        _ORIGINAL_METHODS["urllib3.HTTPConnectionPool.urlopen"] = _original_urlopen

        @functools.wraps(_original_urlopen)
        def _traced_urlopen(self: urllib3.HTTPConnectionPool, method: str, url: str, **kwargs: Any) -> Any:
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}
            inject_context(headers)
            kwargs["headers"] = headers
            return _original_urlopen(self, method, url, **kwargs)

        urllib3.HTTPConnectionPool.urlopen = _traced_urlopen


def instrument_http_clients() -> None:
    """Automatically instrument all available HTTP client libraries.

    This function patches common HTTP client libraries to automatically
    inject OpenTelemetry trace context into all outgoing requests.
    This enables transparent distributed tracing without code changes.

    Supported libraries:
    - requests
    - httpx (sync and async)
    - aiohttp
    - urllib3

    Example:
        Basic usage:

        ```python
        # Enable at application startup
        import lilypad

        lilypad.instrument_http_clients()

        # Now use HTTP clients normally
        import requests
        from lilypad import trace


        @trace()
        def fetch_data():
            # Trace context is automatically added!
            response = requests.get("https://api.example.com/data")
            return response.json()
        ```

        With RPC clients:

        ```python
        # Enable instrumentation
        instrument_http_clients()

        # Your RPC client that uses requests/httpx internally
        from my_api import Client


        @trace()
        def call_remote_service():
            client = Client("https://api.example.com")
            # The underlying HTTP calls will include trace context
            result = client.remote_function("param1", "param2")
            return result
        ```

        Complete distributed system example:

        ```python
        # Service A
        instrument_http_clients()


        @trace()
        def process_request(data):
            # Call Service B - trace context propagated automatically
            response = requests.post("http://service-b/process", json=data)
            return response.json()


        # Service B
        instrument_http_clients()


        @app.route("/process", methods=["POST"])
        def handle_process():
            # Extract trace context from headers
            @trace(extract_from=request.headers)
            def process(data):
                # This span is a child of Service A's span
                return {"processed": True, "data": data}

            return process(request.json)
        ```

    Note:
        - Call this function once at application startup
        - It will only patch libraries that are already imported
        - Safe to call multiple times (idempotent)
        - Works with any HTTP-based RPC library
    """
    global _INSTRUMENTED

    if _INSTRUMENTED:
        return

    _patch_requests()
    _patch_httpx()
    _patch_aiohttp()
    _patch_urllib3()

    _INSTRUMENTED = True


def instrument_requests() -> None:
    """Instrument only the requests library.

    Example:
        ```python
        import lilypad

        lilypad.instrument_requests()
        ```
    """
    _patch_requests()


def instrument_httpx() -> None:
    """Instrument only the httpx library (both sync and async).

    Example:
        ```python
        import lilypad

        lilypad.instrument_httpx()
        ```
    """
    _patch_httpx()


def instrument_aiohttp() -> None:
    """Instrument only the aiohttp library.

    Example:
        ```python
        import lilypad

        lilypad.instrument_aiohttp()
        ```
    """
    _patch_aiohttp()


def instrument_urllib3() -> None:
    """Instrument only the urllib3 library.

    Example:
        ```python
        import lilypad

        lilypad.instrument_urllib3()
        ```
    """
    _patch_urllib3()


def uninstrument_requests() -> None:
    """Remove instrumentation from the requests library.

    Example:
        ```python
        import lilypad

        # Remove requests instrumentation
        lilypad.uninstrument_requests()
        ```
    """
    with suppress(ImportError, KeyError):
        from requests import Session

        if "requests.Session.request" in _ORIGINAL_METHODS:
            Session.request = _ORIGINAL_METHODS.pop("requests.Session.request")


def uninstrument_httpx() -> None:
    """Remove instrumentation from the httpx library (both sync and async).

    Example:
        ```python
        import lilypad

        # Remove httpx instrumentation
        lilypad.uninstrument_httpx()
        ```
    """
    with suppress(ImportError, KeyError):
        import httpx

        if "httpx.Client.request" in _ORIGINAL_METHODS:
            httpx.Client.request = _ORIGINAL_METHODS.pop("httpx.Client.request")

        if "httpx.AsyncClient.request" in _ORIGINAL_METHODS:
            httpx.AsyncClient.request = _ORIGINAL_METHODS.pop("httpx.AsyncClient.request")


def uninstrument_aiohttp() -> None:
    """Remove instrumentation from the aiohttp library.

    Example:
        ```python
        import lilypad

        # Remove aiohttp instrumentation
        lilypad.uninstrument_aiohttp()
        ```
    """
    with suppress(ImportError, KeyError):
        import aiohttp

        if "aiohttp.ClientSession._request" in _ORIGINAL_METHODS:
            aiohttp.ClientSession._request = _ORIGINAL_METHODS.pop("aiohttp.ClientSession._request")


def uninstrument_urllib3() -> None:
    """Remove instrumentation from the urllib3 library.

    Example:
        ```python
        import lilypad

        # Remove urllib3 instrumentation
        lilypad.uninstrument_urllib3()
        ```
    """
    with suppress(ImportError, KeyError):
        import urllib3

        if "urllib3.HTTPConnectionPool.urlopen" in _ORIGINAL_METHODS:
            urllib3.HTTPConnectionPool.urlopen = _ORIGINAL_METHODS.pop("urllib3.HTTPConnectionPool.urlopen")


def uninstrument_http_clients() -> None:
    """Remove instrumentation from all HTTP client libraries.

    This function removes the automatic trace context injection from all
    previously instrumented HTTP client libraries, restoring their original
    behavior.

    Example:
        ```python
        import lilypad

        # Remove all HTTP client instrumentation
        lilypad.uninstrument_http_clients()
        ```

    Note:
        This will only remove instrumentation from libraries that were
        previously instrumented. It's safe to call even if no libraries
        were instrumented.
    """
    global _INSTRUMENTED

    uninstrument_requests()
    uninstrument_httpx()
    uninstrument_aiohttp()
    uninstrument_urllib3()

    _INSTRUMENTED = False
