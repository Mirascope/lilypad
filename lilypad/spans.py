"""A context manager for creating a tracing span with parent-child relationship tracking,"""

import datetime
import json
from contextlib import AbstractContextManager
from typing import Any

from opentelemetry import context as context_api
from opentelemetry.trace import Span as OTSpan
from opentelemetry.trace import StatusCode, get_tracer, set_span_in_context

from lilypad.server.client.schemas.v0 import SpanType

from .traces import span_order_context


class Span:
    """A context manager for creating a tracing span with parent-child relationship tracking."""

    def __init__(self, name: str) -> None:
        self.name: str = name
        self._span: OTSpan | None = None
        self._span_cm: AbstractContextManager[OTSpan] | None = None
        self._order_cm: AbstractContextManager[Any] | None = None
        self._finished: bool = False
        self._token = None

    def __enter__(self) -> "Span":
        tracer = get_tracer("lilypad")
        self._span = tracer.start_span(self.name)
        self._span.set_attribute("lilypad.type", SpanType.TRACE.value)

        self._current_context = context_api.get_current()
        ctx = set_span_in_context(self._span, self._current_context)
        # Activate our context
        self._token = context_api.attach(ctx)

        self._order_cm = span_order_context(self._span)
        self._order_cm.__enter__()

        self.metadata(
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat()
        )
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if exc_type is not None and self._span is not None and exc_val is not None:
            self._span.record_exception(exc_val)
        if self._order_cm is not None:
            self._order_cm.__exit__(exc_type, exc_val, exc_tb)

        if self._span is not None:
            self._span.end()

        if self._token:
            context_api.detach(self._token)

        self._finished = True

    async def __aenter__(self) -> "Span":
        return self.__enter__()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        self.__exit__(exc_type, exc_val, exc_tb)

    def _log_event(self, level: str, message: str, **kwargs: Any) -> None:
        if self._span is not None:
            attributes: dict[str, Any] = {
                f"{level}.message": message,
            }
            if level in ("error", "critical"):
                self._span.set_status(StatusCode.ERROR)
            attributes |= kwargs
            self._span.add_event(level, attributes=attributes)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        self._log_event("debug", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an informational message."""
        self._log_event("info", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Alias for the warning method."""
        self._log_event("warning", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Alias for the error method."""
        self._log_event("error", message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Alias for the critical method."""
        self._log_event("critical", message, **kwargs)

    def log(self, message: str, **kwargs: Any) -> None:
        """Alias for the info method."""
        self.info(message, **kwargs)

    def metadata(self, *args: Any, **kwargs: Any) -> None:
        """Enhance structured logging by setting metadata attributes.

        Accepts either a dictionary as the first argument or key-value pairs.
        Non-primitive values are automatically serialized to JSON.
        """
        if self._span is None:
            return
        if args and isinstance(args[0], dict):
            data: dict[str, Any] = args[0].copy()
            data |= kwargs
        else:
            data = kwargs

        for key, value in data.items():
            if not isinstance(value, str | int | float | bool) and value is not None:
                try:
                    value = json.dumps(value)
                except Exception:
                    value = str(value)
            self._span.set_attribute(key, value)

    def finish(self) -> None:
        """Explicitly finish the span if it has not been ended yet."""
        if not self._finished and self._span is not None:
            self._span.end()

            if self._token:
                context_api.detach(self._token)
            self._finished = True


def span(name: str) -> Span:
    """Convenience function to create a Span context manager."""
    return Span(name)
