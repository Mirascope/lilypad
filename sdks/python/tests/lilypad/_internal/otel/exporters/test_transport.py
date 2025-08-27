import os
import pytest
from opentelemetry.sdk.trace.export import SpanExportResult
from unittest.mock import Mock
from opentelemetry.sdk.trace import ReadableSpan

from lilypad._internal.otel.exporters.transport import (
    TelemetryTransport,
    TelemetryConfig,
)
from lilypad.client import get_client


@pytest.fixture
def vcr_client():
    return get_client(
        api_key=os.getenv("LILYPAD_API_KEY", "test-vcr-key"),
        base_url=os.getenv("LILYPAD_BASE_URL", "http://localhost:3000"),
    )


@pytest.fixture
def vcr_transport(vcr_client):
    config = TelemetryConfig(timeout=30.0, max_retry_attempts=3)
    return TelemetryTransport(client=vcr_client, config=config)


def create_test_span(name="test-span", span_id=0x1234567890ABCDEF, attributes=None):
    span = Mock(spec=ReadableSpan)
    span.name = name
    span.get_span_context.return_value = Mock(
        trace_id=0x123456789ABCDEF0123456789ABCDEF0,
        span_id=span_id,
    )
    span.parent = None
    span.start_time = 1000000000000000000
    span.end_time = 1000000001000000000
    span.attributes = attributes or {}

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

    return span


@pytest.mark.vcr()
def test_transport_init_and_export(vcr_client):
    transport = TelemetryTransport(
        client=vcr_client,
        config=TelemetryConfig(timeout=30.0, max_retry_attempts=3),
    )

    span = create_test_span()
    result = transport.export([span])

    assert result == SpanExportResult.SUCCESS


@pytest.mark.vcr()
def test_send_batch_spans(vcr_transport):
    spans = [
        create_test_span(f"span-{i}", 0x1234567890ABCDE0 + i, {"index": i})
        for i in range(3)
    ]

    result = vcr_transport.export(spans)
    assert result == SpanExportResult.SUCCESS


@pytest.mark.vcr()
def test_send_nested_spans(vcr_transport):
    parent = create_test_span("parent-span", 0x1111111111111111)

    child1 = create_test_span("child-span-1", 0x2222222222222222)
    child1.parent = Mock(span_id=0x1111111111111111)

    child2 = create_test_span("child-span-2", 0x3333333333333333)
    child2.parent = Mock(span_id=0x1111111111111111)

    result = vcr_transport.export([parent, child1, child2])
    assert result == SpanExportResult.SUCCESS


@pytest.mark.vcr()
def test_send_span_with_events(vcr_transport):
    span = create_test_span("span-with-events")

    event1 = Mock()
    event1.name = "processing.started"
    event1.timestamp = 1000000000500000000
    event1.attributes = {"item.count": 10}

    event2 = Mock()
    event2.name = "processing.completed"
    event2.timestamp = 1000000001500000000
    event2.attributes = {"items.processed": 10}

    span.events = [event1, event2]

    result = vcr_transport.export([span])
    assert result == SpanExportResult.SUCCESS


@pytest.mark.vcr()
def test_send_span_with_error(vcr_transport):
    span = create_test_span("error-span")

    error_status = Mock()
    error_status.status_code = Mock()
    error_status.status_code.value = 2
    error_status.description = "Something went wrong"
    span.status = error_status

    span.attributes = {
        "error.type": "ValueError",
        "error.message": "Invalid input",
    }

    result = vcr_transport.export([span])
    assert result == SpanExportResult.SUCCESS


@pytest.mark.vcr()
def test_send_empty_batch(vcr_transport):
    result = vcr_transport.export([])
    assert result == SpanExportResult.SUCCESS


@pytest.mark.vcr()
def test_span_with_various_attributes(vcr_transport):
    span = create_test_span(
        "attribute-test",
        attributes={
            "string_attr": "test_value",
            "int_attr": 42,
            "float_attr": 3.14,
            "bool_attr": True,
            "list_attr": ["a", "b", "c"],
        },
    )

    result = vcr_transport.export([span])
    assert result == SpanExportResult.SUCCESS


@pytest.mark.vcr()
def test_shutdown_behavior(vcr_transport):
    span = create_test_span()
    result = vcr_transport.export([span])
    assert result == SpanExportResult.SUCCESS

    vcr_transport.shutdown()
