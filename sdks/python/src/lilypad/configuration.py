"""Configuration utilities for Lilypad SDK initialization and setup."""

import logging
from secrets import token_bytes
from opentelemetry import trace
from opentelemetry.trace import INVALID_SPAN_ID, INVALID_TRACE_ID
from opentelemetry.sdk.trace.id_generator import IdGenerator
from rich.logging import RichHandler

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
) -> None:
    """
    Configure the lilypad SDK.

    Args:
        log_handlers (list[logging.Handler]): Custom logging handlers to use. If None, defaults to RichHandler.
        log_format (str): Custom logging format. If None, defaults to a standard format.
        log_level (int): The logging level to set. Defaults to logging.INFO.
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
