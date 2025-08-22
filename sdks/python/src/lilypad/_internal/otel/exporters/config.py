"""Configuration and factory functions for the export system.

This module provides simple configuration and factory functions
for setting up the two-phase export system.
"""

from dataclasses import dataclass

<<<<<<< HEAD
import httpx

from .processors import LLMSpanProcessor
<<<<<<< HEAD
=======
=======
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from .exporters import ImmediateStartExporter, LilypadOTLPExporter
from .processors import LLMSpanProcessor
import httpx

>>>>>>> e12254f2 (Implement Otel Exporters details without a client)
from .transport import TelemetryTransport, TelemetryConfig
>>>>>>> 619cbcba (Implement Otel Exporters details without a client)


@dataclass
class ConfigureExportersConfig:
    """Config for configure_exporters function."""

    client: httpx.Client  # httpx client, will be wrapped by Fern in future
    base_url: str = "https://api.lilypad.io"
    timeout: float = 30.0
    max_retry_attempts: int = 3


def configure_exporters(
    config: ConfigureExportersConfig,
) -> LLMSpanProcessor:
    """Configure the two-phase export system.

    This is the main entry point for setting up Lilypad exporters.
    It creates and configures all necessary components for the
    two-phase export system.

    Args:
        config: Configuration including the Lilypad client.
    Returns:
        Configured LLMSpanProcessor ready for use with OpenTelemetry.
    """
    telemetry_config = TelemetryConfig(
        timeout=config.timeout,
        max_retry_attempts=config.max_retry_attempts
    )
    
    transport = TelemetryTransport(
        client=config.client,
        config=telemetry_config,
        base_url=config.base_url
    )
    
    start_exporter = ImmediateStartExporter(
        transport=transport,
        max_retry_attempts=config.max_retry_attempts
    )
    
    otlp_exporter = LilypadOTLPExporter(
        transport=transport,
        timeout=config.timeout
    )
    
    batch_processor = BatchSpanProcessor(
        span_exporter=otlp_exporter
    )
    
    return LLMSpanProcessor(
        start_exporter=start_exporter,
        batch_processor=batch_processor
    )
