"""Configuration utilities for Lilypad SDK initialization and setup."""

import logging
from secrets import token_bytes

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.id_generator import IdGenerator
from opentelemetry.trace import INVALID_SPAN_ID, INVALID_TRACE_ID
from rich.logging import RichHandler

from lilypad._internal.otel.exporters import (
    configure_exporters,
    ConfigureExportersConfig,
)
from lilypad.client import get_client

DEFAULT_LOG_LEVEL: int = logging.INFO


class CryptoIdGenerator(IdGenerator):
    """Generate span/trace IDs with cryptographically secure randomness."""

    def _random_int(self, n_bytes: int) -> int:
        """Generate a random integer with the specified number of bytes."""
        return int.from_bytes(token_bytes(n_bytes), "big")

    def generate_span_id(self) -> int:
        """Generate a valid 64-bit span ID using secure random bytes."""
        span_id = self._random_int(8)
        while span_id == INVALID_SPAN_ID:
            span_id = self._random_int(8)
        return span_id

    def generate_trace_id(self) -> int:
        """Generate a valid 128-bit trace ID using secure random bytes."""
        trace_id = self._random_int(16)
        while trace_id == INVALID_TRACE_ID:
            trace_id = self._random_int(16)
        return trace_id


def configure(
    *,
    log_handlers: list[logging.Handler] | None = None,
    log_format: str | None = None,
    log_level: int = DEFAULT_LOG_LEVEL,
    lilypad_endpoint: str | None = None,
    api_key: str | None = None,
    timeout: float = 30.0,
    max_retry_attempts: int = 3,
) -> None:
    """Configure the lilypad SDK.

    Sets up logging and optionally configures OpenTelemetry exporters for
    two-phase LLM tracing.

    Args:
        log_handlers: Custom logging handlers to use. If None, defaults to RichHandler.
        log_format: Custom logging format. If None, defaults to a standard format.
        log_level: The logging level to set. Defaults to logging.INFO.
        lilypad_endpoint: Optional Lilypad ingestion endpoint URL for tracing.
        api_key: Optional API key for authentication with Lilypad endpoint.
        timeout: Request timeout in seconds for telemetry operations.
        max_retry_attempts: Maximum number of retry attempts for failed exports.
    """
    logger = logging.getLogger("lilypad")
    logger.setLevel(log_level)
    logger.handlers.clear()
    handlers = log_handlers or [RichHandler()]
    for handler in handlers:
        handler.setFormatter(logging.Formatter(log_format))
        logger.addHandler(handler)

    if trace.get_tracer_provider().__class__.__name__ == "TracerProvider":
        logger.info("TracerProvider already initialized.")  # noqa: T201
        return

    if lilypad_endpoint and api_key:
        # Get or create the shared Lilypad client
        client = get_client(
            base_url=lilypad_endpoint,
            api_key=api_key,
            timeout=timeout,
        )

        config = ConfigureExportersConfig(
            client=client,
            base_url=lilypad_endpoint,
            timeout=timeout,
            max_retry_attempts=max_retry_attempts,
        )

        current_provider = trace.get_tracer_provider()
        if isinstance(current_provider, TracerProvider):
            processor = configure_exporters(config)
            current_provider.add_span_processor(processor)
            logger.info("Added Lilypad exporters to existing TracerProvider")
        else:
            provider = TracerProvider()

            processor = configure_exporters(config)
            provider.add_span_processor(processor)

            trace.set_tracer_provider(provider)
            logger.info("Configured Lilypad OpenTelemetry exporters")
