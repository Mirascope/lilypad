"""HTTP client integration for distributed tracing.

This module provides traced HTTP clients that automatically propagate
trace context across service boundaries.
"""

from __future__ import annotations

import os
from typing import Any, Optional, Union

from .._utils.context_propagation import inject_context

# Check which HTTP clients are available
_HAS_REQUESTS = False
_HAS_HTTPX = False
_HAS_AIOHTTP = False

try:
    import requests

    _HAS_REQUESTS = True
except ImportError:
    pass

try:
    import httpx

    _HAS_HTTPX = True
except ImportError:
    pass

try:
    import aiohttp

    _HAS_AIOHTTP = True
except ImportError:
    pass


if _HAS_REQUESTS:

    class TracedRequestsSession(requests.Session):
        """A requests Session that automatically propagates trace context.

        This session class extends requests.Session to automatically inject
        OpenTelemetry trace context headers into all outgoing HTTP requests.
        This enables distributed tracing across service boundaries without
        manual header management.

        The trace context is injected based on the current active span,
        allowing traces to maintain parent-child relationships across
        different services in a distributed system.

        Example:
            Basic usage:

            ```python
            from lilypad import trace
            from lilypad.integrations.http_client import TracedRequestsSession


            @trace()
            def fetch_user_data(user_id: int) -> dict:
                with TracedRequestsSession() as session:
                    # Trace context is automatically added to request headers
                    response = session.get(f"https://api.example.com/users/{user_id}")
                    response.raise_for_status()
                    return response.json()
            ```

            Making multiple requests:

            ```python
            @trace()
            def aggregate_data(user_id: int) -> dict:
                with TracedRequestsSession() as session:
                    # All requests will include trace context
                    user = session.get(f"https://api.example.com/users/{user_id}").json()
                    orders = session.get(f"https://api.example.com/orders?user={user_id}").json()
                    profile = session.get(f"https://api.example.com/profiles/{user_id}").json()

                    return {"user": user, "orders": orders, "profile": profile}
            ```

            With custom headers and error handling:

            ```python
            @trace()
            def call_external_api(payload: dict) -> dict:
                with TracedRequestsSession() as session:
                    # Custom headers are preserved, trace headers are added
                    headers = {"Content-Type": "application/json", "X-API-Key": "secret-key"}

                    try:
                        response = session.post(
                            "https://api.example.com/process", json=payload, headers=headers, timeout=30
                        )
                        response.raise_for_status()
                        return response.json()
                    except requests.RequestException as e:
                        # Errors are captured in the trace
                        logger.error(f"API call failed: {e}")
                        raise
            ```

        Note:
            The exact headers added depend on the LILYPAD_PROPAGATOR environment variable:
            - 'traceparent' for W3C Trace Context (default)
            - 'b3' for B3 Single Header
            - 'uber-trace-id' for Jaeger
        """

        def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
            """Make an HTTP request with trace context propagation."""
            # Get or create headers
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}

            # Inject current trace context into headers
            inject_context(headers)
            kwargs["headers"] = headers

            # Make the request
            return super().request(method, url, **kwargs)

    def traced_requests_get(url: str, **kwargs: Any) -> requests.Response:
        """Make a GET request with trace context propagation.

        This is a convenience function that creates a one-off traced request.

        Args:
            url: The URL to request
            **kwargs: Additional arguments to pass to requests.get

        Returns:
            The response object
        """
        session = TracedRequestsSession()
        return session.get(url, **kwargs)

    def traced_requests_post(url: str, **kwargs: Any) -> requests.Response:
        """Make a POST request with trace context propagation."""
        session = TracedRequestsSession()
        return session.post(url, **kwargs)


if _HAS_HTTPX:

    class TracedHTTPXClient(httpx.Client):
        """An httpx Client that automatically propagates trace context.

        Example:
            ```python
            from lilypad.integrations.http_client import TracedHTTPXClient

            with TracedHTTPXClient() as client:
                # Trace context is automatically propagated
                response = client.get("http://api.example.com/data")
            ```
        """

        def request(self, method: str, url: Union[httpx.URL, str], **kwargs: Any) -> httpx.Response:
            """Make an HTTP request with trace context propagation."""
            # Get or create headers
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}

            # Inject current trace context into headers
            inject_context(headers)
            kwargs["headers"] = headers

            # Make the request
            return super().request(method, url, **kwargs)

    class TracedAsyncHTTPXClient(httpx.AsyncClient):
        """An async httpx Client that automatically propagates trace context.

        Example:
            ```python
            from lilypad.integrations.http_client import TracedAsyncHTTPXClient

            async with TracedAsyncHTTPXClient() as client:
                # Trace context is automatically propagated
                response = await client.get("http://api.example.com/data")
            ```
        """

        async def request(self, method: str, url: Union[httpx.URL, str], **kwargs: Any) -> httpx.Response:
            """Make an HTTP request with trace context propagation."""
            # Get or create headers
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}

            # Inject current trace context into headers
            inject_context(headers)
            kwargs["headers"] = headers

            # Make the request
            return await super().request(method, url, **kwargs)


if _HAS_AIOHTTP:

    class TracedAiohttpSession(aiohttp.ClientSession):
        """An aiohttp ClientSession that automatically propagates trace context.

        Example:
            ```python
            from lilypad.integrations.http_client import TracedAiohttpSession

            async with TracedAiohttpSession() as session:
                # Trace context is automatically propagated
                async with session.get("http://api.example.com/data") as resp:
                    data = await resp.json()
            ```
        """

        async def _request(
            self, method: str, str_or_url: Union[str, aiohttp.yarl.URL], **kwargs: Any
        ) -> aiohttp.ClientResponse:
            """Make an HTTP request with trace context propagation."""
            # Get or create headers
            headers = kwargs.get("headers", {})
            if headers is None:
                headers = {}

            # Inject current trace context into headers
            inject_context(headers)
            kwargs["headers"] = headers

            # Make the request
            return await super()._request(method, str_or_url, **kwargs)


# Factory function for creating traced aiohttp session
def create_traced_aiohttp_session(**kwargs: Any) -> "TracedAiohttpSession":
    """Create a new TracedAiohttpSession instance.

    Args:
        **kwargs: Arguments to pass to aiohttp.ClientSession constructor

    Returns:
        A new TracedAiohttpSession instance

    Example:
        ```python
        async def main():
            session = create_traced_aiohttp_session()
            async with session:
                async with session.get("http://api.example.com") as resp:
                    data = await resp.json()
        ```
    """
    if not _HAS_AIOHTTP:
        raise ImportError("aiohttp is not installed. Install it with: pip install aiohttp")
    return TracedAiohttpSession(**kwargs)


# Convenience function to get the appropriate client based on what's installed
def get_traced_http_client(async_client: bool = False, prefer: Optional[str] = None) -> Any:
    """Get a traced HTTP client based on available libraries.

    This function returns an appropriate HTTP client that automatically
    propagates OpenTelemetry trace context. It selects the client based
    on installed libraries and user preference.

    Args:
        async_client: Whether to return an async client (default: False).
                     If True, returns a factory function for async clients.
                     If False, returns a sync client instance.
        prefer: Preferred library ("requests", "httpx", "aiohttp").
               Can also be set via LILYPAD_HTTP_CLIENT environment variable.

    Returns:
        For sync clients: A traced HTTP client instance ready to use
        For async clients: A factory function that creates the client

    Raises:
        ImportError: If no suitable HTTP client library is installed

    Example:
        Getting a sync client:

        ```python
        from lilypad import trace
        from lilypad.integrations.http_client import get_traced_http_client


        @trace()
        def fetch_data(endpoint: str) -> dict:
            # Automatically selects available client (requests or httpx)
            client = get_traced_http_client()

            if hasattr(client, "get"):  # requests-style
                response = client.get(f"https://api.example.com/{endpoint}")
                return response.json()
            else:  # httpx-style
                with client:
                    response = client.get(f"https://api.example.com/{endpoint}")
                    return response.json()
        ```

        Getting an async client:

        ```python
        @trace()
        async def fetch_data_async(endpoint: str) -> dict:
            # Returns a factory function for async clients
            client_factory = get_traced_http_client(async_client=True)

            # Create client instance
            async with client_factory() as client:
                response = await client.get(f"https://api.example.com/{endpoint}")
                return response.json()
        ```

        With library preference:

        ```python
        # Prefer httpx even if requests is installed
        client = get_traced_http_client(prefer="httpx")

        # Or via environment variable
        # export LILYPAD_HTTP_CLIENT=httpx
        client = get_traced_http_client()
        ```

        Handling different client types:

        ```python
        @trace()
        async def universal_fetch(url: str) -> dict:
            # Get appropriate async client
            client_factory = get_traced_http_client(async_client=True, prefer="httpx")

            async with client_factory() as client:
                # Works with both httpx and aiohttp
                response = await client.get(url)

                # Handle response based on client type
                if hasattr(response, "json"):  # httpx
                    return response.json()
                else:  # aiohttp
                    return await response.json()
        ```

    Note:
        - For async clients, a factory function is returned to ensure proper
          async context management across different libraries
        - The client preference order is: prefer > env var > first available
        - All returned clients automatically inject trace context headers
    """
    preference = prefer or os.getenv("LILYPAD_HTTP_CLIENT", "").lower()

    if async_client:
        if preference == "aiohttp" and _HAS_AIOHTTP:
            return create_traced_aiohttp_session
        elif (preference == "httpx" and _HAS_HTTPX) or _HAS_HTTPX:
            return lambda **kwargs: TracedAsyncHTTPXClient(**kwargs)
        elif _HAS_AIOHTTP:
            return create_traced_aiohttp_session
        else:
            raise ImportError("No async HTTP client library found. Install httpx or aiohttp: pip install httpx aiohttp")
    else:
        # Sync clients can return instances directly
        if preference == "requests" and _HAS_REQUESTS:
            return TracedRequestsSession()
        elif preference == "httpx" and _HAS_HTTPX:
            return TracedHTTPXClient()
        elif _HAS_REQUESTS:
            return TracedRequestsSession()
        elif _HAS_HTTPX:
            return TracedHTTPXClient()
        else:
            raise ImportError("No HTTP client library found. Install requests or httpx: pip install requests httpx")
