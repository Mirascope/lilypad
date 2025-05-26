"""Unit tests for the span() context manager and related functionality."""

from typing import Any
from contextlib import AbstractContextManager
from collections.abc import Generator

import pytest

from lilypad.lib.spans import span
from lilypad.lib._utils import json_dumps

dummy_spans: list["DummySpan"] = []


class DummySpanContext:
    """A dummy span context with fixed trace_id and span_id."""

    @property
    def trace_id(self) -> int:
        """Return a fixed trace ID."""
        return 1234567890

    @property
    def span_id(self) -> int:
        """Return a fixed span ID."""
        return 9876543210


class DummySpan:
    """Dummy span that records its name, attributes, events, and end status.

    The __exit__ method is modified to call end() so that the span is properly finished.
    """

    def __init__(self, name: str) -> None:
        self.name: str = name
        self.status: str = "UNSET"
        self.attributes: dict[str, Any] = {}
        self.events: list[tuple[str, dict[str, Any]]] = []
        self.ended: bool = False
        self.parent: "DummySpan" | None = None
        dummy_spans.append(self)

    def set_attribute(self, key: str, value: Any) -> None:
        """Set a single attribute on the span."""
        self.attributes[key] = value

    def add_event(self, event_name: str, attributes: dict[str, Any]) -> None:
        """Record an event with the given name and attributes."""
        self.events.append((event_name, attributes))

    def get_span_context(self) -> DummySpanContext:
        """Return a dummy span context."""
        return DummySpanContext()

    def set_status(self, status: Any) -> None:
        """Set the status of the span."""
        self.status = status

    def record_exception(self, exc: BaseException) -> None:
        """Record an exception event."""
        self.add_event(
            "exception",
            {
                "exception.type": str(exc),
                "exception.message": str(exc),
                "exception.stacktrace": str(exc),
            },
        )

    def end(self) -> None:
        """Mark the span as finished."""
        self.ended = True

    def __enter__(self) -> "DummySpan":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        tb: Any,
    ) -> None:
        self.end()


class DummyTracer:
    """Dummy tracer that returns DummySpan instances."""

    def start_span(self, name: str) -> AbstractContextManager[DummySpan]:
        """Return a dummy span context manager."""
        return DummySpan(name)


@pytest.fixture(autouse=True)
def reset_dummy_spans() -> Generator[None, None, None]:
    """Reset the dummy_spans list before and after each test."""
    dummy_spans.clear()
    yield
    dummy_spans.clear()


@pytest.fixture(autouse=True)
def patch_get_tracer(monkeypatch) -> None:
    """Patch get_tracer to return a DummyTracer instance."""
    monkeypatch.setattr("lilypad.lib.spans.get_tracer", lambda _: DummyTracer())


def test_basic_sync_span() -> None:
    """Test basic synchronous span creation, logging, and metadata."""
    with span("test span") as s:
        s.info("hello", foo="bar")
        s.debug("debug message", count=1)
        s.metadata({"custom": {"nested": [1, 2, 3]}})
    assert len(dummy_spans) == 1
    dummy = dummy_spans[0]
    assert "timestamp" in dummy.attributes
    info_events = [e for e in dummy.events if e[0] == "info"]
    debug_events = [e for e in dummy.events if e[0] == "debug"]
    assert any("hello" in event[1].get(f"{event[0]}.message", "") for event in info_events)
    assert any("debug message" in event[1].get(f"{event[0]}.message", "") for event in debug_events)
    custom_value = dummy.attributes.get("custom")
    assert custom_value == '{"nested":[1,2,3]}'
    s.finish()
    assert dummy.ended is True


def test_exception_captures_stacktrace() -> None:
    """Test that an exception within a span is captured with its stack trace."""
    try:
        with span("exception span") as s:
            s.info("before exception")
            raise ValueError("test error")
    except ValueError:
        pass
    assert len(dummy_spans) == 1
    dummy = dummy_spans[0]
    exception_events = [e for e in dummy.events if e[0] == "exception"]
    assert len(exception_events) == 1
    attrs = exception_events[0][1]
    assert "exception.type" in attrs
    assert "exception.message" in attrs
    assert "exception.stacktrace" in attrs


@pytest.mark.asyncio
async def test_async_span() -> None:
    """Test asynchronous span creation and metadata."""
    async with span("async span") as s:
        s.warning("async warning", code=100)
        s.metadata(**{"async": True})
    assert len(dummy_spans) == 1
    dummy = dummy_spans[0]
    warning_events = [e for e in dummy.events if e[0] == "warning"]
    assert len(warning_events) == 1
    assert dummy.attributes.get("async") is True


def test_logging_levels() -> None:
    """Test that logging at various levels is recorded correctly."""
    with span("log levels") as s:
        s.debug("debugging", value=10)
        s.info("information", status="ok")
        s.warning("warning", risk="high")
        s.error("error occurred", error_code=500)
        s.critical("critical error", critical_flag=True)
        s.log("legacy log", legacy=True)
    dummy = dummy_spans[0]
    levels = {lvl for lvl, _ in dummy.events}
    for expected in ["debug", "info", "warning", "error", "critical"]:
        assert expected in levels
    info_events = [e for e in dummy.events if e[0] == "info"]
    assert any(e[1].get("legacy") is True for e in info_events)


def test_metadata_serialization() -> None:
    """Test that metadata() correctly serializes non-primitive values."""
    data = {"list": [1, 2, 3], "dict": {"a": 1}}
    with span("metadata test") as s:
        s.metadata(data)
    dummy = dummy_spans[0]
    assert dummy.attributes.get("list") == json_dumps([1, 2, 3])
    assert dummy.attributes.get("dict") == json_dumps({"a": 1})


def test_dummy_span_record_exception_directly() -> None:
    """Test that DummySpan.record_exception records an exception event correctly when called directly."""
    span_instance = DummySpan("direct exception test")
    dummy_exception = ValueError("direct test error")
    span_instance.record_exception(dummy_exception)

    exception_events = [event for event in span_instance.events if event[0] == "exception"]
    assert len(exception_events) == 1

    attrs = exception_events[0][1]
    assert attrs["exception.type"] == str(dummy_exception)
    assert attrs["exception.message"] == str(dummy_exception)
    assert attrs["exception.stacktrace"] == str(dummy_exception)
