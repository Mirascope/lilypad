"""Unit tests for the span() context manager and related functionality."""

from typing import Any
from contextlib import AbstractContextManager
from collections.abc import Generator
from unittest.mock import Mock

import pytest

from lilypad.spans import span, Span
from lilypad._utils import json_dumps
from lilypad.sessions import session

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
    monkeypatch.setattr("lilypad.spans.get_tracer", lambda _: DummyTracer())
    # Also patch get_tracer_provider to return a real TracerProvider instance
    from opentelemetry.sdk.trace import TracerProvider

    class MockTracerProvider(TracerProvider):
        pass

    monkeypatch.setattr("lilypad.spans.get_tracer_provider", lambda: MockTracerProvider())


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


def test_unconfigured_lilypad(monkeypatch) -> None:
    """Test span behavior when Lilypad is not configured."""
    # Reset the warning flag to ensure the warning is logged
    Span._warned_not_configured = False

    # Patch get_tracer_provider to return something that's not a TracerProvider
    monkeypatch.setattr("lilypad.spans.get_tracer_provider", lambda: object())

    # Create a span and verify it's a no-op
    with span("unconfigured test") as s:
        s.info("this should be ignored")
        s.metadata(test="value")

        # Test span_id and opentelemetry_span properties with _noop=True
        assert s.span_id == 0
        assert s.opentelemetry_span is None

    # The span should be a no-op, so no dummy spans should be created
    assert len(dummy_spans) == 0


def test_metadata_with_none_span() -> None:
    """Test metadata method when _span is None."""
    s = Span("test")
    # Don't enter the context manager, so _span remains None
    s.metadata(test="value")
    # No assertion needed, just verifying it doesn't raise an exception


def test_metadata_serialization_exception(monkeypatch) -> None:
    """Test exception handling in metadata serialization."""

    # Create a class that raises an exception when json_dumps is called
    class UnserializableObject:
        def __repr__(self) -> str:
            return "UnserializableObject()"

    # Patch json_dumps to raise an exception
    def mock_json_dumps(obj):
        if isinstance(obj, UnserializableObject):
            raise TypeError("Cannot serialize UnserializableObject")
        return json_dumps(obj)

    monkeypatch.setattr("lilypad.spans.json_dumps", mock_json_dumps)

    # Create a span and add metadata with the unserializable object
    with span("metadata exception test") as s:
        s.metadata(unserializable=UnserializableObject())

    # Verify the metadata was added as a string representation
    assert len(dummy_spans) == 1
    dummy = dummy_spans[0]
    assert dummy.attributes.get("unserializable") == "UnserializableObject()"


def test_finish_method() -> None:
    """Test the finish method directly."""
    # Create a span without using the context manager
    s = Span("finish test")
    s._span = DummySpan("finish test")
    s._token = "mock_token"
    s._finished = False

    # Call finish
    s.finish()

    # Verify the span was ended
    assert s._span.ended is True
    assert s._finished is True

    # Call finish again (should be a no-op)
    s.finish()

    # Still just one end call
    assert s._span.ended is True


def test_span_with_session_context() -> None:
    """Test span creation within a session context (line 49)."""
    with session("test-session-id") as sess:
        with span("session test") as s:
            # The span should have the session_id attribute set
            pass
    
    # Verify the session ID was set on the span
    assert len(dummy_spans) == 1
    dummy = dummy_spans[0]
    assert dummy.attributes.get("lilypad.session_id") == "test-session-id"


def test_span_opentelemetry_span_with_span():
    """Test opentelemetry_span property when _span is not None (line 81)."""
    test_span = Span("test")
    
    # Directly set _span to mock object to test the property
    mock_otel_span = Mock()
    test_span._span = mock_otel_span
    
    # Now opentelemetry_span should return the mock span
    result = test_span.opentelemetry_span
    assert result == mock_otel_span


def test_span_span_id_with_span():
    """Test span_id property when _span is not None (line 89)."""
    test_span = Span("test")
    
    # Directly set _span to mock object to test the property
    mock_otel_span = Mock()
    mock_otel_span.get_span_context.return_value.span_id = 12345
    test_span._span = mock_otel_span
    
    # Now span_id should return the actual span ID from the mock
    result = test_span.span_id
    assert result == 12345


@pytest.mark.asyncio
async def test_async_span_context_manager():
    """Test async context manager methods directly (lines 81, 89)."""
    async with span("async context manager test") as s:
        # This should hit both __aenter__ (line 81) and __aexit__ (line 89)
        s.info("Testing async context manager")
        assert s.name == "async context manager test"
    
    # Verify the span was created and finished properly
    assert len(dummy_spans) == 1
    dummy = dummy_spans[0]
    assert dummy.ended is True
