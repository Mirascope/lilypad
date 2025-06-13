"""Tests to improve coverage for spans.py missing lines."""

import pytest
from unittest.mock import Mock, patch
from lilypad.spans import Span


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