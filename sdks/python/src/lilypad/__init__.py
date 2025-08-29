"""Lilypad SDK - The official Python library for the Lilypad API."""

from contextlib import suppress

from . import configuration
from .configuration import configure
from .client import (
    Lilypad,
    AsyncLilypad,
    get_client,
    get_sync_client,
    get_async_client,
    create_transport_client,
    close_cached_clients,
)

with suppress(ImportError):
    from ._internal.otel import instrument_openai

with suppress(ImportError):
    from ._internal.otel import instrument_anthropic

from .tracing import trace
from .spans import span
from .errors import (
    LilypadException,
    SpanNotFoundError,
    RemoteExecutionError,
    VersionResolutionError,
    ConfigurationError,
)

__all__ = [
    "AsyncLilypad",
    "ConfigurationError",
    "Lilypad",
    "LilypadException",
    "RemoteExecutionError",
    "SpanNotFoundError",
    "VersionResolutionError",
    "close_cached_clients",
    "configuration",
    "configure",
    "create_transport_client",
    "get_async_client",
    "get_client",
    "get_sync_client",
    "instrument_anthropic",
    "instrument_openai",
    "span",
    "trace",
]
