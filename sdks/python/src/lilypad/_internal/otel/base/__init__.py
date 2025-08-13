"""Base utilities for OpenTelemetry instrumentation of LLM providers."""

from .wrappers import (
    create_sync_wrapper,
    create_async_wrapper,
)
from .protocols import (
    SyncStreamHandler,
    AsyncStreamHandler,
    SyncCompletionHandler,
    AsyncCompletionHandler,
)

__all__ = [
    "AsyncCompletionHandler",
    "AsyncStreamHandler",
    "SyncCompletionHandler",
    "SyncStreamHandler",
    "create_async_wrapper",
    "create_sync_wrapper",
]
