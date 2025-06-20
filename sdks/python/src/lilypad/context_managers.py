"""Context managers for distributed tracing.

This module provides context managers for handling trace context propagation
in special cases where automatic instrumentation is not sufficient.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

from opentelemetry import context as otel_context

from ._utils.context_propagation import _extract_context


@contextmanager
def propagated_context(
    *, parent: otel_context.Context | None = None, extract_from: dict[str, Any] | None = None
) -> Generator[None, None, None]:
    """Context manager for OpenTelemetry trace context propagation.

    Args:
        parent: Parent context to attach (for cross-thread propagation)
        extract_from: Carrier dict to extract context from (e.g., HTTP headers, message headers)

    Examples:
        ```python
        # Extract from HTTP request headers
        with lilypad.propagated_context(extract_from=dict(request.headers)):
            process_data()

        # Cross-thread propagation
        with lilypad.propagated_context(parent=parent_ctx):
            process_in_thread()

        # Extract from custom message headers
        with lilypad.propagated_context(extract_from=message["headers"]):
            handle_message(message["data"])
        ```

    Note:
        Only one of parent or extract_from should be provided.
    """
    if parent and extract_from:
        raise ValueError("Cannot specify both parent and extract_from")

    if extract_from is not None:
        # Extract context from carrier
        ctx = _extract_context(extract_from)
        token = otel_context.attach(ctx)
    elif parent:
        # Use explicitly provided parent context
        token = otel_context.attach(parent)
    else:
        # No context to attach
        token = None

    try:
        yield
    finally:
        # Detach context when done
        if token is not None:
            otel_context.detach(token)
