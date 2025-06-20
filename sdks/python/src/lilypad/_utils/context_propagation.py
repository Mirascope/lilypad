"""Context propagation utilities for distributed tracing.

This module provides utilities for extracting and injecting trace context
across process boundaries using OpenTelemetry propagators.
"""

from __future__ import annotations

import os
from typing import Any, MutableMapping

from opentelemetry import context, propagate
from opentelemetry.propagators.b3 import B3MultiFormat, B3SingleFormat
from opentelemetry.propagators.composite import CompositePropagator
from opentelemetry.propagators.jaeger import JaegerPropagator
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator


def get_propagator() -> CompositePropagator:
    """Get the configured propagator based on environment settings.

    Supports multiple propagation formats:
    - tracecontext (W3C Trace Context) - default
    - b3 (B3 Single Format)
    - b3multi (B3 Multi Format)
    - jaeger (Jaeger)
    - composite (all of the above)

    Returns:
        A configured propagator instance
    """
    propagator_type = os.getenv("LILYPAD_PROPAGATOR", "tracecontext").lower()

    if propagator_type == "b3":
        return CompositePropagator([B3SingleFormat()])
    elif propagator_type == "b3multi":
        return CompositePropagator([B3MultiFormat()])
    elif propagator_type == "jaeger":
        return CompositePropagator([JaegerPropagator()])
    elif propagator_type == "composite":
        # Support all common formats
        return CompositePropagator(
            [
                TraceContextTextMapPropagator(),
                B3SingleFormat(),
                B3MultiFormat(),
                JaegerPropagator(),
            ]
        )
    else:
        # Default to W3C Trace Context
        return CompositePropagator([TraceContextTextMapPropagator()])


class ContextPropagator:
    """Utility class for extracting and injecting trace context.

    WARNING: This class modifies global OpenTelemetry state by calling
    `propagate.set_global_textmap()`. This affects all OpenTelemetry
    instrumentation in the current process. If you have other OpenTelemetry
    integrations, they will use the propagator configured here.

    The propagator type can be controlled via the LILYPAD_PROPAGATOR
    environment variable. Supported values:
    - "tracecontext" (default): W3C Trace Context
    - "b3": B3 Single Format
    - "b3multi": B3 Multi Format
    - "jaeger": Jaeger format
    - "composite": All formats (for maximum compatibility)
    """

    def __init__(self, set_global: bool = True) -> None:
        """Initialize the context propagator.

        Args:
            set_global: Whether to set the global OpenTelemetry propagator.
                       Default is True for backward compatibility.

        WARNING: If set_global is True, this sets the global OpenTelemetry
        propagator, affecting all trace context propagation in the current process.
        """
        self.propagator = get_propagator()
        # Set the global propagator - this affects the entire process
        if set_global:
            propagate.set_global_textmap(self.propagator)

    def extract_context(self, carrier: dict[str, Any]) -> context.Context:
        """Extract trace context from a carrier (e.g., HTTP headers).

        Args:
            carrier: A dictionary-like object containing trace context
                    (typically HTTP headers)

        Returns:
            The extracted context
        """
        return propagate.extract(carrier)

    def inject_context(self, carrier: MutableMapping[str, str], context: context.Context | None = None) -> None:
        """Inject current trace context into a carrier.

        Args:
            carrier: A mutable mapping to inject context into
                    (typically HTTP headers)
            context: Optional context to inject. If None, uses current context
        """
        propagate.inject(carrier, context=context)

    def with_extracted_context(self, carrier: dict[str, Any]) -> tuple[context.Context, object | None]:
        """Extract context and attach it, returning the context and token.

        This is useful for manual context management.

        Args:
            carrier: A dictionary-like object containing trace context

        Returns:
            Tuple of (extracted context, detach token)
        """
        ctx = self.extract_context(carrier)
        token = context.attach(ctx)
        return ctx, token

    def detach_context(self, token: object | None) -> None:
        """Detach a previously attached context.

        Args:
            token: The token returned from attach operation
        """
        if token is not None:
            context.detach(token)


# Global instance for convenience - created lazily
_propagator: ContextPropagator | None = None


def _get_propagator() -> ContextPropagator:
    """Get or create the global propagator instance."""
    global _propagator
    if _propagator is None:
        # Check if we should set global propagator
        # This is controlled by whether configure() has been called
        import os

        set_global = os.environ.get("_LILYPAD_PROPAGATOR_SET_GLOBAL", "true").lower() == "true"
        _propagator = ContextPropagator(set_global=set_global)
    return _propagator


def _extract_context(carrier: dict[str, Any]) -> context.Context:
    """Extract trace context from a carrier (e.g., HTTP headers).

    This function extracts OpenTelemetry trace context from a carrier object,
    typically HTTP headers received from a request. This allows distributed
    traces to maintain parent-child relationships across service boundaries.

    Args:
        carrier: A dictionary-like object containing trace context headers.
                 Typically HTTP headers from an incoming request.

    Returns:
        An OpenTelemetry Context object containing the extracted trace information.
        This context can be used to create child spans or passed to other functions.

    Example:
        Basic usage in a web handler:

        ```python
        from fastapi import FastAPI, Request
        from lilypad import trace
        from lilypad._utils.context_propagation import extract_context

        app = FastAPI()


        @app.post("/process")
        async def process_request(request: Request, data: dict):
            # Extract trace context from incoming request headers
            context = extract_context(dict(request.headers))

            # Use the extracted context in a traced function
            @trace(parent_context=context)
            async def process_data(data: dict) -> dict:
                # This span will be a child of the incoming trace
                result = await do_processing(data)
                return result

            return await process_data(data)
        ```

        Manual context management:

        ```python
        from opentelemetry import context as otel_context
        from lilypad._utils.context_propagation import extract_context


        def handle_message(headers: dict, payload: dict):
            # Extract context from message headers
            ctx = extract_context(headers)

            # Attach the context for this scope
            token = otel_context.attach(ctx)
            try:
                # All traces within this block will use the extracted context
                process_message(payload)
            finally:
                # Detach context when done
                otel_context.detach(token)
        ```

        Using with Flask:

        ```python
        from flask import Flask, request
        from lilypad import trace
        from lilypad._utils.context_propagation import extract_context

        app = Flask(__name__)


        @app.route("/api/endpoint", methods=["POST"])
        def api_endpoint():
            # Extract context from Flask request headers
            context = extract_context(dict(request.headers))

            @trace(parent_context=context)
            def handle_request(data):
                # Process as child of incoming trace
                return {"status": "processed", "data": data}

            return handle_request(request.json)
        ```

    Note:
        The function looks for trace headers based on the configured propagator:
        - W3C TraceContext: looks for 'traceparent' header
        - B3: looks for 'b3' or 'x-b3-*' headers
        - Jaeger: looks for 'uber-trace-id' header

        If no valid trace context is found, returns an empty context.
    """
    return _get_propagator().extract_context(carrier)


def _inject_context(carrier: MutableMapping[str, str], context: context.Context | None = None) -> None:
    """Inject current trace context into a carrier (e.g., HTTP headers).

    This function injects the current OpenTelemetry trace context into a carrier
    object, typically HTTP headers. This allows trace context to be propagated
    across service boundaries in distributed systems.

    Args:
        carrier: A mutable mapping (e.g., dict) to inject trace context into.
                 Typically HTTP headers that will be sent with a request.
        context: Optional specific context to inject. If None (default),
                 uses the current active context.

    Returns:
        None. The carrier is modified in-place with trace headers.

    Example:
        Basic usage with HTTP requests:

        ```python
        import httpx
        from lilypad import trace
        from lilypad._utils.context_propagation import inject_context


        @trace()
        async def call_external_service(data: dict) -> dict:
            # Create headers dict
            headers = {}

            # Inject current trace context into headers
            inject_context(headers)
            # Now headers contains: {'traceparent': '00-trace_id-span_id-01'}

            # Make HTTP request with trace context
            async with httpx.AsyncClient() as client:
                response = await client.post("https://api.example.com/process", json=data, headers=headers)
                return response.json()
        ```

        Using with requests library:

        ```python
        import requests
        from lilypad import trace
        from lilypad._utils.context_propagation import inject_context


        @trace()
        def sync_call_service(payload: dict) -> dict:
            headers = {"Content-Type": "application/json"}

            # Add trace context to existing headers
            inject_context(headers)

            response = requests.post("https://api.example.com/endpoint", json=payload, headers=headers)
            return response.json()
        ```

        Injecting specific context:

        ```python
        from opentelemetry import context as otel_context

        # Capture context from one trace
        saved_context = otel_context.get_current()

        # Later, inject that specific context
        headers = {}
        inject_context(headers, context=saved_context)
        ```

    Note:
        The exact headers added depend on the configured propagator format:
        - W3C TraceContext: adds 'traceparent' (and optionally 'tracestate')
        - B3: adds 'b3' header (single format) or 'x-b3-*' headers (multi format)
        - Jaeger: adds 'uber-trace-id' header
    """
    _get_propagator().inject_context(carrier, context)


def with_extracted_context(carrier: dict[str, Any]) -> tuple[context.Context, object | None]:
    """Extract context and attach it, returning the context and token.

    Args:
        carrier: A dictionary-like object containing trace context

    Returns:
        Tuple of (extracted context, detach token)
    """
    return _get_propagator().with_extracted_context(carrier)


def detach_context(token: object | None) -> None:
    """Detach a previously attached context.

    Args:
        token: The token returned from attach operation
    """
    _get_propagator().detach_context(token)
