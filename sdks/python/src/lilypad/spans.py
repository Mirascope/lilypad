"""Explicit span management for Lilypad SDK tracing."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


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
        self._is_noop = True
        self._span_id: str | None = None

    def __enter__(self) -> Span:
        """Enter the span context.

        Returns:
            This span instance for use within the context.
        """
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
        self.finish()

    def set(self, **attributes: Any) -> None:
        """Set attributes on the current span.

        Args:
            **attributes: Key-value pairs to set as span attributes.
        """
        raise NotImplementedError("Span.set not yet implemented")

    def event(self, name: str, **attributes: Any) -> None:
        """Record an event within the span.

        Args:
            name: Name of the event.
            **attributes: Event attributes as key-value pairs.
        """
        raise NotImplementedError("Span.event not yet implemented")

    def metadata(self, **attributes: Any) -> None:
        """Set metadata attributes on the span.

        Args:
            **attributes: Metadata key-value pairs.
        """
        raise NotImplementedError("Span.metadata not yet implemented")

    def debug(self, message: str, **fields: Any) -> None:
        """Log a debug message within the span.

        Args:
            message: Debug message text.
            **fields: Additional structured fields for the log entry.
        """
        raise NotImplementedError("Span.debug not yet implemented")

    def info(self, message: str, **fields: Any) -> None:
        """Log an info message within the span.

        Args:
            message: Info message text.
            **fields: Additional structured fields for the log entry.
        """
        raise NotImplementedError("Span.info not yet implemented")

    def warning(self, message: str, **fields: Any) -> None:
        """Log a warning message within the span.

        Args:
            message: Warning message text.
            **fields: Additional structured fields for the log entry.
        """
        raise NotImplementedError("Span.warning not yet implemented")

    def error(self, message: str, **fields: Any) -> None:
        """Log an error message within the span.

        Args:
            message: Error message text.
            **fields: Additional structured fields for the log entry.
        """
        raise NotImplementedError("Span.error not yet implemented")

    def critical(self, message: str, **fields: Any) -> None:
        """Log a critical message within the span.

        Args:
            message: Critical message text.
            **fields: Additional structured fields for the log entry.
        """
        raise NotImplementedError("Span.critical not yet implemented")

    def finish(self) -> None:
        """Explicitly finish the span."""
        raise NotImplementedError("Span.finish not yet implemented")

    @property
    def span_id(self) -> str | None:
        """Get the span ID if available.

        Returns:
            The span ID or None if not available.
        """
        return self._span_id

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
