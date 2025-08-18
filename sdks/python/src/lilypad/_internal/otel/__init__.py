"""OpenTelemetry instrumentation support for various libraries."""

from contextlib import suppress

with suppress(ImportError):
    from .openai import instrument_openai as instrument_openai

with suppress(ImportError):
    from .anthropic import instrument_anthropic as instrument_anthropic

with suppress(ImportError):
    from .google import instrument_google as instrument_google

with suppress(ImportError):
    from .azure import instrument_azure as instrument_azure

__all__ = [
    "instrument_anthropic",
    "instrument_azure",
    "instrument_google",
    "instrument_openai",
]
