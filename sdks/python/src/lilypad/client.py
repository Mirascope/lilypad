"""Client factory for creating and managing httpx clients.

This module provides factory functions for creating shared httpx.Client
instances that can be used across the SDK for both API calls and telemetry.
"""

import httpx

# Module-level client instance for reuse
_client_instance: httpx.Client | None = None


def get_client(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout: float = 30.0,
) -> httpx.Client:
    """Get or create a shared httpx client instance.

    This factory function ensures we reuse the same httpx.Client instance
    across the SDK for connection pooling and efficiency.

    Args:
        base_url: Base URL for the API (default: https://api.lilypad.io)
        api_key: API key for authentication
        timeout: Default timeout for requests in seconds

    Returns:
        Configured httpx.Client instance
    """
    global _client_instance

    if _client_instance is None:
        _client_instance = httpx.Client(
            base_url=base_url or "https://api.lilypad.io",
            headers={
                "Authorization": f"Bearer {api_key}" if api_key else "",
                "User-Agent": "lilypad-python-sdk",
            },
            timeout=timeout,
        )

    return _client_instance


def close_client() -> None:
    """Close the shared client instance if it exists."""
    global _client_instance
    if _client_instance:
        _client_instance.close()
        _client_instance = None
