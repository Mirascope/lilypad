"""Utility functions for OpenTelemetry exporters.

This module provides helper functions for formatting and converting
OpenTelemetry data types for export.
"""


def format_trace_id(trace_id: int) -> str:
    """Format a trace ID as a 32-character hex string.

    Args:
        trace_id: The trace ID as an integer.

    Returns:
        Formatted trace ID as hex string.
    """
    return format(trace_id, "032x")


def format_span_id(span_id: int) -> str:
    """Format a span ID as a 16-character hex string.

    Args:
        span_id: The span ID as an integer.

    Returns:
        Formatted span ID as hex string.
    """
    return format(span_id, "016x")
