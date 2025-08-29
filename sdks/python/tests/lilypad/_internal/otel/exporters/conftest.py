"""Test fixtures for exporters module."""

import os
from unittest.mock import MagicMock, Mock
import pytest
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind, Status, Link
from opentelemetry.trace.span import TraceState
from opentelemetry.util.types import Attributes

from lilypad._internal.otel.exporters.config import ConfigureExportersConfig
from lilypad._internal.otel.exporters.transport import (
    TelemetryTransport,
    TelemetryConfig,
)
from lilypad._internal.otel.exporters.exporters import (
    ImmediateStartExporter,
    LilypadOTLPExporter,
)
from lilypad._internal.otel.exporters.processors import LLMSpanProcessor
from lilypad.client import get_client


@pytest.fixture
def exporter_config():
    """Create test exporter configuration."""
    from unittest.mock import MagicMock

    mock_client = MagicMock()
    return ConfigureExportersConfig(
        client=mock_client,
        base_url="http://localhost:3000",
        timeout=30.0,
        max_retry_attempts=3,
    )


@pytest.fixture
def mock_lilypad_client():
    """Create mock Fern-generated client."""
    client = MagicMock()
    client.telemetry = MagicMock()
    client.telemetry.send_traces = MagicMock(return_value={"partial_success": None})
    return client


@pytest.fixture
def real_lilypad_client():
    """Create real Fern-generated client for VCR tests."""
    return get_client(
        api_key=os.getenv("LILYPAD_API_KEY", "test-api-key"),
        base_url=os.getenv("LILYPAD_BASE_URL", "http://localhost:3000"),
    )


@pytest.fixture
def telemetry_config():
    """Create test telemetry configuration."""
    return TelemetryConfig(
        timeout=30.0,
        max_retry_attempts=3,
    )


@pytest.fixture
def mock_transport(mock_lilypad_client, telemetry_config):
    """Create transport with mock client."""
    return TelemetryTransport(client=mock_lilypad_client, config=telemetry_config)


@pytest.fixture
def real_transport(real_lilypad_client, telemetry_config):
    """Create transport with real client for VCR tests."""
    return TelemetryTransport(client=real_lilypad_client, config=telemetry_config)


@pytest.fixture
def immediate_start_exporter(mock_transport):
    """Create ImmediateStartExporter with mock transport."""
    return ImmediateStartExporter(transport=mock_transport, max_retry_attempts=3)


@pytest.fixture
def otlp_exporter(mock_transport):
    """Create LilypadOTLPExporter with mock transport."""
    return LilypadOTLPExporter(transport=mock_transport, timeout=30.0)


@pytest.fixture
def batch_processor(otlp_exporter):
    """Create BatchSpanProcessor with OTLP exporter."""
    return BatchSpanProcessor(otlp_exporter)


@pytest.fixture
def llm_processor(immediate_start_exporter, batch_processor):
    """Create LLMSpanProcessor with both exporters."""
    return LLMSpanProcessor(
        start_exporter=immediate_start_exporter,
        batch_processor=batch_processor,
    )


@pytest.fixture
def span_exporter():
    """Create InMemorySpanExporter for capturing spans."""
    exporter = InMemorySpanExporter()
    exporter.clear()
    return exporter


@pytest.fixture
def tracer_provider(span_exporter):
    """Create TracerProvider with InMemorySpanExporter."""
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(span_exporter))
    return provider


def create_mock_span(
    name: str = "test-span",
    trace_id: int | None = None,
    span_id: int | None = None,
    parent_span_id: int | None = None,
    start_time: int | None = None,
    end_time: int | None = None,
    attributes: Attributes | None = None,
    status: Status | None = None,
    events: list | None = None,
    links: list[Link] | None = None,
    kind: SpanKind = SpanKind.INTERNAL,
    resource: Mock | None = None,
) -> ReadableSpan:
    """Create a mock ReadableSpan for testing."""
    if trace_id is None:
        trace_id = 0x123456789ABCDEF0123456789ABCDEF0
    if span_id is None:
        span_id = 0x1234567890ABCDEF
    if start_time is None:
        start_time = 1000000000000000000
    if end_time is None:
        end_time = 1000000001000000000

    if resource is None:
        resource = Mock(attributes={"service.name": "test-service"})

    span = Mock(spec=ReadableSpan)
    span.name = name
    span.get_span_context = Mock(
        return_value=Mock(
            trace_id=trace_id,
            span_id=span_id,
            trace_flags=1,
            trace_state=TraceState(),
            is_remote=False,
            is_valid=True,
        )
    )
    span.parent = (
        Mock(
            trace_id=trace_id,
            span_id=parent_span_id,
            trace_flags=1,
            trace_state=TraceState(),
            is_remote=False,
            is_valid=bool(parent_span_id),
        )
        if parent_span_id
        else None
    )
    span.start_time = start_time
    span.end_time = end_time
    span.attributes = attributes or {}
    if status:
        span.status = status
    else:
        status_mock = Mock()
        status_mock.status_code = Mock()
        status_mock.status_code.value = 0
        status_mock.description = None
        span.status = status_mock
    span.events = events or []
    span.links = links or []
    span.kind = Mock(value=kind.value if hasattr(kind, "value") else 0)
    span.resource = resource
    span.instrumentation_scope = Mock()
    span.instrumentation_scope.name = "test-instrumentation"
    span.instrumentation_scope.version = "1.0.0"

    return span


@pytest.fixture
def mock_span():
    """Create a single mock span."""
    return create_mock_span()


@pytest.fixture
def mock_spans():
    """Create multiple mock spans for batch testing."""
    shared_resource = Mock(attributes={"service.name": "test-service"})
    spans = []
    for i in range(3):
        span = create_mock_span(
            name=f"test-span-{i}",
            span_id=0x1234567890ABCDE0 + i,
            resource=shared_resource,
        )
        spans.append(span)
    return spans


@pytest.fixture
def nested_mock_spans():
    """Create nested mock spans with parent-child relationships."""
    shared_resource = Mock(attributes={"service.name": "test-service"})

    parent = create_mock_span(
        name="parent-span", span_id=0x1111111111111111, resource=shared_resource
    )

    child1 = create_mock_span(
        name="child-span-1",
        span_id=0x2222222222222222,
        parent_span_id=0x1111111111111111,
        resource=shared_resource,
    )

    child2 = create_mock_span(
        name="child-span-2",
        span_id=0x3333333333333333,
        parent_span_id=0x1111111111111111,
        resource=shared_resource,
    )

    return [parent, child1, child2]


@pytest.fixture
def mock_span_with_events():
    """Create mock span with events."""
    events = [
        Mock(
            name="event1",
            timestamp=1000000000500000000,
            attributes={"key": "value"},
        ),
        Mock(
            name="event2",
            timestamp=1000000000800000000,
            attributes={"key2": "value2"},
        ),
    ]
    return create_mock_span(name="span-with-events", events=events)


@pytest.fixture
def mock_span_with_error():
    """Create mock span with error status."""
    error_status = Mock()
    error_status.status_code = Mock()
    error_status.status_code.value = 2
    error_status.description = "Something went wrong"
    return create_mock_span(
        name="error-span",
        status=error_status,
        attributes={
            "error.type": "ValueError",
            "error.message": "Invalid input",
        },
    )


@pytest.fixture(autouse=True)
def cleanup_environment():
    """Clean up environment after each test."""
    yield
    # Clean up singleton instance if it exists
    # Note: TracerProvider doesn't have a public _instance attribute
    # so we'll skip this cleanup
