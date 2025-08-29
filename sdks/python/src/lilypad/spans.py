"""Explicit span management for Lilypad SDK tracing."""

from __future__ import annotations

import logging
from typing import Any, Protocol, runtime_checkable

from opentelemetry import context as otel_context
from opentelemetry import trace as otel_trace
from opentelemetry.trace import Status, StatusCode

logger = logging.getLogger("lilypad")
_warned_noop = False


@runtime_checkable
class SpanProtocol(Protocol):
    """Protocol defining the interface for trace spans.

    Provides methods for setting attributes, logging events, and managing
    span lifecycle within a trace context.
    """

    def set(self, **attributes: Any) -> None:
        """Set attributes on the current span.

        Args:
            **attributes: Key-value pairs to set as span attributes.
        """
        ...

    def event(self, name: str, **attributes: Any) -> None:
        """Record an event within the span.

        Args:
            name: Name of the event.
            **attributes: Event attributes as key-value pairs.
        """
        ...

    def metadata(self, **attributes: Any) -> None:
        """Set metadata attributes on the span.

        Args:
            **attributes: Metadata key-value pairs.
        """
        ...

    def debug(self, message: str, **fields: Any) -> None:
        """Log a debug message within the span.

        Args:
            message: Debug message text.
            **fields: Additional structured fields for the log entry.
        """
        ...

    def info(self, message: str, **fields: Any) -> None:
        """Log an info message within the span.

        Args:
            message: Info message text.
            **fields: Additional structured fields for the log entry.
        """
        ...

    def warning(self, message: str, **fields: Any) -> None:
        """Log a warning message within the span.

        Args:
            message: Warning message text.
            **fields: Additional structured fields for the log entry.
        """
        ...

    def error(self, message: str, **fields: Any) -> None:
        """Log an error message within the span.

        Args:
            message: Error message text.
            **fields: Additional structured fields for the log entry.
        """
        ...

    def critical(self, message: str, **fields: Any) -> None:
        """Log a critical message within the span.

        Args:
            message: Critical message text.
            **fields: Additional structured fields for the log entry.
        """
        ...

    def finish(self) -> None:
        """Explicitly finish the span."""
        ...

    @property
    def span_id(self) -> str | None:
        """Get the span ID if available."""
        ...

    @property
    def is_noop(self) -> bool:
        """Check if this is a no-op span (tracing disabled)."""
        ...


class Span(SpanProtocol):
    """Context-managed span for explicit tracing.

    Creates a child span within the current trace context. Acts as a no-op
    if tracing is not configured.
    """

    def __init__(self, name: str) -> None:
        """Initialize a new span with the given name.

        Args:
            name: Name for the span.
        """
        self._name = name
        self._span: otel_trace.Span | None = None
        self._token: object | None = None
        self._is_noop = True
        self._finished = False

    def __enter__(self) -> Span:
        """Enter the span context.

        Returns:
            This span instance for use within the context.
        """
        tracer = otel_trace.get_tracer("lilypad")
        self._span = tracer.start_span(self._name)

        if self._span.__class__.__name__ == "NonRecordingSpan":
            self._is_noop = True
            self._span = None
            global _warned_noop
            if not _warned_noop:
                logger.warning(
                    f"Lilypad tracing is not configured; Span('{self._name}') is a no-op."
                )
                _warned_noop = True
        else:
            self._is_noop = False
            self._span.set_attribute("lilypad.type", "trace")
            self._token = otel_context.attach(
                otel_trace.set_span_in_context(self._span)
            )

        return self

    def __exit__(
        self, exc_type: type[BaseException] | None, exc: BaseException | None, tb: Any
    ) -> None:
        """Exit the span context.

        Args:
            exc_type: Exception type if an exception was raised.
            exc: Exception instance if an exception was raised.
            tb: Traceback if an exception was raised.
        """
        if self._span and not self._finished:
            if exc is not None:
                self._span.record_exception(exc)
                self._span.set_status(Status(StatusCode.ERROR))
            self.finish()

    def set(self, **attributes: Any) -> None:
        """Set attributes on the current span.

        Args:
            **attributes: Key-value pairs to set as span attributes.
        """
        if self._span and not self._finished:
            import json

            for key, value in attributes.items():
                if isinstance(value, (dict, list)):
                    self._span.set_attribute(key, json.dumps(value))
                else:
                    self._span.set_attribute(key, value)

    def event(self, name: str, **attributes: Any) -> None:
        """Record an event within the span.

        Args:
            name: Name of the event.
            **attributes: Event attributes as key-value pairs.
        """
        if self._span and not self._finished:
            import json

            serialized_attrs = {}
            for key, value in attributes.items():
                if isinstance(value, (dict, list)):
                    serialized_attrs[key] = json.dumps(value)
                else:
                    serialized_attrs[key] = value
            self._span.add_event(name, attributes=serialized_attrs)

    def metadata(self, **attributes: Any) -> None:
        """Set metadata attributes on the span.

        Args:
            **attributes: Metadata key-value pairs.
        """
        self.set(**attributes)

    def debug(self, message: str, **fields: Any) -> None:
        """Log a debug message within the span.

        Args:
            message: Debug message text.
            **fields: Additional structured fields for the log entry.
        """
        attrs = {"message": message, "level": "debug", **fields}
        self.event("debug", **attrs)

    def info(self, message: str, **fields: Any) -> None:
        """Log an info message within the span.

        Args:
            message: Info message text.
            **fields: Additional structured fields for the log entry.
        """
        attrs = {"message": message, "level": "info", **fields}
        self.event("info", **attrs)

    def warning(self, message: str, **fields: Any) -> None:
        """Log a warning message within the span.

        Args:
            message: Warning message text.
            **fields: Additional structured fields for the log entry.
        """
        attrs = {"message": message, "level": "warning", **fields}
        self.event("warning", **attrs)

    def error(self, message: str, **fields: Any) -> None:
        """Log an error message within the span.

        Args:
            message: Error message text.
            **fields: Additional structured fields for the log entry.
        """
        attrs = {"message": message, "level": "error", **fields}
        self.event("error", **attrs)
        if self._span and not self._finished:
            self._span.set_status(Status(StatusCode.ERROR))

    def critical(self, message: str, **fields: Any) -> None:
        """Log a critical message within the span.

        Args:
            message: Critical message text.
            **fields: Additional structured fields for the log entry.
        """
        attrs = {"message": message, "level": "critical", **fields}
        self.event("critical", **attrs)
        if self._span and not self._finished:
            self._span.set_status(Status(StatusCode.ERROR))

    def finish(self) -> None:
        """Explicitly finish the span."""
        if not self._finished:
            self._finished = True
            if self._span:
                self._span.end()
            if self._token:
                otel_context.detach(self._token)
                self._token = None

    @property
    def span_id(self) -> str | None:
        """Get the span ID if available.

        Returns:
            The span ID or None if not available.
        """
        if self._span:
            sc = self._span.get_span_context()
            if sc and sc.span_id:
                return f"{sc.span_id:016x}"
        return None

    @property
    def is_noop(self) -> bool:
        """Check if this is a no-op span.

        Returns:
            True if tracing is disabled, False otherwise.
        """
        return self._is_noop


def span(name: str) -> Span:
    """Create a new span context manager.

    Args:
        name: Name for the new span.

    Returns:
        A Span context manager that creates a child span when entered.
    """
    return Span(name)
