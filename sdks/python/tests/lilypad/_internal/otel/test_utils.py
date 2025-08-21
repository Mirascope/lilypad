"""Common test utilities for OpenTelemetry instrumentation tests."""

from typing import Any

from opentelemetry.sdk.trace import ReadableSpan


def extract_span_data(span: ReadableSpan) -> dict[str, Any]:
    """Extract serializable data from a span for snapshot testing.

    Args:
        span: The span to extract data from

    Returns:
        Dictionary containing span name, attributes, status, and events
    """
    return {
        "name": span.name,
        "attributes": dict(span.attributes) if span.attributes else {},
        "status": {
            "status_code": span.status.status_code.name,
            "description": span.status.description,
        },
        "events": [
            {
                "name": event.name,
                "attributes": dict(event.attributes) if event.attributes else {},
            }
            for event in span.events
        ],
    }
