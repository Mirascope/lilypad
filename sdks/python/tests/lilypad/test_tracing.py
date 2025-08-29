"""Tests for @trace decorator functionality."""

from __future__ import annotations

import asyncio
import os
from typing import Generator

import pytest
from dotenv import load_dotenv
from inline_snapshot import snapshot
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from lilypad import trace
from lilypad._internal.otel.openai import instrument_openai
from ._internal.otel.test_utils import extract_span_data


@pytest.fixture
def span_exporter() -> Generator[InMemorySpanExporter, None, None]:
    """Set up InMemorySpanExporter for testing span content."""
    from opentelemetry import trace as otel_trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.trace import ProxyTracerProvider

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
    yield exporter
    exporter.clear()


@pytest.fixture
def openai_api_key() -> str:
    """Get OpenAI API key from environment or return dummy key."""
    load_dotenv()
    return os.getenv("OPENAI_API_KEY", "test-api-key")


@pytest.fixture
def openai_client(openai_api_key: str):
    """Create instrumented OpenAI client."""
    from openai import OpenAI

    client = OpenAI(api_key=openai_api_key)
    instrument_openai(client)
    return client


def test_trace_sync_local(span_exporter: InMemorySpanExporter):
    """Test basic @trace decorator on a synchronous function."""
    calls = []

    @trace(tags=["unit", "local"])
    def f(x: int) -> int:
        calls.append(x)
        return x + 1

    assert f(3) == 4
    assert calls == [3]

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "f",
            "attributes": {
                "lilypad.type": "trace",
                "lilypad.fn.qualname": "f",
                "lilypad.fn.is_async": False,
                "lilypad.fn.module": "tests.lilypad.test_tracing",
                "lilypad.trace.tags": ("local", "unit"),
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [],
        }
    )


def test_trace_with_no_tags(span_exporter: InMemorySpanExporter):
    """Test @trace decorator without tags."""

    @trace
    def add(a: int, b: int) -> int:
        return a + b

    result = add(2, 3)
    assert result == 5

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "add",
            "attributes": {
                "lilypad.type": "trace",
                "lilypad.fn.qualname": "add",
                "lilypad.fn.is_async": False,
                "lilypad.fn.module": "tests.lilypad.test_tracing",
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [],
        }
    )


def test_trace_wrap_method(span_exporter: InMemorySpanExporter):
    """Test that .wrap() returns TraceResult with response and span_id."""

    @trace(tags=["wrap_test"])
    def multiply(x: int, y: int) -> int:
        return x * y

    result = multiply.wrap(4, 5)
    assert result.response == 20
    assert result.span_id is not None
    assert len(result.span_id) == 16

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].get_span_context().span_id == int(result.span_id, 16)


def test_trace_preserves_return_type(span_exporter: InMemorySpanExporter):
    """Test that @trace preserves the original function's return type."""

    @trace
    def get_data() -> dict[str, int]:
        return {"a": 1, "b": 2}

    result = get_data()
    assert result == {"a": 1, "b": 2}
    assert isinstance(result, dict)

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1


def test_trace_nested_functions(span_exporter: InMemorySpanExporter):
    """Test nested traced functions create parent-child relationships."""

    @trace(tags=["parent"])
    def outer(x: int) -> int:
        return inner(x) + 1

    @trace(tags=["child"])
    def inner(x: int) -> int:
        return x * 2

    result = outer(5)
    assert result == 11

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 2

    inner_span = next(s for s in spans if s.name == "inner")
    outer_span = next(s for s in spans if s.name == "outer")

    assert (
        inner_span.parent.span_id == outer_span.get_span_context().span_id
        if inner_span.parent
        else False
    )


def test_trace_with_exception(span_exporter: InMemorySpanExporter):
    """Test that @trace properly handles exceptions."""

    @trace(tags=["error"])
    def failing_function():
        raise ValueError("Test error")

    with pytest.raises(ValueError, match="Test error"):
        failing_function()

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].status.status_code.name == "ERROR"

    events = spans[0].events
    assert any(e.name == "exception" for e in events)


def test_trace_qualname_simplification(span_exporter: InMemorySpanExporter):
    """Test that qualified names are simplified correctly."""

    def create_function():
        @trace
        def local_func():
            return "local"

        return local_func

    fn = create_function()
    result = fn()
    assert result == "local"

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert spans[0].name == "local_func"
    assert "local_func" in spans[0].attributes["lilypad.fn.qualname"]


@pytest.mark.vcr()
def test_trace_with_openai_parent_child(
    openai_client, span_exporter: InMemorySpanExporter
):
    """Test @trace with OpenAI creates parent-child span relationship."""

    @trace(tags=["e2e"])
    def ask(msg: str) -> str:
        resp = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": msg}],
            max_tokens=16,
        )
        return resp.choices[0].message.content or ""

    out = ask("Say hi")
    assert isinstance(out, str)
    assert out

    spans = span_exporter.get_finished_spans()
    assert len(spans) >= 2

    trace_span = next(s for s in spans if s.name == "ask")
    child_spans = [
        s
        for s in spans
        if s.parent and s.parent.span_id == trace_span.get_span_context().span_id
    ]
    assert len(child_spans) > 0
    assert any("gen_ai.system" in (child.attributes or {}) for child in child_spans)

    assert extract_span_data(trace_span) == snapshot(
        {
            "name": "ask",
            "attributes": {
                "lilypad.type": "trace",
                "lilypad.fn.qualname": "ask",
                "lilypad.fn.is_async": False,
                "lilypad.fn.module": "tests.lilypad.test_tracing",
                "lilypad.trace.tags": ("e2e",),
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [],
        }
    )


def test_trace_async_function(span_exporter: InMemorySpanExporter):
    """Test @trace decorator on async functions."""

    @trace(tags=["async", "test"])
    async def async_add(a: int, b: int) -> int:
        await asyncio.sleep(0.001)
        return a + b

    result = asyncio.run(async_add(3, 4))
    assert result == 7

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
    assert extract_span_data(spans[0]) == snapshot(
        {
            "name": "async_add",
            "attributes": {
                "lilypad.type": "trace",
                "lilypad.fn.qualname": "async_add",
                "lilypad.fn.is_async": True,
                "lilypad.fn.module": "tests.lilypad.test_tracing",
                "lilypad.trace.tags": ("async", "test"),
            },
            "status": {"status_code": "UNSET", "description": None},
            "events": [],
        }
    )


def test_trace_async_wrap_method(span_exporter: InMemorySpanExporter):
    """Test that .wrap() works with async functions."""

    @trace
    async def async_multiply(x: int, y: int) -> int:
        await asyncio.sleep(0.001)
        return x * y

    result = asyncio.run(async_multiply.wrap(6, 7))
    assert result.response == 42
    assert result.span_id is not None

    spans = span_exporter.get_finished_spans()
    assert len(spans) == 1
