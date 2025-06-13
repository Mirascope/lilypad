"""Tests for distributed tracing context propagation."""

import pytest
from unittest.mock import Mock, patch

from opentelemetry import trace, context
from opentelemetry.trace import TraceFlags
from opentelemetry.sdk.trace import TracerProvider

from lilypad._utils.context_propagation import (
    ContextPropagator,
    extract_context,
    inject_context,
    with_extracted_context,
    detach_context,
)
from lilypad.traces import trace as lilypad_trace


@pytest.fixture
def setup_tracer():
    """Set up a test tracer provider."""
    provider = TracerProvider()
    trace.set_tracer_provider(provider)
    yield provider
    # Clean up
    trace.set_tracer_provider(None)


class TestContextPropagator:
    """Test the ContextPropagator class."""

    def test_extract_context_with_w3c_headers(self, setup_tracer):
        """Test extracting context from W3C Trace Context headers."""
        headers = {
            "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        }

        propagator = ContextPropagator()
        ctx = propagator.extract_context(headers)

        # Verify context was extracted
        span_context = trace.get_current_span(ctx).get_span_context()
        assert span_context.is_valid
        assert format(span_context.trace_id, "032x") == "4bf92f3577b34da6a3ce929d0e0e4736"
        assert format(span_context.span_id, "016x") == "00f067aa0ba902b7"
        assert span_context.trace_flags == TraceFlags(0x01)

    def test_inject_context_with_current_context(self, setup_tracer):
        """Test injecting current context into headers."""
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("test_span") as span:
            headers = {}
            propagator = ContextPropagator()
            propagator.inject_context(headers)

            # Verify headers were injected
            assert "traceparent" in headers
            # Format: 00-{trace_id}-{span_id}-{flags}
            parts = headers["traceparent"].split("-")
            assert len(parts) == 4
            assert parts[0] == "00"  # version
            assert parts[1] == format(span.get_span_context().trace_id, "032x")
            assert parts[2] == format(span.get_span_context().span_id, "016x")

    def test_with_extracted_context(self, setup_tracer):
        """Test extracting and attaching context."""
        headers = {
            "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        }

        propagator = ContextPropagator()

        # Get current context before extraction
        original_ctx = context.get_current()

        # Extract and attach
        extracted_ctx, token = propagator.with_extracted_context(headers)

        # Verify context is now active
        current_ctx = context.get_current()
        assert current_ctx != original_ctx

        # Detach
        propagator.detach_context(token)

        # Verify original context is restored
        assert context.get_current() == original_ctx


class TestTraceDecoratorWithPropagation:
    """Test the @trace decorator with context propagation."""

    def test_trace_with_extract_from(self, setup_tracer):
        """Test @trace decorator with extract_from parameter."""
        headers = {
            "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        }

        # Mock the necessary dependencies
        with patch("lilypad.traces.get_settings") as mock_settings:
            mock_settings.return_value = Mock(project_id="test-project", api_key="test-key")

            with patch("lilypad.traces.get_sync_client") as mock_client:
                mock_client.return_value = Mock()

                @lilypad_trace(extract_from=headers)
                def test_function():
                    # Get current span
                    span = trace.get_current_span()
                    # Should be child of extracted context
                    return span.get_span_context()

                result = test_function()

                # Verify the span has the correct parent trace
                assert format(result.trace_id, "032x") == "4bf92f3577b34da6a3ce929d0e0e4736"

    def test_trace_with_parent_context(self, setup_tracer):
        """Test @trace decorator with parent_context parameter."""
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("parent_span") as parent:
            parent_ctx = context.get_current()

            # Mock the necessary dependencies
            with patch("lilypad.traces.get_settings") as mock_settings:
                mock_settings.return_value = Mock(project_id="test-project", api_key="test-key")

                with patch("lilypad.traces.get_sync_client") as mock_client:
                    mock_client.return_value = Mock()

                    # Clear current context
                    context.attach(context.Context())

                    @lilypad_trace(parent_context=parent_ctx)
                    def test_function():
                        # Get current span
                        span = trace.get_current_span()
                        return span.get_span_context()

                    result = test_function()

                    # Verify the span has the same trace ID as parent
                    assert result.trace_id == parent.get_span_context().trace_id

    @pytest.mark.asyncio
    async def test_async_trace_with_extract_from(self, setup_tracer):
        """Test async @trace decorator with extract_from parameter."""
        headers = {
            "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        }

        # Mock the necessary dependencies
        with patch("lilypad.traces.get_settings") as mock_settings:
            mock_settings.return_value = Mock(project_id="test-project", api_key="test-key")

            with patch("lilypad.traces.get_async_client") as mock_client:
                mock_client.return_value = Mock()

                @lilypad_trace(extract_from=headers)
                async def test_function():
                    # Get current span
                    span = trace.get_current_span()
                    return span.get_span_context()

                result = await test_function()

                # Verify the span has the correct parent trace
                assert format(result.trace_id, "032x") == "4bf92f3577b34da6a3ce929d0e0e4736"


class TestModuleFunctions:
    """Test module-level convenience functions."""

    def test_extract_context_function(self, setup_tracer):
        """Test the module-level extract_context function."""
        headers = {
            "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        }

        ctx = extract_context(headers)

        # Verify context was extracted
        span_context = trace.get_current_span(ctx).get_span_context()
        assert span_context.is_valid

    def test_inject_context_function(self, setup_tracer):
        """Test the module-level inject_context function."""
        tracer = trace.get_tracer(__name__)

        with tracer.start_as_current_span("test_span"):
            headers = {}
            inject_context(headers)

            # Verify headers were injected
            assert "traceparent" in headers

    def test_with_extracted_context_function(self, setup_tracer):
        """Test the module-level with_extracted_context function."""
        headers = {
            "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        }

        original_ctx = context.get_current()

        ctx, token = with_extracted_context(headers)
        assert context.get_current() != original_ctx

        detach_context(token)
        assert context.get_current() == original_ctx


class TestEnvironmentConfiguration:
    """Test environment-based propagator configuration."""

    @patch.dict("os.environ", {"LILYPAD_PROPAGATOR": "b3"})
    def test_b3_propagator_configuration(self):
        """Test that B3 propagator is used when configured."""
        from lilypad._utils.context_propagation import get_propagator

        propagator = get_propagator()
        # Check that B3 propagator is in the composite
        assert any("B3SingleFormat" in str(type(p)) for p in propagator._propagators)

    @patch.dict("os.environ", {"LILYPAD_PROPAGATOR": "composite"})
    def test_composite_propagator_configuration(self):
        """Test that composite propagator includes all formats."""
        from lilypad._utils.context_propagation import get_propagator

        propagator = get_propagator()
        # Should include multiple propagators
        assert len(propagator._propagators) > 1

        # Check for presence of different propagator types
        propagator_types = [str(type(p)) for p in propagator._propagators]
        assert any("TraceContext" in t for t in propagator_types)
        assert any("B3" in t for t in propagator_types)
