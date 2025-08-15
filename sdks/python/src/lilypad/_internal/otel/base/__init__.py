"""Base utilities for OpenTelemetry instrumentation of LLM providers."""

from .wrappers import (
    create_sync_wrapper,
    create_async_wrapper,
)
from .stream_wrappers import (
    create_stream_method_wrapper,
    create_async_stream_method_wrapper,
)
from .context_stream_wrappers import (
    create_context_stream_wrapper,
    create_async_context_stream_wrapper,
    ContextStreamHandler,
    AsyncContextStreamHandler,
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
    "create_async_context_stream_wrapper",
    "create_async_stream_method_wrapper",
    "create_async_wrapper",
    "create_context_stream_wrapper",
    "create_stream_method_wrapper",
    "create_sync_wrapper",
]
