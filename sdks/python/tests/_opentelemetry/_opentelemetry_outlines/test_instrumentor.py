"""Tests for Outlines instrumentor."""

from unittest.mock import Mock, patch
from collections.abc import Collection

from lilypad._opentelemetry._opentelemetry_outlines import OutlinesInstrumentor, _patched_targets


class TestOutlinesInstrumentor:
    """Test OutlinesInstrumentor class."""

    def test_init(self):
        """Test OutlinesInstrumentor initialization."""
        instrumentor = OutlinesInstrumentor()
        assert isinstance(instrumentor, OutlinesInstrumentor)

    def test_instrumentation_dependencies(self):
        """Test instrumentation_dependencies method."""
        instrumentor = OutlinesInstrumentor()
        dependencies = instrumentor.instrumentation_dependencies()

        assert isinstance(dependencies, Collection)
        assert len(dependencies) == 1
        assert "outlines>=0.1.10,<1.0" in dependencies

    @patch("lilypad._opentelemetry._opentelemetry_outlines.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate_async")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate_stream")
    def test_instrument_basic(
        self,
        mock_model_generate_stream,
        mock_model_generate_async,
        mock_model_generate,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test basic _instrument functionality."""
        # Clear any existing patched targets
        _patched_targets.clear()

        instrumentor = OutlinesInstrumentor()

        # Mock tracer
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Mock patch functions
        mock_generate_wrapper = Mock()
        mock_stream_wrapper = Mock()

        mock_model_generate.return_value = mock_generate_wrapper
        mock_model_generate_stream.return_value = mock_stream_wrapper

        # Call _instrument
        instrumentor._instrument()

        # Verify get_tracer was called correctly
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_outlines",
            "0.1.0",
            None,
            schema_url="https://opentelemetry.io/schemas/1.28.0",
        )

        # Verify patch functions were called with tracer
        mock_model_generate.assert_called_with(mock_tracer)
        mock_model_generate_stream.assert_called_with(mock_tracer)

        # Verify wrap_function_wrapper was called for all methods
        # 7 models * 2 methods (generate, stream) = 14 calls
        assert mock_wrap_function_wrapper.call_count == 14

        # Verify patched targets were tracked
        assert len(_patched_targets) == 14

        # Check some specific wrapper calls
        expected_calls = [
            ("outlines.models.exllamav2", "ExLlamaV2Model.generate", mock_generate_wrapper),
            ("outlines.models.exllamav2", "ExLlamaV2Model.stream", mock_stream_wrapper),
            ("outlines.models.llamacpp", "LlamaCpp.generate", mock_generate_wrapper),
            ("outlines.models.openai", "OpenAI.__call__", mock_generate_wrapper),
            ("outlines.models.transformers", "Transformers.generate", mock_generate_wrapper),
            ("outlines.models.vllm", "VLLM.stream", mock_stream_wrapper),
        ]

        # Check that expected calls were made
        for module, name, wrapper in expected_calls:
            found = False
            for call in mock_wrap_function_wrapper.call_args_list:
                if call[0][0] == module and call[0][1] == name and call[0][2] == wrapper:
                    found = True
                    break
            assert found, f"Expected call not found: {module}.{name}"

    @patch("lilypad._opentelemetry._opentelemetry_outlines.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate_stream")
    def test_instrument_with_tracer_provider(
        self,
        mock_model_generate_stream,
        mock_model_generate,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test _instrument with custom tracer_provider."""
        # Clear any existing patched targets
        _patched_targets.clear()

        instrumentor = OutlinesInstrumentor()

        # Mock tracer provider
        mock_tracer_provider = Mock()
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Mock patch functions
        mock_model_generate.return_value = Mock()
        mock_model_generate_stream.return_value = Mock()

        # Call _instrument with tracer_provider
        instrumentor._instrument(tracer_provider=mock_tracer_provider)

        # Verify get_tracer was called with custom tracer_provider
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_outlines",
            "0.1.0",
            mock_tracer_provider,
            schema_url="https://opentelemetry.io/schemas/1.28.0",
        )

    @patch("lilypad._opentelemetry._opentelemetry_outlines.unwrap")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.__import__", create=True)
    def test_uninstrument_basic(self, mock_import, mock_unwrap):
        """Test basic _uninstrument functionality."""
        # Clear and populate patched targets
        _patched_targets.clear()
        _patched_targets.extend(
            [
                ("outlines.models.exllamav2", "ExLlamaV2Model", "generate"),
                ("outlines.models.exllamav2", "ExLlamaV2Model", "stream"),
                ("outlines.models.llamacpp", "LlamaCpp", "generate"),
            ]
        )

        instrumentor = OutlinesInstrumentor()

        # Mock the import function and set up class attributes
        mock_module = Mock()
        mock_module.ExLlamaV2Model = Mock()
        mock_module.LlamaCpp = Mock()
        mock_import.return_value = mock_module

        # Call _uninstrument
        instrumentor._uninstrument()

        # Verify unwrap was called for each patched target in reverse order
        assert mock_unwrap.call_count == 3
        mock_unwrap.assert_any_call(mock_module.LlamaCpp, "generate")
        mock_unwrap.assert_any_call(mock_module.ExLlamaV2Model, "stream")
        mock_unwrap.assert_any_call(mock_module.ExLlamaV2Model, "generate")

        # Verify imports were made with correct fromlist
        assert mock_import.call_count == 3
        mock_import.assert_any_call("outlines.models.llamacpp", fromlist=["LlamaCpp"])
        mock_import.assert_any_call("outlines.models.exllamav2", fromlist=["ExLlamaV2Model"])

        # Verify patched targets were cleared
        assert len(_patched_targets) == 0

    @patch("lilypad._opentelemetry._opentelemetry_outlines.unwrap", side_effect=Exception("Unwrap error"))
    @patch("lilypad._opentelemetry._opentelemetry_outlines.__import__", create=True)
    def test_uninstrument_with_errors(self, mock_import, mock_unwrap):
        """Test _uninstrument suppresses exceptions."""
        # Clear and populate patched targets
        _patched_targets.clear()
        _patched_targets.extend(
            [
                ("outlines.models.exllamav2", "ExLlamaV2Model", "generate"),
                ("outlines.models.llamacpp", "LlamaCpp", "generate"),
            ]
        )

        instrumentor = OutlinesInstrumentor()

        # Mock the import function
        mock_module = Mock()
        mock_module.ExLlamaV2Model = Mock()
        mock_module.LlamaCpp = Mock()
        mock_import.return_value = mock_module

        # Call _uninstrument - should not raise despite unwrap errors
        instrumentor._uninstrument()

        # Verify unwrap was attempted for each target
        assert mock_unwrap.call_count == 2

        # Verify patched targets were still cleared
        assert len(_patched_targets) == 0

    @patch("lilypad._opentelemetry._opentelemetry_outlines.unwrap")
    def test_uninstrument_with_kwargs(self, mock_unwrap):
        """Test _uninstrument with additional kwargs."""
        # Clear patched targets
        _patched_targets.clear()

        instrumentor = OutlinesInstrumentor()

        # Call _uninstrument with kwargs (should be ignored)
        instrumentor._uninstrument(some_kwarg="value")

        # Should work without errors
        assert mock_unwrap.call_count == 0  # No targets to unwrap

    def test_inheritance(self):
        """Test that OutlinesInstrumentor properly inherits from BaseInstrumentor."""
        from opentelemetry.instrumentation.instrumentor import BaseInstrumentor

        instrumentor = OutlinesInstrumentor()
        assert isinstance(instrumentor, BaseInstrumentor)

        # Verify required methods exist
        assert hasattr(instrumentor, "_instrument")
        assert hasattr(instrumentor, "_uninstrument")
        assert hasattr(instrumentor, "instrumentation_dependencies")
        assert callable(instrumentor._instrument)
        assert callable(instrumentor._uninstrument)
        assert callable(instrumentor.instrumentation_dependencies)

    @patch("lilypad._opentelemetry._opentelemetry_outlines.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate_stream")
    def test_instrument_tracer_version_and_schema(
        self,
        mock_model_generate_stream,
        mock_model_generate,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test that tracer is created with correct version and schema."""
        # Clear any existing patched targets
        _patched_targets.clear()

        instrumentor = OutlinesInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_model_generate.return_value = Mock()
        mock_model_generate_stream.return_value = Mock()

        instrumentor._instrument()

        # Verify tracer was created with correct parameters
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_outlines",
            "0.1.0",  # Instrumentor version
            None,  # tracer_provider (default)
            schema_url="https://opentelemetry.io/schemas/1.28.0",  # Schema URL
        )

    @patch("lilypad._opentelemetry._opentelemetry_outlines.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate_stream")
    def test_instrument_multiple_calls(
        self,
        mock_model_generate_stream,
        mock_model_generate,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test that _instrument can be called multiple times safely."""
        # Clear any existing patched targets
        _patched_targets.clear()

        instrumentor = OutlinesInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_model_generate.return_value = Mock()
        mock_model_generate_stream.return_value = Mock()

        # Call _instrument multiple times
        instrumentor._instrument()
        initial_count = len(_patched_targets)

        instrumentor._instrument()

        # Verify functions were called multiple times
        assert mock_get_tracer.call_count == 2
        assert mock_wrap_function_wrapper.call_count == 28  # 14 calls per instrument

        # Patched targets should accumulate
        assert len(_patched_targets) == initial_count * 2

    @patch("lilypad._opentelemetry._opentelemetry_outlines.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate")
    @patch("lilypad._opentelemetry._opentelemetry_outlines.model_generate_stream")
    def test_patched_targets_tracking(
        self,
        mock_model_generate_stream,
        mock_model_generate,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test that patched targets are properly tracked."""
        # Clear any existing patched targets
        _patched_targets.clear()

        instrumentor = OutlinesInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_model_generate.return_value = Mock()
        mock_model_generate_stream.return_value = Mock()

        # Call _instrument
        instrumentor._instrument()

        # Verify all expected models and methods are tracked
        expected_models = [
            "ExLlamaV2Model",
            "LlamaCpp",
            "MLXLM",
            "OpenAI",
            "Transformers",
            "TransformersVision",
            "VLLM",
        ]

        tracked_models = set()
        tracked_methods = set()

        for _module, class_name, method in _patched_targets:
            tracked_models.add(class_name)
            tracked_methods.add(method)

        # Verify all models are tracked
        for model in expected_models:
            assert model in tracked_models, f"Model {model} not tracked"

        # Verify both generate and stream methods are tracked (except OpenAI which uses __call__)
        assert "generate" in tracked_methods
        assert "stream" in tracked_methods
        assert "__call__" in tracked_methods  # For OpenAI

    @patch("lilypad._opentelemetry._opentelemetry_outlines.unwrap")
    @patch(
        "lilypad._opentelemetry._opentelemetry_outlines.__import__",
        side_effect=ImportError("Module not found"),
        create=True,
    )
    def test_uninstrument_import_error(self, mock_import, mock_unwrap):
        """Test _uninstrument handles import errors gracefully."""
        # Clear and populate patched targets
        _patched_targets.clear()
        _patched_targets.extend(
            [
                ("nonexistent.module", "Class", "method"),
            ]
        )

        instrumentor = OutlinesInstrumentor()

        # Call _uninstrument - should not raise despite import error
        instrumentor._uninstrument()

        # Verify import was attempted
        mock_import.assert_called_once_with("nonexistent.module", fromlist=["Class"])

        # Verify unwrap was not called (due to import error)
        mock_unwrap.assert_not_called()

        # Verify patched targets were still cleared
        assert len(_patched_targets) == 0
