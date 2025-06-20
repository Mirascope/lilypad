"""HTTP client instrumentation using OpenTelemetry standard pattern."""

from __future__ import annotations

from contextlib import suppress

from typing import Any, Callable
from collections.abc import Collection

from wrapt import wrap_function_wrapper
from opentelemetry.instrumentation.utils import unwrap
from opentelemetry.instrumentation.instrumentor import BaseInstrumentor

from ..._utils.context_propagation import _inject_context


def _wrap_request_method(
    wrapped: Callable[..., Any], instance: Any, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> Any:
    """Wrapper for HTTP request methods to inject trace context."""
    # Get or create headers
    headers = kwargs.get("headers", {})
    if headers is None:
        headers = {}

    # Inject trace context
    _inject_context(headers)
    kwargs["headers"] = headers

    # Call original method
    return wrapped(*args, **kwargs)


async def _wrap_async_request_method(
    wrapped: Callable[..., Any], instance: Any, args: tuple[Any, ...], kwargs: dict[str, Any]
) -> Any:
    """Async wrapper for HTTP request methods to inject trace context."""
    # Get or create headers
    headers = kwargs.get("headers", {})
    if headers is None:
        headers = {}

    # Inject trace context
    _inject_context(headers)
    kwargs["headers"] = headers

    # Call original method
    return await wrapped(*args, **kwargs)


class RequestsInstrumentor(BaseInstrumentor):
    """Instrumentor for requests library."""

    def instrumentation_dependencies(self) -> Collection[str]:
        return ("requests>=2.0",)

    def _instrument(self, **kwargs: Any) -> None:
        """Enable requests instrumentation."""
        wrap_function_wrapper(module="requests", name="Session.request", wrapper=_wrap_request_method)

    def _uninstrument(self, **kwargs: Any) -> None:
        """Disable requests instrumentation."""
        with suppress(ImportError, AttributeError):
            import requests

            unwrap(requests.Session, "request")


class HTTPXInstrumentor(BaseInstrumentor):
    """Instrumentor for httpx library."""

    def instrumentation_dependencies(self) -> Collection[str]:
        return ("httpx>=0.23.0",)

    def _instrument(self, **kwargs: Any) -> None:
        """Enable httpx instrumentation."""
        # Sync client
        wrap_function_wrapper(module="httpx", name="Client.request", wrapper=_wrap_request_method)

        # Async client
        wrap_function_wrapper(module="httpx", name="AsyncClient.request", wrapper=_wrap_async_request_method)

    def _uninstrument(self, **kwargs: Any) -> None:
        """Disable httpx instrumentation."""
        with suppress(ImportError, AttributeError):
            import httpx

            unwrap(httpx.Client, "request")
            unwrap(httpx.AsyncClient, "request")


class AIOHTTPInstrumentor(BaseInstrumentor):
    """Instrumentor for aiohttp library."""

    def instrumentation_dependencies(self) -> Collection[str]:
        return ("aiohttp>=3.0",)

    def _instrument(self, **kwargs: Any) -> None:
        """Enable aiohttp instrumentation."""
        wrap_function_wrapper(module="aiohttp", name="ClientSession._request", wrapper=_wrap_async_request_method)

    def _uninstrument(self, **kwargs: Any) -> None:
        """Disable aiohttp instrumentation."""
        with suppress(ImportError, AttributeError):
            import aiohttp

            unwrap(aiohttp.ClientSession, "_request")


class URLLib3Instrumentor(BaseInstrumentor):
    """Instrumentor for urllib3 library."""

    def instrumentation_dependencies(self) -> Collection[str]:
        return ("urllib3>=1.0",)

    def _instrument(self, **kwargs: Any) -> None:
        """Enable urllib3 instrumentation."""
        wrap_function_wrapper(module="urllib3", name="HTTPConnectionPool.urlopen", wrapper=_wrap_request_method)

    def _uninstrument(self, **kwargs: Any) -> None:
        """Disable urllib3 instrumentation."""
        with suppress(ImportError, AttributeError):
            import urllib3

            unwrap(urllib3.HTTPConnectionPool, "urlopen")


def instrument_requests() -> None:
    """Instrument the requests library to inject trace context.

    This function enables automatic trace context propagation for all HTTP
    requests made using the requests library. It works regardless of import
    order - requests can be imported before or after this call.

    The instrumentation is idempotent - calling this multiple times has no
    additional effect after the first call.

    Example:
        ```python
        import lilypad

        lilypad.instrument_requests()

        # Now all requests will include trace context
        import requests

        response = requests.get("https://api.example.com")
        ```
    """
    RequestsInstrumentor().instrument()


def instrument_httpx() -> None:
    """Instrument the httpx library to inject trace context.

    This function enables automatic trace context propagation for all HTTP
    requests made using the httpx library (both sync and async clients).
    It works regardless of import order.

    The instrumentation is idempotent - calling this multiple times has no
    additional effect after the first call.

    Example:
        ```python
        import lilypad

        lilypad.instrument_httpx()

        import httpx

        # Sync client
        with httpx.Client() as client:
            response = client.get("https://api.example.com")

        # Async client
        async with httpx.AsyncClient() as client:
            response = await client.get("https://api.example.com")
        ```
    """
    HTTPXInstrumentor().instrument()


def instrument_aiohttp() -> None:
    """Instrument the aiohttp library to inject trace context.

    This function enables automatic trace context propagation for all HTTP
    requests made using the aiohttp library. It works regardless of import order.

    The instrumentation is idempotent - calling this multiple times has no
    additional effect after the first call.

    Example:
        ```python
        import lilypad

        lilypad.instrument_aiohttp()

        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.example.com") as response:
                data = await response.text()
        ```
    """
    AIOHTTPInstrumentor().instrument()


def instrument_urllib3() -> None:
    """Instrument the urllib3 library to inject trace context.

    This function enables automatic trace context propagation for all HTTP
    requests made using the urllib3 library. It works regardless of import order.

    The instrumentation is idempotent - calling this multiple times has no
    additional effect after the first call.

    Example:
        ```python
        import lilypad

        lilypad.instrument_urllib3()

        import urllib3

        http = urllib3.PoolManager()
        response = http.request("GET", "https://api.example.com")
        ```
    """
    URLLib3Instrumentor().instrument()


def uninstrument_requests() -> None:
    """Remove instrumentation from the requests library.

    This restores the original behavior of the requests library, removing
    automatic trace context injection. Safe to call even if the library
    was never instrumented.

    Example:
        ```python
        import lilypad

        # Remove requests instrumentation
        lilypad.uninstrument_requests()
        ```
    """
    RequestsInstrumentor().uninstrument()


def uninstrument_httpx() -> None:
    """Remove instrumentation from the httpx library.

    This restores the original behavior of both sync and async httpx clients,
    removing automatic trace context injection. Safe to call even if the
    library was never instrumented.

    Example:
        ```python
        import lilypad

        # Remove httpx instrumentation
        lilypad.uninstrument_httpx()
        ```
    """
    HTTPXInstrumentor().uninstrument()


def uninstrument_aiohttp() -> None:
    """Remove instrumentation from the aiohttp library.

    This restores the original behavior of aiohttp, removing automatic trace
    context injection. Safe to call even if the library was never instrumented.

    Example:
        ```python
        import lilypad

        # Remove aiohttp instrumentation
        lilypad.uninstrument_aiohttp()
        ```
    """
    AIOHTTPInstrumentor().uninstrument()


def uninstrument_urllib3() -> None:
    """Remove instrumentation from the urllib3 library.

    This restores the original behavior of urllib3, removing automatic trace
    context injection. Safe to call even if the library was never instrumented.

    Example:
        ```python
        import lilypad

        # Remove urllib3 instrumentation
        lilypad.uninstrument_urllib3()
        ```
    """
    URLLib3Instrumentor().uninstrument()
