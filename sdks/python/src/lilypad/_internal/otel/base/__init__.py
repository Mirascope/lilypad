"""Base utilities for OpenTelemetry instrumentation of LLM providers."""

from .instrument import (
    BaseInstrumentor,
)
from .protocols import (
    SyncStreamHandler,
    AsyncStreamHandler,
    SyncCompletionHandler,
    AsyncCompletionHandler,
)

# from .stream_wrappers import (
#     create_stream_method_wrapper,
#     create_async_stream_method_wrapper,
# )
from .context_stream_wrappers import (
    ContextStreamHandler,
    AsyncContextStreamHandler,
    # create_context_stream_wrapper,
    # create_async_context_stream_wrapper,
)

__all__ = [
    "AsyncCompletionHandler",
    "AsyncStreamHandler",
    "BaseInstrumentor",
    "SyncCompletionHandler",
    "SyncStreamHandler",
    # "create_async_context_stream_wrapper",
    # "create_async_stream_method_wrapper",
    # "create_context_stream_wrapper",
    # "create_stream_method_wrapper",
]
