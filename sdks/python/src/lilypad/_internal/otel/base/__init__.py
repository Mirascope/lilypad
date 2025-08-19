"""Base utilities for OpenTelemetry instrumentation of LLM providers."""

from .wrappers import (
    BaseWrappers,
    create_sync_wrapper,
    create_async_wrapper,
    create_sync_stream_wrapper,
    create_async_stream_wrapper,
)
from .protocols import (
    SyncStreamHandler,
    AsyncStreamHandler,
    SyncCompletionHandler,
    AsyncCompletionHandler,
)
from .stream_wrappers import (
    create_stream_method_wrapper,
    create_async_stream_method_wrapper,
)
from .context_stream_wrappers import (
    ContextStreamHandler,
    AsyncContextStreamHandler,
    create_context_stream_wrapper,
    create_async_context_stream_wrapper,
)

__all__ = [
    "AsyncCompletionHandler",
    "AsyncStreamHandler",
    "BaseWrappers",
    "SyncCompletionHandler",
    "SyncStreamHandler",
    "create_async_context_stream_wrapper",
    "create_async_stream_method_wrapper",
    "create_async_stream_wrapper",
    "create_async_wrapper",
    "create_context_stream_wrapper",
    "create_stream_method_wrapper",
    "create_sync_stream_wrapper",
    "create_sync_wrapper",
]
