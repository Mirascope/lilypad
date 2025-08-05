"""Factory helpers for cached Lilypad client instances."""

from __future__ import annotations

import typing
import asyncio
import logging
import weakref
from typing import TypeVar, ParamSpec, Any
from functools import (
    wraps,  # noqa: TID251
    lru_cache,
)

import httpx

from ..generated.client import Lilypad as _BaseLilypad, AsyncLilypad as _BaseAsyncLilypad
from .settings import get_settings
from ..generated.core.api_error import ApiError
from ..generated.errors.not_found_error import NotFoundError

_P = ParamSpec("_P")
_R = TypeVar("_R")

# Configure logger for this module
logger = logging.getLogger(__name__)


def _noop_fallback(*_args: object, **_kwargs: object) -> None:
    """Fallback function that swallows exceptions and returns None."""
    return None


async def _async_noop_fallback(*_args: object, **_kwargs: object) -> None:
    """Async fallback function that swallows exceptions and returns None."""
    return None


class _SafeRawClientWrapper:
    """Generic wrapper for any RawClient that converts 404 ApiError to NotFoundError."""

    def __init__(self, raw_client: object):
        self._raw_client = raw_client

    def __getattr__(self, name: str):
        attr = getattr(self._raw_client, name)
        if callable(attr):

            @wraps(attr)
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return attr(*args, **kwargs)
                except ApiError as e:
                    if e.status_code == 404:
                        raise NotFoundError(body=e.body, headers=e.headers)
                    raise e

            return wrapper
        return attr


class _SafeAsyncRawClientWrapper:
    """Generic wrapper for any AsyncRawClient that converts 404 ApiError to NotFoundError."""

    def __init__(self, raw_client: object) -> None:
        self._raw_client = raw_client

    def __getattr__(self, name: str) -> typing.Callable[..., Any]:
        attr = getattr(self._raw_client, name)
        if callable(attr):

            @wraps(attr)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                try:
                    return await attr(*args, **kwargs)
                except ApiError as e:
                    if e.status_code == 404:
                        raise NotFoundError(body=e.body, headers=e.headers)
                    raise e

            return wrapper
        return attr


class Lilypad(_BaseLilypad):
    """Enhanced synchronous Lilypad client with fail-safe error handling.

    This client automatically handles API errors and provides fallback behavior
    for non-critical failures while preserving important exceptions like NotFoundError.

    All initialization parameters are identical to the base Fern-generated client.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str,
        token: str | typing.Callable[[], str] | None = None,
        timeout: float | None = None,
        follow_redirects: bool | None = True,
        httpx_client: httpx.Client | None = None,
    ) -> None:
        """Initialize the enhanced Lilypad client.

        Args:
            base_url: The base URL for API requests
            api_key: API key for authentication (required)
            token: Optional token for additional authentication
            timeout: Request timeout in seconds
            follow_redirects: Whether to follow HTTP redirects
            httpx_client: Optional custom httpx client

        Raises:
            ValueError: If required parameters are missing
            RuntimeError: If client initialization fails
        """
        try:
            # Initialize the base client first
            super().__init__(
                base_url=base_url,
                api_key=api_key,
                token=token,
                timeout=timeout,
                follow_redirects=follow_redirects,
                httpx_client=httpx_client,
            )

            # Enhance the HTTP client with error handling
            self._enhance_http_client()

        except Exception as e:
            logger.error("Failed to initialize Lilypad client: %s", e)
            raise RuntimeError(f"Client initialization failed: {e}") from e

    def _enhance_http_client(self) -> None:
        """Enhance the HTTP client with error handling capabilities.

        Raises:
            AttributeError: If the client wrapper doesn't have the expected structure
        """
        try:
            # Wrap all raw clients in projects
            if hasattr(self, "projects"):
                self._wrap_raw_clients(self.projects)
                logger.debug("Successfully wrapped all RawClients")

        except Exception as e:
            logger.error("Failed to enhance HTTP client: %s", e)
            # Don't raise here - allow the client to work without enhancement

    def _wrap_raw_clients(self, client_obj: object) -> None:
        """Recursively wrap all _raw_client attributes."""
        # Wrap the main _raw_client if it exists
        if hasattr(client_obj, "_raw_client"):
            original_raw_client = client_obj._raw_client
            if original_raw_client is not None:
                wrapped_raw_client = _SafeRawClientWrapper(original_raw_client)
                client_obj._raw_client = wrapped_raw_client
                logger.debug("Wrapped _raw_client: %s", type(original_raw_client).__name__)

        # Recursively check all attributes for sub-clients
        for attr_name in dir(client_obj):
            if not attr_name.startswith("_"):
                try:
                    attr_obj = getattr(client_obj, attr_name)
                    if hasattr(attr_obj, "_raw_client"):
                        self._wrap_raw_clients(attr_obj)
                except Exception:
                    # Skip attributes that can't be accessed
                    pass


class AsyncLilypad(_BaseAsyncLilypad):
    """Enhanced asynchronous Lilypad client with fail-safe error handling.

    This client automatically handles API errors and provides fallback behavior
    for non-critical failures while preserving important exceptions like NotFoundError.

    All initialization parameters are identical to the base Fern-generated client.
    """

    def __init__(
        self,
        *,
        base_url: str | None = None,
        api_key: str,
        token: str | typing.Callable[[], str] | None = None,
        timeout: float | None = None,
        follow_redirects: bool | None = True,
        httpx_client: httpx.AsyncClient | None = None,
    ) -> None:
        """Initialize the enhanced AsyncLilypad client.

        Args:
            base_url: The base URL for API requests
            api_key: API key for authentication (required)
            token: Optional token for additional authentication
            timeout: Request timeout in seconds
            follow_redirects: Whether to follow HTTP redirects
            httpx_client: Optional custom async httpx client

        Raises:
            ValueError: If required parameters are missing
            RuntimeError: If client initialization fails
        """
        try:
            # Initialize the base client first
            super().__init__(
                base_url=base_url,
                api_key=api_key,
                token=token,
                timeout=timeout,
                follow_redirects=follow_redirects,
                httpx_client=httpx_client,
            )

            # Enhance the HTTP client with error handling
            self._enhance_http_client()

        except Exception as e:
            logger.error("Failed to initialize AsyncLilypad client: %s", e)
            raise RuntimeError(f"Async client initialization failed: {e}") from e

    def _enhance_http_client(self) -> None:
        """Enhance the async HTTP client with error handling capabilities.

        Raises:
            AttributeError: If the client wrapper doesn't have the expected structure
        """
        try:
            # Wrap all raw clients in projects
            if hasattr(self, "projects"):
                self._wrap_raw_clients(self.projects)
                logger.debug("Successfully wrapped all AsyncRawClients")

        except Exception as e:
            logger.error("Failed to enhance async HTTP client: %s", e)
            # Don't raise here - allow the client to work without enhancement

    def _wrap_raw_clients(self, client_obj: object) -> None:
        """Recursively wrap all _raw_client attributes."""
        # Wrap the main _raw_client if it exists
        if hasattr(client_obj, "_raw_client"):
            original_raw_client = client_obj._raw_client
            if original_raw_client is not None:
                wrapped_raw_client = _SafeAsyncRawClientWrapper(original_raw_client)
                client_obj._raw_client = wrapped_raw_client
                logger.debug("Wrapped async _raw_client: %s", type(original_raw_client).__name__)

        # Recursively check all attributes for sub-clients
        for attr_name in dir(client_obj):
            if not attr_name.startswith("_"):
                try:
                    attr_obj = getattr(client_obj, attr_name)
                    if hasattr(attr_obj, "_raw_client"):
                        self._wrap_raw_clients(attr_obj)
                except Exception:
                    # Skip attributes that can't be accessed
                    pass


@lru_cache(maxsize=256)
def _sync_singleton(api_key: str, base_url: str | None, timeout: float | None) -> Lilypad:
    """Return (or create) the process‑wide synchronous client.

    Args:
        api_key: Lilypad API key used for authentication.
        base_url: Optional base URL override
        timeout: Optional timeout override in seconds

    Returns:
        A memoized :class:`lilypad.Lilypad` instance tied to *api_key*.

    Raises:
        RuntimeError: If client creation fails
    """
    try:
        return Lilypad(api_key=api_key, base_url=base_url, timeout=timeout)
    except Exception as e:
        logger.error("Failed to create singleton Lilypad client: %s", e)
        raise RuntimeError(f"Failed to create cached client: {e}") from e


def get_sync_client(api_key: str | None = None, base_url: str | None = None, timeout: float | None = None) -> Lilypad:
    """Obtain a cached synchronous client.

    Args:
        api_key: Overrides the ``LILYPAD_API_KEY`` environment variable when
            provided.  If *None*, the environment variable is used.
        base_url: Overrides the ``LILYPAD_BASE_URL`` environment variable when
            provided.
        timeout: Overrides the ``LILYPAD_TIMEOUT`` environment variable when
            provided. If *None*, the environment variable is used (default 5.0 seconds).

    Returns:
        A cached :class:`lilypad.Lilypad`.

    Raises:
        RuntimeError: If API key is not provided and environment variable is not set
    """
    key = api_key or get_settings().api_key
    if key is None:
        raise RuntimeError("Lilypad API key not provided and LILYPAD_API_KEY is not set.")

    effective_base_url = base_url or get_settings().base_url
    effective_timeout = timeout if timeout is not None else get_settings().timeout
    logger.debug(
        "Creating sync client with api_key=*****, base_url=%s, timeout=%s", effective_base_url, effective_timeout
    )

    return _sync_singleton(key, effective_base_url, effective_timeout)


@lru_cache(maxsize=256)
def _async_singleton(
    api_key: str, loop_id_for_cache: int, base_url: str | None = None, timeout: float | None = None
) -> AsyncLilypad:
    """Return (or create) an asynchronous client bound to a specific loop.

    Args:
        api_key: Lilypad API key.
        loop_id_for_cache: ``id(asyncio.get_running_loop())`` identifying the event loop.
        base_url: Optional base URL override
        timeout: Optional timeout override in seconds

    Returns:
        An AsyncLilypad instance bound to the current event loop

    Raises:
        RuntimeError: If client creation fails
    """
    try:
        loop = asyncio.get_running_loop()
        client = AsyncLilypad(api_key=api_key, base_url=base_url, timeout=timeout)
        # Ensure the client is closed when the loop is closed.
        weakref.finalize(loop, _async_singleton.cache_clear)
        return client
    except Exception as e:
        logger.error("Failed to create singleton AsyncLilypad client: %s", e)
        raise RuntimeError(f"Failed to create cached async client: {e}") from e


def get_async_client(
    api_key: str | None = None, base_url: str | None = None, timeout: float | None = None
) -> AsyncLilypad:
    """Obtain a cached asynchronous client for the current event loop.

    The cache key is the tuple ``(api_key, id(event_loop))`` so that each
    event loop receives its own client instance.

    Args:
        api_key: Overrides the ``LILYPAD_API_KEY`` environment variable.  If
            *None*, the environment variable value is used.
        base_url: Overrides the ``LILYPAD_BASE_URL`` environment variable when
            provided.
        timeout: Overrides the ``LILYPAD_TIMEOUT`` environment variable when
            provided. If *None*, the environment variable is used (default 5.0 seconds).

    Returns:
        A cached :class:`lilypad.AsyncLilypad` for the running event loop.

    Raises:
        RuntimeError: If called outside an event loop or if API key is not available
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError as exc:  # pragma: no cover – called outside event loop
        raise RuntimeError("get_async_client() must be called from within an active event loop.") from exc

    key = api_key or get_settings().api_key
    if key is None:
        raise RuntimeError("Lilypad API key not provided and LILYPAD_API_KEY is not set.")

    effective_base_url = base_url or get_settings().base_url
    effective_timeout = timeout if timeout is not None else get_settings().timeout
    logger.debug(
        "Creating async client with api_key=*****, base_url=%s, timeout=%s", effective_base_url, effective_timeout
    )

    return _async_singleton(key, id(loop), effective_base_url, effective_timeout)


__all__ = ["AsyncLilypad", "Lilypad", "get_async_client", "get_sync_client"]
