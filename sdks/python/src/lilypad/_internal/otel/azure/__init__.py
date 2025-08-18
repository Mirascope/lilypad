"""Azure AI Inference instrumentation module for OpenTelemetry integration."""

from .instrument import instrument_azure

__all__ = ["instrument_azure"]
