"""Configuration and factory functions for the export system.

This module provides simple configuration and factory functions
for setting up the two-phase export system.
"""

from __future__ import annotations

from dataclasses import dataclass

from lilypad.client import Lilypad
from .processors import LLMSpanProcessor


@dataclass
class ConfigureExportersConfig:
    """Config for configure_exporters function."""

    client: Lilypad
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
    from concurrent.futures import ThreadPoolExecutor
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from .transport import TelemetryTransport, TelemetryConfig
    from .exporters import ImmediateStartExporter, LilypadOTLPExporter

    telemetry_config = TelemetryConfig(
        timeout=config.timeout,
        max_retry_attempts=config.max_retry_attempts,
    )

    transport = TelemetryTransport(
        client=config.client,
        config=telemetry_config,
    )

    start_exporter = ImmediateStartExporter(
        transport=transport,
        max_retry_attempts=config.max_retry_attempts,
    )

    otlp_exporter = LilypadOTLPExporter(
        transport=transport,
        timeout=config.timeout,
    )

    batch_processor = BatchSpanProcessor(
        span_exporter=otlp_exporter,
        max_queue_size=2048,
        schedule_delay_millis=5000,
        export_timeout_millis=30000,
        max_export_batch_size=512,
    )

    executor = ThreadPoolExecutor(
        max_workers=2,
        thread_name_prefix="llm-span-processor",
    )

    return LLMSpanProcessor(
        start_exporter=start_exporter,
        batch_processor=batch_processor,
        executor=executor,
    )
