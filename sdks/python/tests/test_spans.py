"""Comprehensive tests for spans.py module.

This file consolidates all spans-related tests to achieve 100% coverage.
Tests use pytest's functional style.
"""

from collections.abc import Generator
from contextlib import AbstractContextManager
from typing import Any
from unittest.mock import Mock, patch

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.trace import StatusCode

from lilypad._utils import json_dumps
from lilypad.sessions import SESSION_CONTEXT, session
from lilypad.spans import Span, span

dummy_spans: list["DummySpan"] = []


# =============================================================================
# Test Fixtures and Helpers
# =============================================================================


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
    """Dummy span that records its name, attributes, events, and end status."""

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
    class MockTracerProvider(TracerProvider):
        pass

    monkeypatch.setattr("lilypad.spans.get_tracer_provider", lambda: MockTracerProvider())


# =============================================================================
# Basic Functionality Tests
# =============================================================================


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


def test_span_initialization() -> None:
    """Test Span initialization."""
    s = Span("test-span")
    assert s.name == "test-span"
    assert s._span is None
    assert s._span_cm is None
    assert s._order_cm is None
    assert s._finished is False
    assert s._token is None
    assert s._noop is False
    assert s._span_id == 0


def test_span_span_id_property() -> None:
    """Test span_id property in different states."""
    s = Span("test")

    # When _noop is True
    s._noop = True
    s._span_id = 12345
    assert s.span_id == 12345

    # When _noop is False and _span is None
    s._noop = False
    s._span = None
    assert s.span_id == 0

    # When _noop is False and _span exists
    mock_span = Mock()
    mock_span.get_span_context.return_value.span_id = 67890
    s._span = mock_span
    assert s.span_id == 67890


def test_span_opentelemetry_span_property() -> None:
    """Test opentelemetry_span property."""
    s = Span("test")

    # When _noop is True
    s._noop = True
    assert s.opentelemetry_span is None

    # When _noop is False
    s._noop = False
    mock_span = Mock()
    s._span = mock_span
    assert s.opentelemetry_span == mock_span


# =============================================================================
# Exception and Error Handling Tests
# =============================================================================


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


def test_unconfigured_lilypad(monkeypatch) -> None:
    """Test span behavior when Lilypad is not configured."""
    # Reset the warning flag to ensure the warning is logged
    Span._warned_not_configured = False

    # Patch get_tracer_provider to return something that's not a TracerProvider
    monkeypatch.setattr("lilypad.spans.get_tracer_provider", lambda: object())

    # Mock the logger to verify warning is logged
    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Create a span and verify it's a no-op
        with span("unconfigured test") as s:
            s.info("this should be ignored")
            s.metadata(test="value")

            # Test span_id and opentelemetry_span properties with _noop=True
            assert s.span_id == 0
            assert s.opentelemetry_span is None

        # Verify warning was logged
        mock_logger.warning.assert_called_once()
        warning_message = mock_logger.warning.call_args[0][0]
        warning_args = mock_logger.warning.call_args[0]
        assert "Lilypad has not been configured" in warning_message
        # The span name is passed as a parameter, not in the message
        assert len(warning_args) > 1
        assert warning_args[1] == "unconfigured test"

    # The span should be a no-op, so no dummy spans should be created
    assert len(dummy_spans) == 0


def test_multiple_unconfigured_spans(monkeypatch) -> None:
    """Test that warning is only logged once for unconfigured Lilypad."""
    # Reset the warning flag
    Span._warned_not_configured = False

    # Patch get_tracer_provider to return non-TracerProvider
    monkeypatch.setattr("lilypad.spans.get_tracer_provider", lambda: object())

    with patch("logging.getLogger") as mock_get_logger:
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        # Create multiple spans
        with span("first") as s1:
            pass

        with span("second") as s2:
            pass

        # Warning should only be logged once
        assert mock_logger.warning.call_count == 1


# =============================================================================
# Async Context Manager Tests
# =============================================================================


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


@pytest.mark.asyncio
async def test_async_span_context_manager() -> None:
    """Test async context manager methods directly."""
    async with span("async context manager test") as s:
        # This should hit both __aenter__ and __aexit__
        s.info("Testing async context manager")
        assert s.name == "async context manager test"

    # Verify the span was created and finished properly
    assert len(dummy_spans) == 1
    dummy = dummy_spans[0]
    assert dummy.ended is True


@pytest.mark.asyncio
async def test_async_span_with_exception() -> None:
    """Test async span with exception."""
    try:
        async with span("async exception span") as s:
            s.info("before async exception")
            raise RuntimeError("async error")
    except RuntimeError:
        pass

    assert len(dummy_spans) == 1
    dummy = dummy_spans[0]
    exception_events = [e for e in dummy.events if e[0] == "exception"]
    assert len(exception_events) == 1


# =============================================================================
# Logging Tests
# =============================================================================


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


def test_error_and_critical_set_status() -> None:
    """Test that error and critical logs set error status."""
    with span("error status test") as s:
        s.error("Error occurred")
        s.critical("Critical error")

    # Get the actual span
    assert s._span is not None
    # Check that StatusCode.ERROR was set
    # Since we're using DummySpan, we need to check the status was set
    assert dummy_spans[0].status == StatusCode.ERROR


# =============================================================================
# Metadata Tests
# =============================================================================


def test_metadata_serialization() -> None:
    """Test that metadata() correctly serializes non-primitive values."""
    data = {"list": [1, 2, 3], "dict": {"a": 1}}
    with span("metadata test") as s:
        s.metadata(data)

    dummy = dummy_spans[0]
    assert dummy.attributes.get("list") == json_dumps([1, 2, 3])
    assert dummy.attributes.get("dict") == json_dumps({"a": 1})


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


def test_metadata_variations() -> None:
    """Test metadata method with various input combinations."""
    with span("metadata variations") as s:
        # Test with dict as first positional arg
        s.metadata({"key1": "value1"}, key2="value2")

        # Test with non-dict positional args
        s.metadata("arg1", "arg2", key3="value3")

        # Test with only kwargs
        s.metadata(key4="value4")

        # Test with empty call
        s.metadata()

    dummy = dummy_spans[0]

    # Check dict merge
    assert dummy.attributes.get("key1") == "value1"
    assert dummy.attributes.get("key2") == "value2"

    # Check positional args were serialized
    assert "lilypad.metadata" in dummy.attributes

    # Check kwargs only
    assert dummy.attributes.get("key4") == "value4"


def test_metadata_none_values() -> None:
    """Test metadata with None values."""
    with span("metadata none test") as s:
        s.metadata(none_value=None, string_value="test")

    dummy = dummy_spans[0]
    # None values should be set as-is
    assert dummy.attributes.get("none_value") is None
    assert dummy.attributes.get("string_value") == "test"


def test_metadata_serialization_fallback() -> None:
    """Test metadata falls back to str() when JSON serialization fails."""

    class CustomObject:
        def __repr__(self):
            return "CustomObject representation"

    with patch("lilypad.spans.json_dumps", side_effect=Exception("JSON error")), span("metadata fallback test") as s:
        s.metadata(custom=CustomObject())

    dummy = dummy_spans[0]
    assert dummy.attributes.get("custom") == "CustomObject representation"


# =============================================================================
# Session Context Tests
# =============================================================================


def test_span_with_session_context() -> None:
    """Test span creation within a session context."""
    with session("test-session-id") as sess, span("session test") as s:
        # The span should have the session_id attribute set
        pass

    # Verify the session ID was set on the span
    assert len(dummy_spans) == 1
    dummy = dummy_spans[0]
    assert dummy.attributes.get("lilypad.session_id") == "test-session-id"


def test_span_without_session_context() -> None:
    """Test span creation without a session context."""
    # Ensure no session is set
    SESSION_CONTEXT.set(None)

    with span("no session test") as s:
        pass

    # Verify no session_id attribute was set
    assert len(dummy_spans) == 1
    dummy = dummy_spans[0]
    assert "lilypad.session_id" not in dummy.attributes


def test_span_with_session_no_id() -> None:
    """Test span with session that has no ID."""
    # Create a session with no ID
    mock_session = Mock()
    mock_session.id = None

    SESSION_CONTEXT.set(mock_session)
    try:
        with span("session no id test") as s:
            pass

        # Verify no session_id attribute was set
        assert len(dummy_spans) == 1
        dummy = dummy_spans[0]
        assert "lilypad.session_id" not in dummy.attributes
    finally:
        SESSION_CONTEXT.set(None)


# =============================================================================
# Finish Method Tests
# =============================================================================


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


def test_finish_when_already_finished() -> None:
    """Test finish method when span is already finished."""
    s = Span("already finished")
    s._finished = True
    s._span = Mock()
    s._token = Mock()

    # Call finish - should return early
    s.finish()

    # Verify end() was not called
    s._span.end.assert_not_called()


def test_finish_with_token() -> None:
    """Test finish method properly detaches context token."""
    with patch("lilypad.spans.context_api") as mock_context_api:
        s = Span("finish with token")
        s._span = Mock()
        s._token = "test-token"
        s._finished = False

        s.finish()

        # Verify token was detached
        mock_context_api.detach.assert_called_once_with("test-token")
        assert s._finished is True


# =============================================================================
# Context and Exit Behavior Tests
# =============================================================================


def test_span_exit_with_exception() -> None:
    """Test span __exit__ with exception recording."""
    # Directly test __exit__ behavior
    s = Span("exit test")
    s._noop = False
    s._span = Mock()
    s._token = "test-token"

    with patch("lilypad.spans.context_api") as mock_context_api:
        # Simulate exception in __exit__
        exc_type = ValueError
        exc_val = ValueError("test error")
        exc_tb = None

        s.__exit__(exc_type, exc_val, exc_tb)

        # Verify exception was recorded
        s._span.record_exception.assert_called_once_with(exc_val)
        s._span.end.assert_called_once()
        mock_context_api.detach.assert_called_once_with("test-token")
        assert s._finished is True


def test_span_exit_without_exception() -> None:
    """Test normal span exit without exception."""
    s = Span("normal exit")
    s._noop = False
    s._span = Mock()
    s._token = "test-token"

    with patch("lilypad.spans.context_api") as mock_context_api:
        s.__exit__(None, None, None)

        # Verify no exception was recorded
        s._span.record_exception.assert_not_called()
        s._span.end.assert_called_once()
        mock_context_api.detach.assert_called_once_with("test-token")


def test_span_exit_in_noop_mode() -> None:
    """Test span exit in noop mode."""
    s = Span("noop exit")
    s._noop = True
    s._span = Mock()

    s.__exit__(None, None, None)

    # In noop mode, nothing should happen
    s._span.record_exception.assert_not_called()
    s._span.end.assert_not_called()


# =============================================================================
# Direct Method Tests
# =============================================================================


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


def test_span_context_activation() -> None:
    """Test span context activation and token attachment."""
    with (
        patch("lilypad.spans.get_tracer") as mock_get_tracer,
        patch("lilypad.spans.context_api") as mock_context_api,
        patch("lilypad.spans.set_span_in_context") as mock_set_span,
    ):
        # Setup mocks
        mock_otel_span = Mock()
        mock_tracer = Mock()
        mock_tracer.start_span.return_value = mock_otel_span
        mock_get_tracer.return_value = mock_tracer

        mock_context = Mock()
        mock_context_api.get_current.return_value = mock_context

        new_context = Mock()
        mock_set_span.return_value = new_context

        mock_token = "test-token"
        mock_context_api.attach.return_value = mock_token

        # Create and enter span
        s = Span("context test")
        s.__enter__()

        # Verify context operations
        mock_context_api.get_current.assert_called_once()
        mock_set_span.assert_called_once_with(mock_otel_span, mock_context)
        mock_context_api.attach.assert_called_once_with(new_context)
        assert s._token == mock_token


# =============================================================================
# Edge Cases and Coverage Tests
# =============================================================================


def test_log_event_with_empty_message() -> None:
    """Test _log_event with empty message."""
    with span("empty message test") as s:
        s.info("")
        s.error("")

    dummy = dummy_spans[0]
    info_events = [e for e in dummy.events if e[0] == "info"]
    error_events = [e for e in dummy.events if e[0] == "error"]

    assert len(info_events) == 1
    assert len(error_events) == 1


def test_metadata_with_positional_args_exception() -> None:
    """Test metadata with positional args that cause JSON serialization error."""

    class BadJson:
        def __repr__(self):
            return "BadJson"

    with patch("lilypad.spans.json_dumps", side_effect=Exception("JSON error")), span("metadata args exception") as s:
        s.metadata(BadJson(), another=BadJson())

    dummy = dummy_spans[0]
    # Should fallback to str() representation
    assert "lilypad.metadata" in dummy.attributes
    assert dummy.attributes.get("another") == "BadJson"


def test_span_creation_with_real_tracer_provider() -> None:
    """Test span creation with real TracerProvider to increase coverage."""
    # This test ensures we cover the actual OpenTelemetry span creation path
    from opentelemetry.sdk.trace import TracerProvider as RealTracerProvider
    from opentelemetry.trace import get_tracer as real_get_tracer

    # Set up a real tracer provider
    provider = RealTracerProvider()

    def mock_get_tracer(name, **kwargs):
        # Pass the provider to real_get_tracer
        return real_get_tracer(name, tracer_provider=provider)

    with (
        patch("lilypad.spans.get_tracer_provider", return_value=provider),
        patch("lilypad.spans.get_tracer", side_effect=mock_get_tracer),
        span("real tracer test") as s,
    ):
        s.info("Using real tracer")
        assert s._span is not None
        assert s._noop is False


def test_span_type_attribute() -> None:
    """Test that span sets lilypad.type attribute."""
    with span("type attribute test") as s:
        pass

    dummy = dummy_spans[0]
    assert dummy.attributes.get("lilypad.type") == "trace"


def test_span_nonrecording_span_warning() -> None:
    """Test span behavior when NonRecordingSpan is returned (lines 48-57)."""
    # Reset the warning flag
    Span._warned_not_configured = False

    # Create a mock NonRecordingSpan
    class NonRecordingSpan:
        """Mock NonRecordingSpan class."""

        pass

    mock_nonrecording_span = NonRecordingSpan()

    # Mock get_tracer to return our NonRecordingSpan
    with patch("lilypad.spans.get_tracer") as mock_get_tracer:
        mock_get_tracer.return_value.start_span.return_value = mock_nonrecording_span

        # Capture log output
        with patch("lilypad.spans.logging.getLogger") as mock_get_logger:
            mock_logger = Mock()
            mock_get_logger.return_value = mock_logger

            # Create span
            with span("test span") as s:
                # Verify it's marked as noop
                assert s._noop is True
                assert s._span is None

                # Verify warning was logged
                mock_logger.warning.assert_called_once()
                warning_msg = mock_logger.warning.call_args[0][0]
                assert "Lilypad has not been configured" in warning_msg
                assert "Tracing is disabled" in warning_msg
                assert "test span" in mock_logger.warning.call_args[0][1]

                # Verify the flag was set
                assert Span._warned_not_configured is True

            # Create another span - should not log warning again
            mock_logger.warning.reset_mock()
            with span("another test span") as s2:
                assert s2._noop is True
                assert s2._span is None
                # Should not log warning again
                mock_logger.warning.assert_not_called()

    # Reset the flag
    Span._warned_not_configured = False
