"""Lilypad SDK - The official Python library for the Lilypad API."""

from contextlib import suppress

from . import configuration
from .configuration import configure

with suppress(ImportError):
    from ._internal.otel import instrument_openai

with suppress(ImportError):
    from ._internal.otel import instrument_anthropic

with suppress(ImportError):
    from ._internal.otel import instrument_google

with suppress(ImportError):
    from ._internal.otel import instrument_azure

__all__ = [
    "configuration",
    "configure",
    "instrument_anthropic",
    "instrument_azure",
    "instrument_google",
    "instrument_openai",
]
