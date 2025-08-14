"""OpenTelemetry instrumentation support for various libraries."""

from contextlib import suppress

with suppress(ImportError):
    from .openai import instrument_openai as instrument_openai

with suppress(ImportError):
    from .anthropic import instrument_anthropic as instrument_anthropic

__all__ = [
    "instrument_anthropic",
    "instrument_openai",
]
