"""Context managers for distributed tracing.

This module provides context managers for handling trace context propagation
in special cases where automatic instrumentation is not sufficient.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Any, Generator

from opentelemetry import context as otel_context

from ._utils.context_propagation import extract_context


@contextmanager
def propagated_context(carrier: dict[str, Any]) -> Generator[None, None, None]:
    """Context manager for extracting and propagating trace context from incoming requests.

    Use this when you need to extract trace context from incoming HTTP headers
    and propagate it to traced functions within your request handler.

    Args:
        carrier: A dictionary-like object containing trace context (typically HTTP headers)

    Example:
        ```python
        from fastapi import FastAPI, Request
        from lilypad import trace, propagated_context

        app = FastAPI()


        @trace()
        def process_data(data: dict) -> dict:
            # This function is defined at module level
            return {"result": "processed", "data": data}


        @app.post("/api/process")
        async def process_request(request: Request, data: dict):
            with propagated_context(dict(request.headers)):
                # process_data will be a child of the incoming trace
                return await process_data(data)
        ```

    Note:
        This context manager temporarily attaches the extracted context,
        ensuring proper cleanup when the context exits.
    """
    # Extract context from carrier
    ctx = extract_context(carrier)

    # Attach the context
    token = otel_context.attach(ctx)

    try:
        yield
    finally:
        # Detach context when done
        if token is not None:
            otel_context.detach(token)


@contextmanager
def context(
    *, parent: otel_context.Context | None = None, extract_from: dict[str, Any] | None = None
) -> Generator[None, None, None]:
    """Context manager for manual parent context setting.

    Use this when you need to manually set a parent context for traced functions,
    such as when passing context between threads or processing messages from queues.

    Args:
        parent: An explicit parent context to use
        extract_from: A carrier to extract context from (e.g., message headers)

    Example with explicit parent:
        ```python
        from opentelemetry import context as otel_context
        from lilypad import trace, context

        # In main thread
        current_ctx = otel_context.get_current()


        # In worker thread
        def worker_process(data: dict, parent_ctx):
            with context(parent=parent_ctx):
                return process_data(data)
        ```

    Example with message queue:
        ```python
        from lilypad import trace, context


        def process_message(message: dict):
            with context(extract_from=message["headers"]):
                return handle_message(message["data"])
        ```

    Note:
        Only one of parent or extract_from should be provided.
    """
    if parent and extract_from:
        raise ValueError("Cannot specify both parent and extract_from")

    if extract_from:
        # Extract context from carrier
        ctx = extract_context(extract_from)
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
