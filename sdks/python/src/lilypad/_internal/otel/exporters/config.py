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
    raise NotImplementedError()
