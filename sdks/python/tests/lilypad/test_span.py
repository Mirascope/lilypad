"""Tests for Span explicit tracing functionality."""

from __future__ import annotations

from typing import Generator

import pytest
from inline_snapshot import snapshot
from opentelemetry import trace as otel_trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import ProxyTracerProvider

from lilypad.spans import Span, span
import lilypad.spans


@pytest.fixture
def span_exporter() -> Generator[InMemorySpanExporter, None, None]:
    """Set up InMemorySpanExporter for testing span content."""
    current_provider = otel_trace.get_tracer_provider()
    if isinstance(current_provider, ProxyTracerProvider):
        provider = TracerProvider()
        otel_trace.set_tracer_provider(provider)
    else:
        provider = current_provider
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider.add_span_processor(processor)

    exporter.clear()
    lilypad.spans._warned_noop = False
    yield exporter
    exporter.clear()


def test_noop_span_basic() -> None:
    """Test that no-op span handles all operations safely."""
    with span("noop-phase") as s:
        if isinstance(otel_trace.get_tracer_provider(), ProxyTracerProvider):
            assert s.is_noop is True
            assert s.span_id is None
        s.set(a=1, b="x")
        s.event("check", ok=True)
        s.metadata(team="core")
        s.debug("dbg")
        s.info("inf")
        s.warning("warn")
        s.error("err")
        s.critical("crit")

    s.finish()
    s.finish()


def test_noop_span_with_exception() -> None:
    """Test that no-op span handles exceptions gracefully."""
    with pytest.raises(ValueError), span("error-phase") as s:
        s.set(test=True)
        raise ValueError("test error")


def test_span_records_attributes_and_events(
    span_exporter: InMemorySpanExporter,
) -> None:
    """Test that configured span records attributes and events."""
    with span("phase") as s:
        assert s.is_noop is False
        assert s.span_id is not None
        s.set(a=1, b="x")
        s.event("evt", ok=True)
        s.error("boom", code=500)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    sp = spans[0]

    assert sp.name == "phase"
    assert sp.attributes["lilypad.type"] == "trace"
    assert sp.attributes["a"] == 1
    assert sp.attributes["b"] == "x"

    event_names = [e.name for e in sp.events]
    assert "evt" in event_names
    assert "error" in event_names

    assert sp.status.status_code.name == "ERROR"


def test_span_full_lifecycle(span_exporter: InMemorySpanExporter) -> None:
    """Test complete span lifecycle with all logging methods."""
    with span("lifecycle") as s:
        s.set(phase="start")
        s.metadata(version="1.0", env="test")
        s.debug("Starting process", step=1)
        s.info("Process initialized", ready=True)
        s.warning("Low memory", available_mb=256)
        s.event("custom", data={"key": "value"})
        s.error("Connection failed", host="localhost")
        s.critical("System failure", code="CRITICAL_001")

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    sp = spans[0]

    span_data = {
        "name": sp.name,
        "attributes": dict(sp.attributes),
        "status": sp.status.status_code.name,
        "events": [
            {"name": e.name, "attributes": dict(e.attributes) if e.attributes else {}}
            for e in sp.events
        ],
    }

    assert span_data == snapshot(
        {
            "name": "lifecycle",
            "attributes": {
                "lilypad.type": "trace",
                "phase": "start",
                "version": "1.0",
                "env": "test",
            },
            "status": "ERROR",
            "events": [
                {
                    "name": "debug",
                    "attributes": {
                        "message": "Starting process",
                        "level": "debug",
                        "step": 1,
                    },
                },
                {
                    "name": "info",
                    "attributes": {
                        "message": "Process initialized",
                        "level": "info",
                        "ready": True,
                    },
                },
                {
                    "name": "warning",
                    "attributes": {
                        "message": "Low memory",
                        "level": "warning",
                        "available_mb": 256,
                    },
                },
                {"name": "custom", "attributes": {"data": '{"key": "value"}'}},
                {
                    "name": "error",
                    "attributes": {
                        "message": "Connection failed",
                        "level": "error",
                        "host": "localhost",
                    },
                },
                {
                    "name": "critical",
                    "attributes": {
                        "message": "System failure",
                        "level": "critical",
                        "code": "CRITICAL_001",
                    },
                },
            ],
        }
    )


def test_span_with_exception_recording(span_exporter: InMemorySpanExporter) -> None:
    """Test that span records exceptions properly."""
    with pytest.raises(RuntimeError), span("exception-test") as s:
        s.set(operation="risky")
        raise RuntimeError("Something went wrong")

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    sp = spans[0]

    assert sp.name == "exception-test"
    assert sp.status.status_code.name == "ERROR"
    assert sp.attributes["operation"] == "risky"

    exception_events = [e for e in sp.events if e.name == "exception"]
    assert len(exception_events) == 1


def test_span_nested_contexts(span_exporter: InMemorySpanExporter) -> None:
    """Test nested span contexts."""
    with span("parent") as parent:
        parent.set(level=1)
        with span("child") as child:
            child.set(level=2)
            with span("grandchild") as grandchild:
                grandchild.set(level=3)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 3

    span_names = [s.name for s in spans]
    assert "parent" in span_names
    assert "child" in span_names
    assert "grandchild" in span_names

    for sp in spans:
        if sp.name == "parent":
            assert sp.attributes["level"] == 1
        elif sp.name == "child":
            assert sp.attributes["level"] == 2
        elif sp.name == "grandchild":
            assert sp.attributes["level"] == 3


def test_span_idempotent_finish(span_exporter: InMemorySpanExporter) -> None:
    """Test that finish() is idempotent."""
    s = Span("test")
    with s:
        s.set(test=True)

    s.finish()
    s.finish()
    s.finish()

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1


def test_span_manual_lifecycle(span_exporter: InMemorySpanExporter) -> None:
    """Test manual span lifecycle management."""
    s = Span("manual")
    s.__enter__()
    assert s.is_noop is False
    assert s.span_id is not None

    s.set(manual=True)
    s.event("checkpoint")
    s.__exit__(None, None, None)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "manual"
    assert spans[0].attributes["manual"] is True


def test_span_id_format(span_exporter: InMemorySpanExporter) -> None:
    """Test that span_id is properly formatted."""
    with span("format-test") as s:
        span_id = s.span_id
        assert span_id is not None
        assert len(span_id) == 16
        assert all(c in "0123456789abcdef" for c in span_id)


def test_span_attributes_after_finish(span_exporter: InMemorySpanExporter) -> None:
    """Test that operations after finish() are no-ops."""
    s = Span("finished")
    s.__enter__()
    s.set(before=True)
    s.finish()

    s.set(after=True)
    s.event("after_finish")
    s.error("should not appear")

    s.__exit__(None, None, None)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    sp = spans[0]

    assert "before" in sp.attributes
    assert "after" not in sp.attributes

    event_names = [e.name for e in sp.events]
    assert "after_finish" not in event_names
