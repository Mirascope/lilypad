"""Client interfaces and factory for Lilypad SDK.

This module provides interfaces and factory functions for creating Lilypad clients
that support both the Fern-generated API client and OpenTelemetry exporters.
"""

from __future__ import annotations

from typing import TypeAlias, TypeVar, ParamSpec
import asyncio
import weakref
from functools import lru_cache
import httpx
import logging
from collections.abc import Callable

from ._generated.client import (
    Lilypad as _BaseLilypad,
    AsyncLilypad as _BaseAsyncLilypad,
)
from ._internal.settings import get_settings

ApiKey: TypeAlias = str
BaseUrl: TypeAlias = str
Token: TypeAlias = str | Callable[[], str] | None
_P = ParamSpec("_P")
_R = TypeVar("_R")

logger = logging.getLogger(__name__)


class Lilypad(_BaseLilypad):
    """Enhanced Lilypad client with error handling.

    This client automatically handles API errors and provides fallback behavior
    for non-critical failures while preserving important exceptions like NotFoundError.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        token: Token = None,
        timeout: float | None = None,
        follow_redirects: bool | None = True,
        httpx_client: httpx.Client | None = None,
    ) -> None:
        """Initialize the enhanced Lilypad client."""
        try:
            effective_api_key = api_key or get_settings().api_key
            if not effective_api_key:
                raise ValueError("API key is required")

            headers = {"Authorization": f"Bearer {effective_api_key}"}
            if httpx_client:
                if hasattr(httpx_client, "headers"):
                    httpx_client.headers.update(headers)
            else:
                httpx_client = httpx.Client(
                    headers=headers,
                    timeout=timeout or 30.0,
                    follow_redirects=follow_redirects
                    if follow_redirects is not None
                    else True,
                )

            super().__init__(
                base_url=base_url or get_settings().base_url,
                timeout=timeout,
                follow_redirects=follow_redirects,
                httpx_client=httpx_client,
            )

            self.api_key = effective_api_key
            self.base_url = (
                base_url
                or get_settings().base_url
                or self._client_wrapper.get_base_url()
            )

        except Exception as e:
            logger.error("Failed to initialize Lilypad client: %s", e)
            raise RuntimeError(f"Client initialization failed: {e}") from e


class AsyncLilypad(_BaseAsyncLilypad):
    """Enhanced async Lilypad client with error handling.

    This client automatically handles API errors and provides fallback behavior
    for non-critical failures while preserving important exceptions like NotFoundError.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str | None = None,
        token: Token = None,
        timeout: float | None = None,
        follow_redirects: bool | None = True,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the enhanced async Lilypad client."""
        try:
            effective_api_key = api_key or get_settings().api_key
            if not effective_api_key:
                raise ValueError("API key is required")

            headers = {"Authorization": f"Bearer {effective_api_key}"}
            if httpx_client:
                if hasattr(httpx_client, "headers"):
                    httpx_client.headers.update(headers)
            else:
                httpx_client = httpx.AsyncClient(
                    headers=headers,
                    timeout=timeout or 30.0,
                    follow_redirects=follow_redirects
                    if follow_redirects is not None
                    else True,
                )

            super().__init__(
                base_url=base_url or get_settings().base_url,
                timeout=timeout,
                follow_redirects=follow_redirects,
                httpx_client=httpx_client,
            )

            self.api_key = effective_api_key
            self.base_url = (
                base_url
                or get_settings().base_url
                or self._client_wrapper.get_base_url()
            )

        except Exception as e:
            logger.error("Failed to initialize AsyncLilypad client: %s", e)
            raise RuntimeError(f"Async client initialization failed: {e}") from e


@lru_cache(maxsize=256)
def _sync_singleton(api_key: str, base_url: str | None) -> Lilypad:
    """Return (or create) the process-wide synchronous client."""
    try:
        return Lilypad(api_key=api_key, base_url=base_url)
    except Exception as e:
        logger.error("Failed to create singleton Lilypad client: %s", e)
        raise RuntimeError(f"Failed to create cached client: {e}") from e


def get_sync_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> Lilypad:
    """Get or create a cached synchronous client.

    Args:
        api_key: API key for authentication
        base_url: Base URL for the API

    Returns:
        Cached Lilypad client instance
    """
    key = api_key or get_settings().api_key
    if key is None:
        raise RuntimeError(
            "Lilypad API key not provided and LILYPAD_API_KEY is not set."
        )

    effective_base_url = base_url or get_settings().base_url
    logger.debug(
        "Creating sync client with api_key=*****, base_url=%s", effective_base_url
    )

    return _sync_singleton(key, effective_base_url)


@lru_cache(maxsize=256)
def _async_singleton(
    api_key: str, loop_id_for_cache: int, base_url: str | None = None
) -> AsyncLilypad:
    """Return (or create) an asynchronous client bound to a specific loop."""
    try:
        loop = asyncio.get_running_loop()
        client = AsyncLilypad(api_key=api_key, base_url=base_url)
        weakref.finalize(loop, _async_singleton.cache_clear)
        return client
    except Exception as e:
        logger.error("Failed to create singleton AsyncLilypad client: %s", e)
        raise RuntimeError(f"Failed to create cached async client: {e}") from e


def get_async_client(
    api_key: str | None = None,
    base_url: str | None = None,
) -> AsyncLilypad:
    """Get or create a cached asynchronous client.

    Args:
        api_key: API key for authentication
        base_url: Base URL for the API

    Returns:
        Cached AsyncLilypad client instance
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError as exc:
        raise RuntimeError(
            "get_async_client() must be called from within an active event loop."
        ) from exc

    key = api_key or get_settings().api_key
    if key is None:
        raise RuntimeError(
            "Lilypad API key not provided and LILYPAD_API_KEY is not set."
        )

    effective_base_url = base_url or get_settings().base_url
    logger.debug(
        "Creating async client with api_key=*****, base_url=%s", effective_base_url
    )

    return _async_singleton(key, id(loop), effective_base_url)


def create_transport_client(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout: float = 30.0,
    httpx_client: httpx.Client | None = None,
) -> Lilypad:
    """Create a client suitable for OpenTelemetry transport.

    Args:
        base_url: Base URL for the API
        api_key: API key for authentication
        timeout: Request timeout in seconds
        httpx_client: Optional custom httpx client

    Returns:
        Lilypad client configured for transport use
    """
    return Lilypad(
        base_url=base_url,
        api_key=api_key,
        timeout=timeout,
        httpx_client=httpx_client,
    )


def close_cached_clients() -> None:
    """Close all cached client instances."""
    _sync_singleton.cache_clear()
    _async_singleton.cache_clear()


# Temporary Function for this PR.
def get_client(
    api_key: str | None = None,
    base_url: str | None = None,
    timeout: float = 30.0,
) -> Lilypad:
    return get_sync_client(api_key=api_key, base_url=base_url)


__all__ = [
    "AsyncLilypad",
    "Lilypad",
    "close_cached_clients",
    "create_transport_client",
    "get_async_client",
    "get_client",
    "get_sync_client",
]
