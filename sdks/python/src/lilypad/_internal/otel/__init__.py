"""OpenTelemetry instrumentation support for various libraries."""

from contextlib import suppress

with suppress(ImportError):
    from .openai import instrument_openai as instrument_openai

__all__ = [
    "instrument_openai",
]
