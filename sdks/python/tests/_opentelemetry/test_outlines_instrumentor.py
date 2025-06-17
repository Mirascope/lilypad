"""Tests for Outlines OpenTelemetry instrumentor."""

from unittest.mock import Mock, patch
from lilypad._opentelemetry._opentelemetry_outlines import (
    OutlinesInstrumentor,
    _patched_targets,
)


class TestOutlinesInstrumentor:
    """Test OutlinesInstrumentor class."""

    def test_instrumentation_dependencies(self):
        """Test instrumentation_dependencies returns correct package."""
        instrumentor = OutlinesInstrumentor()
        dependencies = instrumentor.instrumentation_dependencies()

        assert "outlines>=0.1.10,<1.0" in dependencies
        assert len(dependencies) == 1

    @patch("lilypad._opentelemetry._opentelemetry_outlines.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate_stream")
    def test_instrument_basic(
        self, mock_model_generate_stream, mock_model_generate, mock_wrap_function_wrapper, mock_get_tracer
    ):
        """Test basic instrumentation functionality."""
        # Setup mocks
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_generate_wrapper = Mock()
        mock_stream_wrapper = Mock()
        mock_model_generate.return_value = mock_generate_wrapper
        mock_model_generate_stream.return_value = mock_stream_wrapper

        # Clear patched targets
        _patched_targets.clear()

        instrumentor = OutlinesInstrumentor()
        instrumentor._instrument()

        # Verify tracer creation
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_outlines",
            "0.1.0",
            None,
            schema_url="https://opentelemetry.io/schemas/1.28.0",
        )

        # Verify wrappers were created with tracer (called multiple times for different models)
        assert mock_model_generate.call_count > 1
        assert mock_model_generate_stream.call_count > 1
        # Verify all calls were made with the tracer
        for call in mock_model_generate.call_args_list:
            assert call[0][0] == mock_tracer
        for call in mock_model_generate_stream.call_args_list:
            assert call[0][0] == mock_tracer

        # Verify function wrapping calls
        assert mock_wrap_function_wrapper.call_count >= 2

        # Check ExLlamaV2Model.generate wrapping
        generate_call = mock_wrap_function_wrapper.call_args_list[0]
        assert generate_call[0] == ("outlines.models.exllamav2", "ExLlamaV2Model.generate", mock_generate_wrapper)

        # Check ExLlamaV2Model.stream wrapping
        stream_call = mock_wrap_function_wrapper.call_args_list[1]
        assert stream_call[0] == ("outlines.models.exllamav2", "ExLlamaV2Model.stream", mock_stream_wrapper)

    @patch("lilypad._opentelemetry._opentelemetry_outlines.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate_stream")
    def test_instrument_with_tracer_provider(
        self, mock_model_generate_stream, mock_model_generate, mock_wrap_function_wrapper, mock_get_tracer
    ):
        """Test instrumentation with custom tracer provider."""
        mock_tracer_provider = Mock()
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_generate_wrapper = Mock()
        mock_stream_wrapper = Mock()
        mock_model_generate.return_value = mock_generate_wrapper
        mock_model_generate_stream.return_value = mock_stream_wrapper

        # Clear patched targets
        _patched_targets.clear()

        instrumentor = OutlinesInstrumentor()
        instrumentor._instrument(tracer_provider=mock_tracer_provider)

        # Verify tracer creation with custom provider
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_outlines",
            "0.1.0",
            mock_tracer_provider,
            schema_url="https://opentelemetry.io/schemas/1.28.0",
        )

    @patch("lilypad._opentelemetry._opentelemetry_outlines.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate_stream")
    def test_instrument_tracks_patched_targets(
        self, mock_model_generate_stream, mock_model_generate, mock_wrap_function_wrapper, mock_get_tracer
    ):
        """Test that instrumentation tracks patched targets."""
        # Setup mocks
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_generate_wrapper = Mock()
        mock_stream_wrapper = Mock()
        mock_model_generate.return_value = mock_generate_wrapper
        mock_model_generate_stream.return_value = mock_stream_wrapper

        # Clear patched targets
        _patched_targets.clear()

        instrumentor = OutlinesInstrumentor()
        instrumentor._instrument()

        # Verify patched targets were recorded (should be many more than just 2)
        assert len(_patched_targets) > 10  # There are many models being instrumented

        # Check that some expected targets are in patched_targets
        expected_targets = [
            ("outlines.models.exllamav2", "ExLlamaV2Model", "generate"),
            ("outlines.models.exllamav2", "ExLlamaV2Model", "stream"),
        ]
        for target in expected_targets:
            assert target in _patched_targets

    def test_instrument_inherits_from_base_instrumentor(self):
        """Test that OutlinesInstrumentor inherits from BaseInstrumentor."""
        from opentelemetry.instrumentation.instrumentor import BaseInstrumentor

        instrumentor = OutlinesInstrumentor()
        assert isinstance(instrumentor, BaseInstrumentor)

    @patch("lilypad._opentelemetry._opentelemetry_outlines.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate_stream")
    def test_instrument_handles_kwargs(
        self, mock_model_generate_stream, mock_model_generate, mock_wrap_function_wrapper, mock_get_tracer
    ):
        """Test instrumentation handles additional kwargs."""
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_generate_wrapper = Mock()
        mock_stream_wrapper = Mock()
        mock_model_generate.return_value = mock_generate_wrapper
        mock_model_generate_stream.return_value = mock_stream_wrapper

        # Clear patched targets
        _patched_targets.clear()

        instrumentor = OutlinesInstrumentor()
        instrumentor._instrument(tracer_provider=Mock(), custom_param="value", another_param=123)

        # Should still work despite additional kwargs
        mock_get_tracer.assert_called_once()
        assert len(_patched_targets) > 10

    def test_patched_targets_is_list(self):
        """Test that _patched_targets is initialized as a list."""
        assert isinstance(_patched_targets, list)

    def test_patched_targets_can_be_cleared(self):
        """Test that _patched_targets can be cleared and modified."""
        # Add some test data
        _patched_targets.extend(
            [
                ("test.module", "TestClass", "test_method"),
                ("another.module", "AnotherClass", "another_method"),
            ]
        )

        assert len(_patched_targets) >= 2

        # Clear and verify
        _patched_targets.clear()
        assert len(_patched_targets) == 0

        # Add new data
        _patched_targets.append(("new.module", "NewClass", "new_method"))
        assert len(_patched_targets) == 1
        assert _patched_targets[0] == ("new.module", "NewClass", "new_method")

    @patch("lilypad._opentelemetry._opentelemetry_outlines.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.wrap_function_wrapper")
    def test_instrument_with_mock_patch_functions(self, mock_wrap_function_wrapper, mock_get_tracer):
        """Test instrumentation with mocked patch functions."""
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Clear patched targets
        _patched_targets.clear()

        with (
            patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate") as mock_model_generate,
            patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate_stream") as mock_model_generate_stream,
        ):
            mock_generate_wrapper = Mock()
            mock_stream_wrapper = Mock()
            mock_model_generate.return_value = mock_generate_wrapper
            mock_model_generate_stream.return_value = mock_stream_wrapper

            instrumentor = OutlinesInstrumentor()
            instrumentor._instrument()

            # Verify patch functions were called with tracer
            assert mock_model_generate.call_count > 1
            assert mock_model_generate_stream.call_count > 1
