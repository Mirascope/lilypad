"""Test cases for OpenTelemetry debug utilities."""

import logging
from unittest.mock import Mock, MagicMock

import pytest
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace import ReadableSpan

from lilypad._utils.otel_debug import wrap_batch_processor


def test_wrap_batch_processor(caplog):
    """Test wrapping of BatchSpanProcessor for debug logging."""
    # Create mock processor
    processor = Mock(spec=BatchSpanProcessor)
    processor.queue = []
    original_on_end = Mock()
    original_flush = Mock(return_value=True)
    processor.on_end = original_on_end
    processor.force_flush = original_flush

    # Create mock span
    mock_span = Mock(spec=ReadableSpan)
    mock_span.name = "test_span"

    # Wrap the processor
    wrap_batch_processor(processor)

    # Test on_end logging
    with caplog.at_level(logging.DEBUG, logger="lilypad.otel-debug"):
        # Call wrapped on_end
        processor.on_end(mock_span)

        # Check that original method was called
        assert original_on_end.called

        # Check log output
        assert "[on_end ] enqueue span=test_span  queue=0→1" in caplog.text

    # Clear logs
    caplog.clear()

    # Test force_flush logging
    with caplog.at_level(logging.DEBUG, logger="lilypad.otel-debug"):
        # Set up queue with items
        processor.queue = [1, 2, 3]

        # Call wrapped force_flush
        result = processor.force_flush(5000)

        # Check that original method was called
        assert original_flush.called
        assert result is True

        # Check log output
        assert "[flush   ] called  queue=3" in caplog.text
        assert "[flush   ] done    queue=3  result=True" in caplog.text


def test_wrap_batch_processor_with_queue_changes(caplog):
    """Test wrapping when queue size changes during operations."""
    # Create a more complex mock processor
    processor = MagicMock(spec=BatchSpanProcessor)
    queue_items = []
    processor.queue = queue_items

    # Store original methods before wrapping
    original_on_end = Mock()
    original_force_flush = Mock(return_value=True)

    # Mock on_end to add item to queue
    def mock_on_end(span):
        queue_items.append(span)
        original_on_end(span)

    # Mock force_flush to clear queue
    def mock_force_flush(timeout=5000):
        queue_items.clear()
        original_force_flush(timeout)
        return True

    processor.on_end = mock_on_end
    processor.force_flush = mock_force_flush

    # Wrap the processor
    wrap_batch_processor(processor)

    # Create mock spans
    span1 = Mock(spec=ReadableSpan)
    span1.name = "span1"
    span2 = Mock(spec=ReadableSpan)
    span2.name = "span2"

    # Test on_end with multiple spans
    with caplog.at_level(logging.DEBUG, logger="lilypad.otel-debug"):
        processor.on_end(span1)
        assert len(queue_items) == 1
        assert "[on_end ] enqueue span=span1  queue=0→1" in caplog.text

        processor.on_end(span2)
        assert len(queue_items) == 2
        assert "[on_end ] enqueue span=span2  queue=1→2" in caplog.text

    # Clear logs
    caplog.clear()

    # Test force_flush clearing queue
    with caplog.at_level(logging.DEBUG, logger="lilypad.otel-debug"):
        result = processor.force_flush()
        assert len(queue_items) == 0
        assert result is True
        assert "[flush   ] called  queue=2" in caplog.text
        assert "[flush   ] done    queue=0  result=True" in caplog.text


def test_wrap_batch_processor_preserves_functionality():
    """Test that wrapping preserves the original functionality."""
    # Create a real-like mock processor
    processor = Mock(spec=BatchSpanProcessor)
    processor.queue = []

    original_on_end_called = False
    original_flush_called = False

    def original_on_end(span):
        nonlocal original_on_end_called
        original_on_end_called = True
        processor.queue.append(span)

    def original_flush(timeout=5000):
        nonlocal original_flush_called
        original_flush_called = True
        processor.queue.clear()
        return True

    processor.on_end = original_on_end
    processor.force_flush = original_flush

    # Wrap the processor
    wrap_batch_processor(processor)

    # Create mock span
    span = Mock(spec=ReadableSpan, name="test")

    # Test that wrapped methods still call originals
    processor.on_end(span)
    assert original_on_end_called
    assert len(processor.queue) == 1

    result = processor.force_flush()
    assert original_flush_called
    assert result is True
    assert len(processor.queue) == 0


def test_wrap_batch_processor_exception_handling(caplog):
    """Test that wrapped methods handle exceptions properly."""
    processor = Mock(spec=BatchSpanProcessor)
    processor.queue = []

    # Make original methods raise exceptions
    processor.on_end = Mock(side_effect=Exception("on_end error"))
    processor.force_flush = Mock(side_effect=Exception("flush error"))

    # Wrap the processor
    wrap_batch_processor(processor)

    span = Mock(spec=ReadableSpan, name="test")

    # Test that exceptions are propagated
    with pytest.raises(Exception, match="on_end error"):
        processor.on_end(span)

    with pytest.raises(Exception, match="flush error"):
        processor.force_flush()


def test_logger_configuration():
    """Test that the logger is properly configured."""
    from lilypad._utils.otel_debug import log

    # Check logger name and level
    assert log.name == "lilypad.otel-debug"
    assert log.level == logging.DEBUG

    # Check that handler is configured
    assert len(log.handlers) > 0
    handler = log.handlers[0]
    assert isinstance(handler, logging.StreamHandler)

    # Check formatter
    formatter = handler.formatter
    assert formatter is not None
    # The format string should contain time, level, and message
    assert "%(asctime)s" in formatter._fmt
    assert "%(levelname)s" in formatter._fmt
    assert "%(message)s" in formatter._fmt
