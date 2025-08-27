"""Unit tests for LLMSpanProcessor."""

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import Mock, patch
import pytest
from opentelemetry.context import Context
from opentelemetry.trace import SpanKind

from lilypad._internal.otel.exporters.processors import LLMSpanProcessor


def test_processor_init(immediate_start_exporter, batch_processor):
    """Test processor initialization."""
    processor = LLMSpanProcessor(
        start_exporter=immediate_start_exporter,
        batch_processor=batch_processor,
    )
    assert processor.start_exporter == immediate_start_exporter
    assert processor.batch_processor == batch_processor
    assert processor.executor is not None
    assert processor._shutdown is False


def test_processor_init_with_custom_executor(immediate_start_exporter, batch_processor):
    """Test processor initialization with custom executor."""
    executor = ThreadPoolExecutor(max_workers=5)
    processor = LLMSpanProcessor(
        start_exporter=immediate_start_exporter,
        batch_processor=batch_processor,
        executor=executor,
    )
    assert processor.executor == executor


def test_processor_on_start(llm_processor, mock_span):
    """Test on_start submits to executor."""
    with patch.object(llm_processor.executor, "submit") as mock_submit:
        llm_processor.on_start(mock_span)

        assert mock_submit.called
        assert (
            mock_submit.call_args[0][0]
            == llm_processor.start_exporter.export_start_event
        )
        assert mock_submit.call_args[0][1] == mock_span


def test_processor_on_start_when_shutdown(llm_processor, mock_span):
    """Test on_start does nothing when shutdown."""
    llm_processor._shutdown = True

    with patch.object(llm_processor.executor, "submit") as mock_submit:
        llm_processor.on_start(mock_span)

        assert not mock_submit.called


def test_processor_on_start_with_parent_context(llm_processor, mock_span):
    """Test on_start with parent context."""
    parent_context = Context()

    with patch.object(llm_processor.executor, "submit") as mock_submit:
        llm_processor.on_start(mock_span, parent_context)

        assert mock_submit.called
        assert (
            mock_submit.call_args[0][0]
            == llm_processor.start_exporter.export_start_event
        )
        assert mock_submit.call_args[0][1] == mock_span


def test_processor_on_end(llm_processor, mock_span):
    """Test on_end delegates to batch processor."""
    llm_processor.batch_processor.on_end = Mock()

    llm_processor.on_end(mock_span)

    assert llm_processor.batch_processor.on_end.called
    assert llm_processor.batch_processor.on_end.call_args[0][0] == mock_span


def test_processor_on_end_when_shutdown(llm_processor, mock_span):
    """Test on_end does nothing when shutdown."""
    llm_processor._shutdown = True
    llm_processor.batch_processor.on_end = Mock()

    llm_processor.on_end(mock_span)

    assert not llm_processor.batch_processor.on_end.called


def test_processor_on_end_without_batch_processor(immediate_start_exporter, mock_span):
    """Test on_end without batch processor."""
    processor = LLMSpanProcessor(
        start_exporter=immediate_start_exporter,
        batch_processor=None,
    )

    processor.on_end(mock_span)


def test_processor_shutdown(llm_processor):
    """Test processor shutdown."""
    llm_processor.batch_processor.shutdown = Mock()
    llm_processor.executor.shutdown = Mock()
    llm_processor.start_exporter.shutdown = Mock()

    llm_processor.shutdown()

    assert llm_processor._shutdown is True
    assert llm_processor.batch_processor.shutdown.called
    assert llm_processor.executor.shutdown.called
    assert llm_processor.executor.shutdown.call_args[1]["wait"] is True
    assert llm_processor.start_exporter.shutdown.called


def test_processor_shutdown_without_batch_processor(immediate_start_exporter):
    """Test shutdown without batch processor."""
    processor = LLMSpanProcessor(
        start_exporter=immediate_start_exporter,
        batch_processor=None,
    )
    processor.executor.shutdown = Mock()
    processor.start_exporter.shutdown = Mock()

    processor.shutdown()

    assert processor._shutdown is True
    assert processor.executor.shutdown.called
    assert processor.start_exporter.shutdown.called


def test_processor_force_flush_with_batch_processor(llm_processor):
    """Test force flush with batch processor."""
    llm_processor.batch_processor.force_flush = Mock(return_value=True)

    result = llm_processor.force_flush(timeout_millis=60000)

    assert result is True
    assert llm_processor.batch_processor.force_flush.called
    assert llm_processor.batch_processor.force_flush.call_args[0][0] == 60000


def test_processor_force_flush_without_batch_processor(immediate_start_exporter):
    """Test force flush without batch processor."""
    processor = LLMSpanProcessor(
        start_exporter=immediate_start_exporter,
        batch_processor=None,
    )

    result = processor.force_flush(timeout_millis=60000)

    assert result is True


def test_processor_create_start_event(llm_processor, mock_span):
    """Test creation of start event from span."""
    event = llm_processor._create_start_event(mock_span, None)

    assert isinstance(event, dict)
    assert event["trace_id"] == "123456789abcdef0123456789abcdef0"
    assert event["span_id"] == "1234567890abcdef"
    assert event["name"] == "test-span"
    assert event["start_time"] == 1000000000000000000
    assert event["kind"] == "INTERNAL"
    assert event["attributes"] == {}
    assert event["parent_span_id"] is None


def test_processor_create_start_event_with_parent_span(
    llm_processor, nested_mock_spans
):
    """Test creation of start event with parent span."""
    child_span = nested_mock_spans[1]
    event = llm_processor._create_start_event(child_span, None)

    assert event["parent_span_id"] == "1111111111111111"


def test_processor_create_start_event_with_parent_context(llm_processor):
    """Test creation of start event with parent context."""
    parent_context = Mock()
    parent_span_context = Mock(span_id=0xAAAAAAAAAAAAAAAA, is_valid=True)
    parent_span = Mock()
    parent_span.get_span_context.return_value = parent_span_context

    test_span = Mock()
    test_span.get_span_context.return_value = Mock(trace_id=123, span_id=456)
    test_span.name = "test"
    test_span.parent = None
    test_span.start_time = 1000
    test_span.attributes = {}
    test_span.kind = SpanKind.INTERNAL

    with patch(
        "lilypad._internal.otel.exporters.processors.get_current_span",
        return_value=parent_span,
    ):
        event = llm_processor._create_start_event(test_span, parent_context)

    assert event["parent_span_id"] == "aaaaaaaaaaaaaaaa"


def test_processor_create_start_event_with_attributes(llm_processor):
    """Test creation of start event with attributes."""
    span = Mock()
    span.get_span_context.return_value = Mock(trace_id=123, span_id=456)
    span.name = "test"
    span.parent = None
    span.start_time = 1000
    span.attributes = {"key1": "value1", "key2": 123}
    span.kind = SpanKind.CLIENT

    event = llm_processor._create_start_event(span, None)

    assert event["attributes"] == {"key1": "value1", "key2": 123}
    assert event["kind"] == "CLIENT"


def test_processor_create_start_event_with_span_kind_mapping(llm_processor):
    """Test span kind mapping to literals."""
    span = Mock()
    span.get_span_context.return_value = Mock(trace_id=123, span_id=456)
    span.name = "test"
    span.parent = None
    span.start_time = 1000
    span.attributes = {}

    test_cases = [
        (SpanKind.CLIENT, "CLIENT"),
        (SpanKind.SERVER, "SERVER"),
        (SpanKind.PRODUCER, "PRODUCER"),
        (SpanKind.CONSUMER, "CONSUMER"),
        (SpanKind.INTERNAL, "INTERNAL"),
    ]

    for span_kind, expected_literal in test_cases:
        span.kind = span_kind
        event = llm_processor._create_start_event(span, None)
        assert event["kind"] == expected_literal


def test_processor_create_start_event_invalid_span_context(llm_processor):
    """Test creation of start event with invalid span context."""
    span = Mock()
    span.get_span_context.return_value = None

    with pytest.raises(ValueError, match="Span context is required"):
        llm_processor._create_start_event(span, None)


def test_processor_concurrent_on_start_calls(llm_processor, mock_spans):
    """Test concurrent on_start calls are handled properly."""
    with patch.object(llm_processor.executor, "submit") as mock_submit:
        for span in mock_spans:
            llm_processor.on_start(span)

        assert mock_submit.call_count == len(mock_spans)


def test_processor_concurrent_on_end_calls(llm_processor, mock_spans):
    """Test concurrent on_end calls are handled properly."""
    llm_processor.batch_processor.on_end = Mock()

    for span in mock_spans:
        llm_processor.on_end(span)

    assert llm_processor.batch_processor.on_end.call_count == len(mock_spans)
