"""OpenAI instrumentation module for OpenTelemetry integration."""

from .instrument import instrument_openai

__all__ = ["instrument_openai"]
