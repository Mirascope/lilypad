"""A context manager for creating a tracing span with parent-child relationship tracking,"""

import time
import logging
import datetime
from typing import Any
from functools import lru_cache  # noqa: TID251
from contextlib import AbstractContextManager, suppress
from contextvars import ContextVar

from opentelemetry import context as context_api
from opentelemetry.trace import Span as OTSpan, StatusCode, get_tracer, get_tracer_provider, set_span_in_context
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from ..lib.sessions import SESSION_CONTEXT
from ..lib._utils.json import json_dumps

_trace_level: ContextVar[int] = ContextVar("_trace_level", default=0)


@lru_cache(maxsize=1)
def get_batch_span_processor() -> BatchSpanProcessor | None:
    """Get the BatchSpanProcessor from the current TracerProvider.

    Retrieve the BatchSpanProcessor from the current TracerProvider dynamically.
    This avoids using a global variable by inspecting the provider's _active_span_processors.
    """
    tracer_provider = get_tracer_provider()
    if hasattr(tracer_provider, "get_active_span_processor"):
        active_processor = tracer_provider.get_active_span_processor()
        if hasattr(active_processor, "_span_processors"):
            for processor in active_processor._span_processors:
                if isinstance(processor, BatchSpanProcessor):
                    return processor
        elif isinstance(active_processor, BatchSpanProcessor):
            return active_processor
    elif hasattr(tracer_provider, "_active_span_processor"):
        processor = getattr(tracer_provider, "_active_span_processor", None)
        if isinstance(processor, BatchSpanProcessor):
            return processor
        elif hasattr(processor, "_span_processors"):
            for span_processors in processor._span_processors:
                if isinstance(span_processors, BatchSpanProcessor):
                    return span_processors
    return None


class Span:
    """A context manager for creating a tracing span with parent-child relationship tracking."""

    _warned_not_configured: bool = False

    def __init__(self, name: str) -> None:
        self.name: str = name
        self._span: OTSpan | None = None
        self._span_cm: AbstractContextManager[OTSpan] | None = None
        self._order_cm: AbstractContextManager[Any] | None = None
        self._finished: bool = False
        self._token = None
        self._noop: bool = False
        self._span_id: int = 0

    def __enter__(self) -> "Span":
        if not isinstance(get_tracer_provider(), TracerProvider):
            if not Span._warned_not_configured:
                logging.getLogger("lilypad").warning(
                    "Lilypad has not been configured. Tracing is disabled "
                    "for span '%s'. Call `lilypad.configure(...)` early in program start-up.",
                    self.name,
                )
                Span._warned_not_configured = True
            self._noop = True
            return self

        tracer = get_tracer("lilypad")
        self._span: OTSpan = tracer.start_span(self.name)
        self._span.set_attribute("lilypad.type", "trace")

        current_session = SESSION_CONTEXT.get()
        if current_session and current_session.id is not None:
            self._span.set_attribute("lilypad.session_id", current_session.id)
        self._is_root = self._span.parent is None
        self._condition = None
        self._lock_acquired = False

        if self._is_root:  # Lock when span is root
            proc = get_batch_span_processor()
            if proc and hasattr(proc, "condition"):
                condition = proc.condition
                try:
                    condition.acquire()
                    self._condition = condition
                    self._lock_acquired = True
                except RuntimeError:
                    pass

        self._current_context = context_api.get_current()
        ctx = set_span_in_context(self._span, self._current_context)
        # Activate our context
        self._token = context_api.attach(ctx)

        self.metadata(timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat())
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        if self._noop:
            return
        if exc_type is not None and self._span is not None and exc_val is not None:
            self._span.record_exception(exc_val)

        if self._span is not None:
            self._span.end()

        if self._is_root:
            if self._lock_acquired and self._condition:
                with suppress(RuntimeError):
                    self._condition.release()
                self._lock_acquired = False

            if (proc := get_batch_span_processor()) is not None:
                for _ in range(3):  # max 3 tries
                    if proc.force_flush(timeout_millis=5_000):
                        break
                    time.sleep(0.05)

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
                    value = json_dumps(value)
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

    @property
    def span_id(self) -> int:
        """Return the span ID."""
        return self._span_id if self._noop else self._span.get_span_context().span_id

    @property
    def opentelemetry_span(self) -> OTSpan | None:
        """Return the underlying OpenTelemetry span."""
        return None if self._noop else self._span


def span(name: str) -> Span:
    """Convenience function to create a Span context manager."""
    return Span(name)
