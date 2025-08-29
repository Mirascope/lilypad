"""VCR-based tests for exporters with real HTTP interactions."""

import os
import time
from concurrent.futures import ThreadPoolExecutor
import pytest
from opentelemetry.sdk.trace import TracerProvider, ReadableSpan
from opentelemetry.sdk.trace.export import SpanExportResult
from opentelemetry.trace import set_tracer_provider

from lilypad._internal.otel.exporters.config import (
    ConfigureExportersConfig,
    configure_exporters,
)
from lilypad._internal.otel.exporters.transport import (
    TelemetryTransport,
    TelemetryConfig,
)
from lilypad._internal.otel.exporters.exporters import (
    ImmediateStartExporter,
    LilypadOTLPExporter,
)
from lilypad.client import get_client


@pytest.fixture
def lilypad_client():
    """Create real Lilypad client for VCR recording."""
    return get_client(
        api_key=os.getenv("LILYPAD_API_KEY", "test-api-key"),
        base_url=os.getenv("LILYPAD_BASE_URL", "http://localhost:3000"),
    )


@pytest.mark.vcr()
def test_transport_export_single_span(lilypad_client):
    """Test exporting a single span with real client."""
    transport = TelemetryTransport(
        client=lilypad_client,
        config=TelemetryConfig(timeout=30.0, max_retry_attempts=3),
    )

    provider = TracerProvider()
    tracer = provider.get_tracer("test-tracer", "1.0.0")

    with tracer.start_as_current_span("test-operation") as otel_span:
        otel_span.set_attribute("test.key", "test-value")

    from unittest.mock import Mock

    span = Mock(spec=ReadableSpan)
    span.name = "test-operation"
    span.get_span_context.return_value = Mock(
        trace_id=0x123456789ABCDEF0123456789ABCDEF0,
        span_id=0x1234567890ABCDEF,
    )
    span.parent = None
    span.start_time = 1000000000000000000
    span.end_time = 1000000001000000000
    span.attributes = {"test.key": "test-value"}
    status_mock = Mock()
    status_mock.status_code = Mock()
    status_mock.status_code.value = 0
    status_mock.description = None
    span.status = status_mock
    span.events = []
    span.links = []
    span.kind = Mock(value=0)
    span.resource = Mock(attributes={"service.name": "test-service"})
    span.instrumentation_scope = Mock()
    span.instrumentation_scope.name = "test-tracer"
    span.instrumentation_scope.version = "1.0.0"
    spans = [span]

    result = transport.export(spans)
    assert result == SpanExportResult.SUCCESS


@pytest.mark.vcr()
def test_transport_export_batch(lilypad_client):
    """Test exporting multiple spans in a batch."""
    transport = TelemetryTransport(
        client=lilypad_client,
        config=TelemetryConfig(),
    )

    provider = TracerProvider()
    tracer = provider.get_tracer("batch-tracer")

    for i in range(3):
        with tracer.start_as_current_span(f"operation-{i}") as otel_span:
            otel_span.set_attribute("index", i)
            time.sleep(0.001)

    from unittest.mock import Mock

    spans = []
    for i in range(3):
        span = Mock(spec=ReadableSpan)
        span.name = f"operation-{i}"
        span.get_span_context.return_value = Mock(
            trace_id=0x123456789ABCDEF0123456789ABCDEF0,
            span_id=0x1234567890ABCDE0 + i,
        )
        span.parent = None
        span.start_time = 1000000000000000000 + i * 1000000
        span.end_time = 1000000001000000000 + i * 1000000
        span.attributes = {"index": i}
        status_mock = Mock()
        status_mock.status_code = Mock()
        status_mock.status_code.value = 0
        status_mock.description = None
        span.status = status_mock
        span.events = []
        span.links = []
        span.kind = Mock(value=0)
        span.resource = Mock(attributes={"service.name": "batch-service"})
        span.instrumentation_scope = Mock()
        span.instrumentation_scope.name = "batch-tracer"
        span.instrumentation_scope.version = ""
        spans.append(span)

    result = transport.export(spans)
    assert result == SpanExportResult.SUCCESS


@pytest.mark.vcr()
def test_immediate_start_exporter(lilypad_client):
    """Test ImmediateStartExporter with real client."""
    transport = TelemetryTransport(client=lilypad_client, config=TelemetryConfig())
    start_exporter = ImmediateStartExporter(transport=transport, max_retry_attempts=2)

    from unittest.mock import Mock

    span = Mock(spec=ReadableSpan)
    span.name = "start-event-test"
    span.get_span_context.return_value = Mock(
        trace_id=0x123456789ABCDEF0123456789ABCDEF0,
        span_id=0x1234567890ABCDEF,
    )
    span.parent = None
    span.start_time = 1000000000000000000
    span.end_time = None  # Not ended yet
    span.attributes = {"event.type": "start"}
    status_mock = Mock()
    status_mock.status_code = Mock()
    status_mock.status_code.value = 0
    status_mock.description = None
    span.status = status_mock
    span.events = []
    span.links = []
    span.kind = Mock(value=0)
    span.resource = Mock(attributes={"service.name": "start-service"})
    span.instrumentation_scope = Mock()
    span.instrumentation_scope.name = "start-tracer"
    span.instrumentation_scope.version = "1.0.0"

    result = start_exporter.export_start_event(span)
    assert result is True


@pytest.mark.vcr()
def test_otlp_exporter(lilypad_client):
    """Test LilypadOTLPExporter with real client."""
    transport = TelemetryTransport(client=lilypad_client, config=TelemetryConfig())
    otlp_exporter = LilypadOTLPExporter(transport=transport, timeout=30.0)

    from unittest.mock import Mock

    spans = []
    for i in range(2):
        span = Mock(spec=ReadableSpan)
        span.name = f"otlp-span-{i}"
        span.get_span_context.return_value = Mock(
            trace_id=0x987654321FEDCBA0987654321FEDCBA0,
            span_id=0xFEDCBA9876543210 + i,
        )
        span.parent = None
        span.start_time = 2000000000000000000 + i * 1000000
        span.end_time = 2000000001000000000 + i * 1000000
        span.attributes = {"otlp.test": True, "index": i}
        status_mock = Mock()
        status_mock.status_code = Mock()
        status_mock.status_code.value = 0
        status_mock.description = None
        span.status = status_mock
        span.events = []
        span.links = []
        span.kind = Mock(value=0)
        span.resource = Mock(attributes={"service.name": "otlp-service"})
        span.instrumentation_scope = Mock()
        span.instrumentation_scope.name = "otlp-tracer"
        span.instrumentation_scope.version = "2.0.0"
        spans.append(span)

    result = otlp_exporter.export(spans)
    assert result == SpanExportResult.SUCCESS


@pytest.mark.vcr()
def test_full_pipeline_with_vcr(lilypad_client):
    """Test complete pipeline with two-phase export using VCR."""
    config = ConfigureExportersConfig(
        client=lilypad_client,
        base_url=os.getenv("LILYPAD_BASE_URL", "http://localhost:3000"),
        timeout=30.0,
        max_retry_attempts=3,
    )

    processor = configure_exporters(config)

    provider = TracerProvider()
    provider.add_span_processor(processor)
    set_tracer_provider(provider)

    tracer = provider.get_tracer("full-pipeline-tracer", "1.0.0")

    with tracer.start_as_current_span("parent-operation") as parent:
        parent.set_attribute("operation.type", "parent")
        parent.set_attribute("test.framework", "pytest")

        with tracer.start_as_current_span("child-operation-1") as child1:
            child1.set_attribute("operation.type", "child")
            child1.set_attribute("child.index", 1)
            time.sleep(0.001)

        with tracer.start_as_current_span("child-operation-2") as child2:
            child2.set_attribute("operation.type", "child")
            child2.set_attribute("child.index", 2)
            time.sleep(0.001)

    processor.force_flush(timeout_millis=30000)

    provider.shutdown()

    assert processor._shutdown is True


@pytest.mark.vcr()
def test_error_span_export(lilypad_client):
    """Test exporting spans with error status."""
    transport = TelemetryTransport(client=lilypad_client, config=TelemetryConfig())

    from unittest.mock import Mock

    error_span = Mock(spec=ReadableSpan)
    error_span.name = "error-operation"
    error_span.get_span_context.return_value = Mock(
        trace_id=0xABCDEF123456789ABCDEF1234567890,
        span_id=0x1234567890ABCDEF,
    )
    error_span.parent = None
    error_span.start_time = 3000000000000000000
    error_span.end_time = 3000000001000000000
    error_span.attributes = {
        "error.type": "ValueError",
        "error.message": "Test error message",
        "http.status_code": 500,
    }
    error_status = Mock()
    error_status.status_code = Mock()
    error_status.status_code.value = 2
    error_status.description = "Internal Server Error"
    error_span.status = error_status
    error_span.events = []
    error_span.links = []
    error_span.kind = Mock(value=2)  # SERVER
    error_span.resource = Mock(attributes={"service.name": "error-service"})
    error_span.instrumentation_scope = Mock()
    error_span.instrumentation_scope.name = "error-tracer"
    error_span.instrumentation_scope.version = "1.0.0"

    result = transport.export([error_span])
    assert result == SpanExportResult.SUCCESS


@pytest.mark.vcr()
def test_concurrent_exports(lilypad_client):
    """Test concurrent span exports."""
    transport = TelemetryTransport(client=lilypad_client, config=TelemetryConfig())

    from unittest.mock import Mock

    def create_and_export_span(index: int) -> SpanExportResult:
        span = Mock(spec=ReadableSpan)
        span.name = f"concurrent-span-{index}"
        span.get_span_context.return_value = Mock(
            trace_id=0x123456789ABCDEF0123456789ABCDEF0 + index,
            span_id=0x1234567890ABCDEF + index,
        )
        span.parent = None
        span.start_time = 4000000000000000000 + index * 1000000
        span.end_time = 4000000001000000000 + index * 1000000
        span.attributes = {"concurrent.index": index}
        status_mock = Mock()
        status_mock.status_code = Mock()
        status_mock.status_code.value = 0
        status_mock.description = None
        span.status = status_mock
        span.events = []
        span.links = []
        span.kind = Mock(value=0)
        span.resource = Mock(attributes={"service.name": "concurrent-service"})
        span.instrumentation_scope = Mock()
        span.instrumentation_scope.name = "concurrent-tracer"
        span.instrumentation_scope.version = "1.0.0"

        return transport.export([span])

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(create_and_export_span, i) for i in range(5)]
        results = [future.result() for future in futures]

    assert all(result == SpanExportResult.SUCCESS for result in results)


@pytest.mark.vcr()
def test_span_with_events_and_links(lilypad_client):
    """Test exporting spans with events and links."""
    transport = TelemetryTransport(client=lilypad_client, config=TelemetryConfig())

    from unittest.mock import Mock

    span = Mock(spec=ReadableSpan)
    span.name = "span-with-events"
    span.get_span_context.return_value = Mock(
        trace_id=0x555666777888999AAABBBCCCDDDEEEF,
        span_id=0xFFFEEEDDDCCCBBBA,
    )
    span.parent = None
    span.start_time = 5000000000000000000
    span.end_time = 5000000002000000000
    span.attributes = {"has.events": True}
    status_mock = Mock()
    status_mock.status_code = Mock()
    status_mock.status_code.value = 0
    status_mock.description = None
    span.status = status_mock

    event1 = Mock()
    event1.name = "processing.started"
    event1.timestamp = 5000000000500000000
    event1.attributes = {"item.count": 10}

    event2 = Mock()
    event2.name = "processing.completed"
    event2.timestamp = 5000000001500000000
    event2.attributes = {"items.processed": 10, "success": True}

    span.events = [event1, event2]

    link = Mock()
    link.context = Mock(
        trace_id=0x111222333444555666777888999AAAB, span_id=0x1122334455667788
    )
    link.attributes = {"link.type": "follows_from"}
    span.links = [link]
    span.kind = Mock(value=0)
    span.resource = Mock(attributes={"service.name": "events-service"})
    span.instrumentation_scope = Mock()
    span.instrumentation_scope.name = "events-tracer"
    span.instrumentation_scope.version = "1.0.0"

    result = transport.export([span])
    assert result == SpanExportResult.SUCCESS
