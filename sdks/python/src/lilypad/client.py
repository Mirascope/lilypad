"""Client interfaces and factory for Lilypad SDK.

This module provides interfaces and factory functions for creating Lilypad clients
that support both the Fern-generated API client and OpenTelemetry exporters.
"""

from __future__ import annotations

from typing import Protocol, TypeAlias
import httpx
import logging
from collections.abc import Callable

ApiKey: TypeAlias = str
BaseUrl: TypeAlias = str
Token: TypeAlias = str | Callable[[], str] | None

logger = logging.getLogger(__name__)


class HttpClientProtocol(Protocol):
    """Protocol for HTTP client implementations."""

    def request(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Make an HTTP request."""
        ...

    def close(self) -> None:
        """Close the client and cleanup resources."""
        ...


class AsyncHttpClientProtocol(Protocol):
    """Protocol for async HTTP client implementations."""

    async def request(
        self,
        *,
        method: str,
        url: str,
        headers: dict[str, str] | None = None,
        json: dict | None = None,
        timeout: float | None = None,
    ) -> httpx.Response:
        """Make an async HTTP request."""
        ...

    async def aclose(self) -> None:
        """Close the async client and cleanup resources."""
        ...


class TelemetryClientProtocol(Protocol):
    """Protocol for telemetry client interface."""

    def send_traces(self, *, resource_spans: list) -> None:
        """Send telemetry traces."""
        ...


class LilypadClientProtocol(Protocol):
    """Protocol for the main Lilypad client interface."""

    base_url: str
    api_key: str
    telemetry: TelemetryClientProtocol

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str,
        token: Token = None,
        timeout: float | None = None,
        follow_redirects: bool | None = True,
        httpx_client: httpx.Client | None = None,
    ) -> None:
        """Initialize the Lilypad client."""
        ...


class AsyncLilypadClientProtocol(Protocol):
    """Protocol for the async Lilypad client interface."""

    base_url: str
    api_key: str
    telemetry: TelemetryClientProtocol

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str,
        token: Token = None,
        timeout: float | None = None,
        follow_redirects: bool | None = True,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the async Lilypad client."""
        ...


class RawClientWrapperProtocol(Protocol):
    """Protocol for raw client error handling wrappers."""

    def __init__(self, raw_client: object) -> None:
        """Initialize with a raw client to wrap."""
        ...

    def __getattr__(self, name: str) -> object:
        """Intercept attribute access for error handling."""
        ...


class ClientFactoryProtocol(Protocol):
    """Protocol for client factory interface."""

    @staticmethod
    def create_sync_client(
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        token: Token = None,
        timeout: float | None = None,
        follow_redirects: bool | None = True,
        httpx_client: httpx.Client | None = None,
    ) -> LilypadClientProtocol:
        """Create a synchronous Lilypad client."""
        ...

    @staticmethod
    def create_async_client(
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        token: Token = None,
        timeout: float | None = None,
        follow_redirects: bool | None = True,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> AsyncLilypadClientProtocol:
        """Create an asynchronous Lilypad client."""
        ...

    @staticmethod
    def get_cached_sync_client(
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> LilypadClientProtocol:
        """Get or create a cached synchronous client."""
        ...

    @staticmethod
    def get_cached_async_client(
        api_key: str | None = None,
        base_url: str | None = None,
    ) -> AsyncLilypadClientProtocol:
        """Get or create a cached asynchronous client."""
        ...


class Lilypad:
    """Enhanced Lilypad client with error handling.

    Implementation will extend the Fern-generated base client and add:
    - Error handling wrappers for raw clients
    - 404 to NotFoundError conversion
    - Logging and monitoring hooks
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str,
        token: Token = None,
        timeout: float | None = None,
        follow_redirects: bool | None = True,
        httpx_client: httpx.Client | None = None,
    ) -> None:
        """Initialize the enhanced Lilypad client."""
        raise NotImplementedError("Implementation in next PR")

    def _enhance_http_client(self) -> None:
        """Enhance HTTP client with error handling."""
        raise NotImplementedError("Implementation in next PR")

    def _wrap_raw_clients(self, client_obj: object) -> None:
        """Recursively wrap raw clients for error handling."""
        raise NotImplementedError("Implementation in next PR")


class AsyncLilypad:
    """Enhanced async Lilypad client with error handling.

    Implementation will extend the Fern-generated async base client and add:
    - Async error handling wrappers for raw clients
    - 404 to NotFoundError conversion
    - Async logging and monitoring hooks
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str,
        token: Token = None,
        timeout: float | None = None,
        follow_redirects: bool | None = True,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the enhanced async Lilypad client."""
        raise NotImplementedError("Implementation in next PR")

    def _enhance_http_client(self) -> None:
        """Enhance async HTTP client with error handling."""
        raise NotImplementedError("Implementation in next PR")

    def _wrap_raw_clients(self, client_obj: object) -> None:
        """Recursively wrap async raw clients for error handling."""
        raise NotImplementedError("Implementation in next PR")


def get_sync_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> LilypadClientProtocol:
    """Get or create a cached synchronous client.

    Args:
        api_key: API key for authentication
        base_url: Base URL for the API

    Returns:
        Cached Lilypad client instance
    """
    raise NotImplementedError("Implementation in next PR")


def get_async_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> AsyncLilypadClientProtocol:
    """Get or create a cached asynchronous client.

    Args:
        api_key: API key for authentication
        base_url: Base URL for the API

    Returns:
        Cached AsyncLilypad client instance
    """
    raise NotImplementedError("Implementation in next PR")


def create_transport_client(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout: float = 30.0,
    httpx_client: httpx.Client | None = None,
) -> LilypadClientProtocol:
    """Create a client suitable for OpenTelemetry transport.

    Args:
        base_url: Base URL for the API
        api_key: API key for authentication
        timeout: Request timeout in seconds
        httpx_client: Optional custom httpx client

    Returns:
        Lilypad client configured for transport use
    """
    raise NotImplementedError("Implementation in next PR")


def close_cached_clients() -> None:
    """Close all cached client instances."""
    raise NotImplementedError("Implementation in next PR")


__all__ = [
    "AsyncHttpClientProtocol",
    "AsyncLilypad",
    "AsyncLilypadClientProtocol",
    "ClientFactoryProtocol",
    "HttpClientProtocol",
    "Lilypad",
    "LilypadClientProtocol",
    "RawClientWrapperProtocol",
    "TelemetryClientProtocol",
    "close_cached_clients",
    "create_transport_client",
    "get_async_client",
    "get_sync_client",
]
