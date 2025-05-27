"""Factory helpers for cached Lilypad client instances."""

from __future__ import annotations

import typing
import asyncio
import logging
import weakref
from typing import TypeVar, ParamSpec
from functools import (
    wraps,  # noqa: TID251
    lru_cache,
)

import httpx

from ...client import Lilypad as _BaseLilypad, AsyncLilypad as _BaseAsyncLilypad
from .settings import get_settings
from ..exceptions import LilypadPaymentRequiredError
from .call_safely import call_safely
from ...core.api_error import ApiError
from ...errors.not_found_error import NotFoundError

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


class _SafeHttpClientMixin:
    """Mixin class providing common error handling logic for HTTP clients."""

    @staticmethod
    def _handle_api_error(error: ApiError) -> None:
        """Handle API errors with appropriate conversion.

        Args:
            error: The API error to handle

        Raises:
            LilypadPaymentRequiredError: If the error is a payment required error
            ApiError: Re-raises the original error for other cases
        """
        if hasattr(error, "status_code") and error.status_code == LilypadPaymentRequiredError.status_code:
            logger.debug("Converting ApiError to LilypadPaymentRequiredError: %s", error)
            raise LilypadPaymentRequiredError(error) from None
        raise error


class _SafeHttpClientWrapper(_SafeHttpClientMixin):
    """Thread-safe wrapper for synchronous HTTP client with error handling."""

    def __init__(self, wrapped_client: typing.Any) -> None:
        """Initialize the wrapper with the original HTTP client.

        Args:
            wrapped_client: The original HTTP client to wrap

        Raises:
            TypeError: If wrapped_client is None
        """
        if wrapped_client is None:
            raise TypeError("wrapped_client cannot be None")
        self._wrapped_client = wrapped_client

    def __getattr__(self, name: str) -> typing.Any:
        """Delegate attribute access to the wrapped client.

        Args:
            name: Attribute name to access

        Returns:
            The attribute from the wrapped client, with request method enhanced

        Raises:
            AttributeError: If the attribute doesn't exist on the wrapped client
        """
        try:
            attr = getattr(self._wrapped_client, name)
        except AttributeError:
            logger.warning("Attribute '%s' not found on wrapped client", name)
            raise

        # Wrap the request method with error handling
        if name == "request" and callable(attr):
            return self._create_safe_request(attr)

        return attr

    def _create_safe_request(
        self, original_request: typing.Callable[..., typing.Any]
    ) -> typing.Callable[..., typing.Any]:
        """Create a safe version of the request method.

        Args:
            original_request: The original request method

        Returns:
            Enhanced request method with error handling
        """

        @call_safely(_noop_fallback, exclude=(NotFoundError,))
        @wraps(original_request)
        def safe_request(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            try:
                return original_request(*args, **kwargs)
            except ApiError as e:
                self._handle_api_error(e)

        return safe_request


class _SafeAsyncHttpClientWrapper(_SafeHttpClientMixin):
    """Thread-safe wrapper for asynchronous HTTP client with error handling."""

    def __init__(self, wrapped_client: typing.Any) -> None:
        """Initialize the wrapper with the original HTTP client.

        Args:
            wrapped_client: The original async HTTP client to wrap

        Raises:
            TypeError: If wrapped_client is None
        """
        if wrapped_client is None:
            raise TypeError("wrapped_client cannot be None")
        self._wrapped_client = wrapped_client

    def __getattr__(self, name: str) -> typing.Any:
        """Delegate attribute access to the wrapped client.

        Args:
            name: Attribute name to access

        Returns:
            The attribute from the wrapped client, with request method enhanced

        Raises:
            AttributeError: If the attribute doesn't exist on the wrapped client
        """
        try:
            attr = getattr(self._wrapped_client, name)
        except AttributeError:
            logger.warning("Attribute '%s' not found on wrapped async client", name)
            raise

        # Wrap the request method with error handling
        if name == "request" and callable(attr):
            return self._create_safe_request(attr)

        return attr

    def _create_safe_request(
        self, original_request: typing.Callable[..., typing.Awaitable[typing.Any]]
    ) -> typing.Callable[..., typing.Awaitable[typing.Any]]:
        """Create a safe version of the async request method.

        Args:
            original_request: The original async request method

        Returns:
            Enhanced async request method with error handling
        """

        @call_safely(_async_noop_fallback, exclude=(NotFoundError,))
        @wraps(original_request)
        async def safe_request(*args: typing.Any, **kwargs: typing.Any) -> typing.Any:
            try:
                return await original_request(*args, **kwargs)
            except ApiError as e:
                self._handle_api_error(e)

        return safe_request


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
        if not hasattr(self, "_client_wrapper"):
            logger.warning("Client wrapper not found, skipping HTTP client enhancement")
            return

        if not hasattr(self._client_wrapper, "httpx_client"):
            logger.warning("HTTP client not found in client wrapper, skipping enhancement")
            return

        try:
            original_client = self._client_wrapper.httpx_client
            if original_client is not None:
                self._client_wrapper.httpx_client = _SafeHttpClientWrapper(original_client)
                logger.debug("Successfully enhanced HTTP client with error handling")
            else:
                logger.warning("HTTP client is None, cannot enhance")
        except Exception as e:
            logger.error("Failed to enhance HTTP client: %s", e)
            # Don't raise here - allow the client to work without enhancement


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
        if not hasattr(self, "_client_wrapper"):
            logger.warning("Client wrapper not found, skipping async HTTP client enhancement")
            return

        if not hasattr(self._client_wrapper, "httpx_client"):
            logger.warning("Async HTTP client not found in client wrapper, skipping enhancement")
            return

        try:
            original_client = self._client_wrapper.httpx_client
            if original_client is not None:
                self._client_wrapper.httpx_client = _SafeAsyncHttpClientWrapper(original_client)
                logger.debug("Successfully enhanced async HTTP client with error handling")
            else:
                logger.warning("Async HTTP client is None, cannot enhance")
        except Exception as e:
            logger.error("Failed to enhance async HTTP client: %s", e)
            # Don't raise here - allow the client to work without enhancement


@lru_cache(maxsize=256)
def _sync_singleton(api_key: str, base_url: str | None) -> Lilypad:
    """Return (or create) the process‑wide synchronous client.

    Args:
        api_key: Lilypad API key used for authentication.
        base_url: Optional base URL override

    Returns:
        A memoized :class:`lilypad.Lilypad` instance tied to *api_key*.

    Raises:
        RuntimeError: If client creation fails
    """
    try:
        return Lilypad(api_key=api_key, base_url=base_url)
    except Exception as e:
        logger.error("Failed to create singleton Lilypad client: %s", e)
        raise RuntimeError(f"Failed to create cached client: {e}") from e


def get_sync_client(api_key: str | None = None, base_url: str | None = None) -> Lilypad:
    """Obtain a cached synchronous client.

    Args:
        api_key: Overrides the ``LILYPAD_API_KEY`` environment variable when
            provided.  If *None*, the environment variable is used.
        base_url: Overrides the ``LILYPAD_BASE_URL`` environment variable when
            provided.

    Returns:
        A cached :class:`lilypad.Lilypad`.

    Raises:
        RuntimeError: If API key is not provided and environment variable is not set
    """
    key = api_key or get_settings().api_key
    if key is None:
        raise RuntimeError("Lilypad API key not provided and LILYPAD_API_KEY is not set.")

    effective_base_url = base_url or get_settings().base_url
    logger.debug("Creating sync client with api_key=*****, base_url=%s", effective_base_url)

    return _sync_singleton(key, effective_base_url)


@lru_cache(maxsize=256)
def _async_singleton(api_key: str, loop_id_for_cache: int, base_url: str | None = None) -> AsyncLilypad:
    """Return (or create) an asynchronous client bound to a specific loop.

    Args:
        api_key: Lilypad API key.
        loop_id_for_cache: ``id(asyncio.get_running_loop())`` identifying the event loop.
        base_url: Optional base URL override

    Returns:
        An AsyncLilypad instance bound to the current event loop

    Raises:
        RuntimeError: If client creation fails
    """
    try:
        loop = asyncio.get_running_loop()
        client = AsyncLilypad(api_key=api_key, base_url=base_url)
        # Ensure the client is closed when the loop is closed.
        weakref.finalize(loop, _async_singleton.cache_clear)
        return client
    except Exception as e:
        logger.error("Failed to create singleton AsyncLilypad client: %s", e)
        raise RuntimeError(f"Failed to create cached async client: {e}") from e


def get_async_client(api_key: str | None = None, base_url: str | None = None) -> AsyncLilypad:
    """Obtain a cached asynchronous client for the current event loop.

    The cache key is the tuple ``(api_key, id(event_loop))`` so that each
    event loop receives its own client instance.

    Args:
        api_key: Overrides the ``LILYPAD_API_KEY`` environment variable.  If
            *None*, the environment variable value is used.
        base_url: Overrides the ``LILYPAD_BASE_URL`` environment variable when
            provided.

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
    logger.debug("Creating async client with api_key=*****, base_url=%s", effective_base_url)

    return _async_singleton(key, id(loop), effective_base_url)


__all__ = ["AsyncLilypad", "Lilypad", "get_async_client", "get_sync_client"]
