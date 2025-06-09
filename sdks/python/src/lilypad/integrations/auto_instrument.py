"""Automatic instrumentation for HTTP clients to enable transparent distributed tracing.

This module provides automatic instrumentation that patches HTTP client libraries
to inject trace context without requiring code changes.

Example:
    Enable automatic instrumentation:
    
    ```python
    # At the start of your application
    from lilypad.integrations.auto_instrument import instrument_http_clients
    
    # Enable automatic trace propagation for all HTTP calls
    instrument_http_clients()
    
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

import functools
import sys
from typing import Any, Callable

from .._utils.context_propagation import inject_context

# Track if we've already instrumented to avoid double-patching
_INSTRUMENTED = False


def _patch_requests() -> None:
    """Patch the requests library to automatically inject trace context."""
    try:
        import requests
        from requests import Session
        
        # Store original methods
        _original_request = Session.request
        
        @functools.wraps(_original_request)
        def _traced_request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
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
        
    except ImportError:
        pass  # requests not installed


def _patch_httpx() -> None:
    """Patch the httpx library to automatically inject trace context."""
    try:
        import httpx
        
        # Patch sync client
        _original_request = httpx.Client.request
        
        @functools.wraps(_original_request)
        def _traced_request(self, method: str, url: Any, **kwargs: Any) -> httpx.Response:
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}
            inject_context(headers)
            kwargs["headers"] = headers
            return _original_request(self, method, url, **kwargs)
        
        httpx.Client.request = _traced_request
        
        # Patch async client
        _original_async_request = httpx.AsyncClient.request
        
        @functools.wraps(_original_async_request)
        async def _traced_async_request(self, method: str, url: Any, **kwargs: Any) -> httpx.Response:
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}
            inject_context(headers)
            kwargs["headers"] = headers
            return await _original_async_request(self, method, url, **kwargs)
        
        httpx.AsyncClient.request = _traced_async_request
        
    except ImportError:
        pass  # httpx not installed


def _patch_aiohttp() -> None:
    """Patch the aiohttp library to automatically inject trace context."""
    try:
        import aiohttp
        
        _original_request = aiohttp.ClientSession._request
        
        @functools.wraps(_original_request)
        async def _traced_request(self, method: str, str_or_url: Any, **kwargs: Any) -> aiohttp.ClientResponse:
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}
            inject_context(headers)
            kwargs["headers"] = headers
            return await _original_request(self, method, str_or_url, **kwargs)
        
        aiohttp.ClientSession._request = _traced_request
        
    except ImportError:
        pass  # aiohttp not installed


def _patch_urllib3() -> None:
    """Patch urllib3 to automatically inject trace context."""
    try:
        import urllib3
        
        _original_urlopen = urllib3.HTTPConnectionPool.urlopen
        
        @functools.wraps(_original_urlopen)
        def _traced_urlopen(self, method: str, url: str, **kwargs: Any) -> Any:
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}
            inject_context(headers)
            kwargs["headers"] = headers
            return _original_urlopen(self, method, url, **kwargs)
        
        urllib3.HTTPConnectionPool.urlopen = _traced_urlopen
        
    except ImportError:
        pass  # urllib3 not installed


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
        from lilypad.integrations.auto_instrument import instrument_http_clients
        instrument_http_clients()
        
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


def uninstrument_http_clients() -> None:
    """Remove HTTP client instrumentation (for testing purposes)."""
    global _INSTRUMENTED
    # Note: This is a simplified version. In production, you'd want to
    # restore the original methods properly.
    _INSTRUMENTED = False