"""Tests for Google GenAI instrumentor."""

import pytest
from unittest.mock import Mock, patch
from collections.abc import Collection

from lilypad._opentelemetry._opentelemetry_google_genai import GoogleGenAIInstrumentor


class TestGoogleGenAIInstrumentor:
    """Test GoogleGenAIInstrumentor class."""

    def test_init(self):
        """Test GoogleGenAIInstrumentor initialization."""
        instrumentor = GoogleGenAIInstrumentor()
        assert isinstance(instrumentor, GoogleGenAIInstrumentor)

    def test_instrumentation_dependencies(self):
        """Test instrumentation_dependencies method."""
        instrumentor = GoogleGenAIInstrumentor()
        dependencies = instrumentor.instrumentation_dependencies()

        assert isinstance(dependencies, Collection)
        assert len(dependencies) == 1
        assert "google-genai>=1.3.0,<2" in dependencies

    @patch("lilypad._opentelemetry._opentelemetry_google_genai.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.generate_content")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.generate_content_async")
    def test_instrument_basic(
        self, mock_generate_content_async, mock_generate_content, mock_wrap_function_wrapper, mock_get_tracer
    ):
        """Test basic _instrument functionality."""
        instrumentor = GoogleGenAIInstrumentor()

        # Mock tracer
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Mock wrapper functions
        mock_sync_wrapper = Mock()
        mock_async_wrapper = Mock()
        mock_generate_content.return_value = mock_sync_wrapper
        mock_generate_content_async.return_value = mock_async_wrapper

        # Call _instrument
        instrumentor._instrument()

        # Verify get_tracer was called correctly
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_google_genai",
            "0.1.0",
            None,
            schema_url="https://opentelemetry.io/schemas/1.28.0",
        )

        # Verify wrapper functions were called
        mock_generate_content.assert_called()
        mock_generate_content_async.assert_called()

        # Verify wrap_function_wrapper was called for all methods
        assert mock_wrap_function_wrapper.call_count == 4

        # Check individual wrapper calls
        expected_calls = [
            {"module": "google.genai.models", "name": "Models.generate_content", "wrapper": mock_sync_wrapper},
            {"module": "google.genai.models", "name": "Models.generate_content_stream", "wrapper": mock_sync_wrapper},
            {"module": "google.genai.models", "name": "AsyncModels.generate_content", "wrapper": mock_async_wrapper},
            {
                "module": "google.genai.models",
                "name": "AsyncModels.generate_content_stream",
                "wrapper": mock_async_wrapper,
            },
        ]

        for i, expected_call in enumerate(expected_calls):
            call_args = mock_wrap_function_wrapper.call_args_list[i]
            assert call_args[1]["module"] == expected_call["module"]
            assert call_args[1]["name"] == expected_call["name"]
            assert call_args[1]["wrapper"] == expected_call["wrapper"]

    @patch("lilypad._opentelemetry._opentelemetry_google_genai.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.generate_content")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.generate_content_async")
    def test_instrument_with_tracer_provider(
        self, mock_generate_content_async, mock_generate_content, mock_wrap_function_wrapper, mock_get_tracer
    ):
        """Test _instrument with custom tracer_provider."""
        instrumentor = GoogleGenAIInstrumentor()

        # Mock tracer provider
        mock_tracer_provider = Mock()
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Mock wrapper functions
        mock_sync_wrapper = Mock()
        mock_async_wrapper = Mock()
        mock_generate_content.return_value = mock_sync_wrapper
        mock_generate_content_async.return_value = mock_async_wrapper

        # Call _instrument with tracer_provider
        instrumentor._instrument(tracer_provider=mock_tracer_provider)

        # Verify get_tracer was called with custom tracer_provider
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_google_genai",
            "0.1.0",
            mock_tracer_provider,
            schema_url="https://opentelemetry.io/schemas/1.28.0",
        )

    @patch("lilypad._opentelemetry._opentelemetry_google_genai.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.generate_content")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.generate_content_async")
    def test_instrument_generate_content_calls(
        self, mock_generate_content_async, mock_generate_content, mock_wrap_function_wrapper, mock_get_tracer
    ):
        """Test that generate_content wrapper functions are called correctly."""
        instrumentor = GoogleGenAIInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Mock wrapper functions - avoid recursive mock issues
        mock_sync_wrapper = Mock(spec=[])
        mock_async_wrapper = Mock(spec=[])
        mock_generate_content.return_value = mock_sync_wrapper
        mock_generate_content_async.return_value = mock_async_wrapper

        instrumentor._instrument()

        # Verify generate_content was called for both stream=True and stream=False
        expected_calls = [
            (mock_tracer,),  # Call with tracer and stream=False (keyword arg)
            (mock_tracer,),  # Call with tracer and stream=True (keyword arg)
        ]

        actual_calls = mock_generate_content.call_args_list
        assert len(actual_calls) == 2
        # Check positional args
        for i, expected_call in enumerate(expected_calls):
            assert actual_calls[i][0] == expected_call
        # Check keyword args
        assert actual_calls[0][1] == {"stream": False}
        assert actual_calls[1][1] == {"stream": True}

        # Verify generate_content_async was called for both stream=True and stream=False
        expected_async_calls = [
            (mock_tracer,),  # Call with tracer and stream=False (keyword arg)
            (mock_tracer,),  # Call with tracer and stream=True (keyword arg)
        ]

        actual_async_calls = mock_generate_content_async.call_args_list
        assert len(actual_async_calls) == 2
        # Check positional args
        for i, expected_call in enumerate(expected_async_calls):
            assert actual_async_calls[i][0] == expected_call
        # Check keyword args
        assert actual_async_calls[0][1] == {"stream": False}
        assert actual_async_calls[1][1] == {"stream": True}

    @patch("google.genai.models")
    @patch("opentelemetry.instrumentation.utils.unwrap")
    def test_uninstrument_basic(self, mock_unwrap, mock_google_genai_models):
        """Test basic _uninstrument functionality."""
        instrumentor = GoogleGenAIInstrumentor()

        # Mock models classes with proper spec to avoid recursion
        mock_models = Mock(spec=["generate_content", "generate_content_stream"])
        mock_async_models = Mock(spec=["generate_content", "generate_content_stream"])
        mock_google_genai_models.Models = mock_models
        mock_google_genai_models.AsyncModels = mock_async_models

        # Call _uninstrument
        instrumentor._uninstrument()

        # Verify unwrap was called for all methods
        assert mock_unwrap.call_count == 4

        expected_unwrap_calls = [
            (mock_models, "generate_content"),
            (mock_models, "generate_content_stream"),
            (mock_async_models, "generate_content"),
            (mock_async_models, "generate_content_stream"),
        ]

        actual_calls = mock_unwrap.call_args_list
        for i, expected_call in enumerate(expected_unwrap_calls):
            assert actual_calls[i][0] == expected_call

    @patch("google.genai.models")
    @patch("opentelemetry.instrumentation.utils.unwrap")
    def test_uninstrument_with_kwargs(self, mock_unwrap, mock_google_genai_models):
        """Test _uninstrument with additional kwargs."""
        instrumentor = GoogleGenAIInstrumentor()

        # Mock models classes with proper spec to avoid recursion
        mock_models = Mock(spec=["generate_content", "generate_content_stream"])
        mock_async_models = Mock(spec=["generate_content", "generate_content_stream"])
        mock_google_genai_models.Models = mock_models
        mock_google_genai_models.AsyncModels = mock_async_models

        # Call _uninstrument with kwargs (should be ignored)
        instrumentor._uninstrument(some_kwarg="value")

        # Verify unwrap was still called correctly
        assert mock_unwrap.call_count == 4

    @patch(
        "lilypad._opentelemetry._opentelemetry_google_genai.wrap_function_wrapper",
        side_effect=Exception("Wrapper error"),
    )
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.generate_content")
    def test_instrument_wrapper_error(self, mock_generate_content, mock_get_tracer, mock_wrap_function_wrapper):
        """Test _instrument handling of wrapper errors."""
        instrumentor = GoogleGenAIInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_generate_content.return_value = Mock()

        # Should raise exception when wrapper fails
        with pytest.raises(Exception, match="Wrapper error"):
            instrumentor._instrument()

    def test_uninstrument_import_error(self):
        """Test _uninstrument handling of import errors."""
        instrumentor = GoogleGenAIInstrumentor()

        # Patch the import statement to raise ImportError
        with (
            patch("builtins.__import__", side_effect=ImportError("Module not found")),
            pytest.raises(ImportError, match="Module not found"),
        ):
            instrumentor._uninstrument()

    @patch("opentelemetry.instrumentation.utils.unwrap", side_effect=Exception("Unwrap error"))
    @patch("google.genai.models")
    def test_uninstrument_unwrap_error(self, mock_google_genai_models, mock_unwrap):
        """Test _uninstrument handling of unwrap errors."""
        instrumentor = GoogleGenAIInstrumentor()

        # Mock models classes with proper spec to avoid recursion
        mock_models = Mock(spec=["generate_content", "generate_content_stream"])
        mock_async_models = Mock(spec=["generate_content", "generate_content_stream"])
        mock_google_genai_models.Models = mock_models
        mock_google_genai_models.AsyncModels = mock_async_models

        # Should raise exception when unwrap fails
        with pytest.raises(Exception, match="Unwrap error"):
            instrumentor._uninstrument()

    def test_inheritance(self):
        """Test that GoogleGenAIInstrumentor properly inherits from BaseInstrumentor."""
        from opentelemetry.instrumentation.instrumentor import BaseInstrumentor

        instrumentor = GoogleGenAIInstrumentor()
        assert isinstance(instrumentor, BaseInstrumentor)

        # Verify required methods exist
        assert hasattr(instrumentor, "_instrument")
        assert hasattr(instrumentor, "_uninstrument")
        assert hasattr(instrumentor, "instrumentation_dependencies")
        assert callable(instrumentor._instrument)
        assert callable(instrumentor._uninstrument)
        assert callable(instrumentor.instrumentation_dependencies)

    @patch("lilypad._opentelemetry._opentelemetry_google_genai.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.generate_content")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.generate_content_async")
    def test_instrument_tracer_version_and_schema(
        self, mock_generate_content_async, mock_generate_content, mock_wrap_function_wrapper, mock_get_tracer
    ):
        """Test that tracer is created with correct version and schema."""
        instrumentor = GoogleGenAIInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_generate_content.return_value = Mock()
        mock_generate_content_async.return_value = Mock()

        instrumentor._instrument()

        # Verify tracer was created with correct parameters
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_google_genai",
            "0.1.0",  # Instrumentor version
            None,  # tracer_provider (default)
            schema_url="https://opentelemetry.io/schemas/1.28.0",  # Schema URL
        )

    @patch("lilypad._opentelemetry._opentelemetry_google_genai.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.generate_content")
    @patch("lilypad._opentelemetry._opentelemetry_google_genai.generate_content_async")
    def test_instrument_multiple_calls(
        self, mock_generate_content_async, mock_generate_content, mock_wrap_function_wrapper, mock_get_tracer
    ):
        """Test that _instrument can be called multiple times safely."""
        instrumentor = GoogleGenAIInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_generate_content.return_value = Mock()
        mock_generate_content_async.return_value = Mock()

        # Call _instrument multiple times
        instrumentor._instrument()
        instrumentor._instrument()

        # Verify functions were called multiple times
        assert mock_get_tracer.call_count == 2
        assert mock_wrap_function_wrapper.call_count == 8  # 4 calls per instrument
