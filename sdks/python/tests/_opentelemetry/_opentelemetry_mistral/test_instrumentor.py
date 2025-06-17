"""Tests for Mistral instrumentor."""

import pytest
from unittest.mock import Mock, patch
from collections.abc import Collection

from lilypad._opentelemetry._opentelemetry_mistral import MistralInstrumentor


class TestMistralInstrumentor:
    """Test MistralInstrumentor class."""

    def test_init(self):
        """Test MistralInstrumentor initialization."""
        instrumentor = MistralInstrumentor()
        assert isinstance(instrumentor, MistralInstrumentor)

    def test_instrumentation_dependencies(self):
        """Test instrumentation_dependencies method."""
        instrumentor = MistralInstrumentor()
        dependencies = instrumentor.instrumentation_dependencies()

        assert isinstance(dependencies, Collection)
        assert len(dependencies) == 1
        assert "mistralai>=1.0.0,<2" in dependencies

    @patch("lilypad._opentelemetry._opentelemetry_mistral.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_complete_patch")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_complete_async_patch")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_stream_patch")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_stream_async_patch")
    def test_instrument_basic(
        self,
        mock_stream_async_patch,
        mock_stream_patch,
        mock_complete_async_patch,
        mock_complete_patch,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test basic _instrument functionality."""
        instrumentor = MistralInstrumentor()

        # Mock tracer
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Mock patch functions
        mock_complete_wrapper = Mock()
        mock_complete_async_wrapper = Mock()
        mock_stream_wrapper = Mock()
        mock_stream_async_wrapper = Mock()

        mock_complete_patch.return_value = mock_complete_wrapper
        mock_complete_async_patch.return_value = mock_complete_async_wrapper
        mock_stream_patch.return_value = mock_stream_wrapper
        mock_stream_async_patch.return_value = mock_stream_async_wrapper

        # Call _instrument
        instrumentor._instrument()

        # Verify get_tracer was called correctly
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_mistral",
            "0.1.0",
            None,
            schema_url="https://opentelemetry.io/schemas/1.28.0",
        )

        # Verify patch functions were called with tracer
        mock_complete_patch.assert_called_once_with(mock_tracer)
        mock_complete_async_patch.assert_called_once_with(mock_tracer)
        mock_stream_patch.assert_called_once_with(mock_tracer)
        mock_stream_async_patch.assert_called_once_with(mock_tracer)

        # Verify wrap_function_wrapper was called for all methods
        assert mock_wrap_function_wrapper.call_count == 4

        # Check individual wrapper calls
        expected_calls = [
            ("mistralai.chat", "Chat.complete", mock_complete_wrapper),
            ("mistralai.chat", "Chat.complete_async", mock_complete_async_wrapper),
            ("mistralai.chat", "Chat.stream", mock_stream_wrapper),
            ("mistralai.chat", "Chat.stream_async", mock_stream_async_wrapper),
        ]

        for i, (module, name, wrapper) in enumerate(expected_calls):
            call_args = mock_wrap_function_wrapper.call_args_list[i]
            assert call_args[0] == (module, name, wrapper)

    @patch("lilypad._opentelemetry._opentelemetry_mistral.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_complete_patch")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_complete_async_patch")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_stream_patch")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_stream_async_patch")
    def test_instrument_with_tracer_provider(
        self,
        mock_stream_async_patch,
        mock_stream_patch,
        mock_complete_async_patch,
        mock_complete_patch,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test _instrument with custom tracer_provider."""
        instrumentor = MistralInstrumentor()

        # Mock tracer provider
        mock_tracer_provider = Mock()
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Mock patch functions
        mock_complete_patch.return_value = Mock()
        mock_complete_async_patch.return_value = Mock()
        mock_stream_patch.return_value = Mock()
        mock_stream_async_patch.return_value = Mock()

        # Call _instrument with tracer_provider
        instrumentor._instrument(tracer_provider=mock_tracer_provider)

        # Verify get_tracer was called with custom tracer_provider
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_mistral",
            "0.1.0",
            mock_tracer_provider,
            schema_url="https://opentelemetry.io/schemas/1.28.0",
        )

    @patch("lilypad._opentelemetry._opentelemetry_mistral.unwrap")
    def test_uninstrument_basic(self, mock_unwrap):
        """Test basic _uninstrument functionality."""
        instrumentor = MistralInstrumentor()

        # Create a mock mistralai.chat module with a Chat class
        mock_chat_module = Mock()
        mock_chat = Mock(spec=["complete", "complete_async", "stream", "stream_async"])
        mock_chat_module.Chat = mock_chat

        # Patch the import to return our mock
        with patch.dict("sys.modules", {"mistralai.chat": mock_chat_module}):
            # Call _uninstrument
            instrumentor._uninstrument()

            # Verify unwrap was called for all methods
            assert mock_unwrap.call_count == 4

            # Check that unwrap was called with the correct method names
            method_names = []
            for call in mock_unwrap.call_args_list:
                method_names.append(call[0][1])  # Second argument is method name

            expected_methods = ["complete", "complete_async", "stream", "stream_async"]
            assert method_names == expected_methods

    @patch("lilypad._opentelemetry._opentelemetry_mistral.unwrap")
    def test_uninstrument_with_kwargs(self, mock_unwrap):
        """Test _uninstrument with additional kwargs."""
        instrumentor = MistralInstrumentor()

        # Create a mock mistralai.chat module with a Chat class
        mock_chat_module = Mock()
        mock_chat = Mock(spec=["complete", "complete_async", "stream", "stream_async"])
        mock_chat_module.Chat = mock_chat

        # Patch the import to return our mock
        with patch.dict("sys.modules", {"mistralai.chat": mock_chat_module}):
            # Call _uninstrument with kwargs (should be ignored)
            instrumentor._uninstrument(some_kwarg="value")

            # Verify unwrap was still called correctly
            assert mock_unwrap.call_count == 4

    @patch(
        "lilypad._opentelemetry._opentelemetry_mistral.wrap_function_wrapper",
        side_effect=Exception("Wrapper error"),
    )
    @patch("lilypad._opentelemetry._opentelemetry_mistral.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_complete_patch")
    def test_instrument_wrapper_error(self, mock_complete_patch, mock_get_tracer, mock_wrap_function_wrapper):
        """Test _instrument handling of wrapper errors."""
        instrumentor = MistralInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_complete_patch.return_value = Mock()

        # Should raise exception when wrapper fails
        with pytest.raises(Exception, match="Wrapper error"):
            instrumentor._instrument()

    def test_uninstrument_import_error(self):
        """Test _uninstrument handling of import errors."""
        instrumentor = MistralInstrumentor()

        # Patch the import statement to raise ImportError
        with (
            patch("builtins.__import__", side_effect=ImportError("Module not found")),
            pytest.raises(ImportError, match="Module not found"),
        ):
            instrumentor._uninstrument()

    @patch("lilypad._opentelemetry._opentelemetry_mistral.unwrap", side_effect=Exception("Unwrap error"))
    def test_uninstrument_unwrap_error(self, mock_unwrap):
        """Test _uninstrument handling of unwrap errors."""
        instrumentor = MistralInstrumentor()

        # Create a mock mistralai.chat module with a Chat class
        mock_chat_module = Mock()
        mock_chat = Mock(spec=["complete", "complete_async", "stream", "stream_async"])
        mock_chat_module.Chat = mock_chat

        # Patch the import to return our mock
        with (
            patch.dict("sys.modules", {"mistralai.chat": mock_chat_module}),
            pytest.raises(Exception, match="Unwrap error"),
        ):
            # Should raise exception when unwrap fails
            instrumentor._uninstrument()

    def test_inheritance(self):
        """Test that MistralInstrumentor properly inherits from BaseInstrumentor."""
        from opentelemetry.instrumentation.instrumentor import BaseInstrumentor

        instrumentor = MistralInstrumentor()
        assert isinstance(instrumentor, BaseInstrumentor)

        # Verify required methods exist
        assert hasattr(instrumentor, "_instrument")
        assert hasattr(instrumentor, "_uninstrument")
        assert hasattr(instrumentor, "instrumentation_dependencies")
        assert callable(instrumentor._instrument)
        assert callable(instrumentor._uninstrument)
        assert callable(instrumentor.instrumentation_dependencies)

    @patch("lilypad._opentelemetry._opentelemetry_mistral.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_complete_patch")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_complete_async_patch")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_stream_patch")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_stream_async_patch")
    def test_instrument_tracer_version_and_schema(
        self,
        mock_stream_async_patch,
        mock_stream_patch,
        mock_complete_async_patch,
        mock_complete_patch,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test that tracer is created with correct version and schema."""
        instrumentor = MistralInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_complete_patch.return_value = Mock()
        mock_complete_async_patch.return_value = Mock()
        mock_stream_patch.return_value = Mock()
        mock_stream_async_patch.return_value = Mock()

        instrumentor._instrument()

        # Verify tracer was created with correct parameters
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_mistral",
            "0.1.0",  # Instrumentor version
            None,  # tracer_provider (default)
            schema_url="https://opentelemetry.io/schemas/1.28.0",  # Schema URL
        )

    @patch("lilypad._opentelemetry._opentelemetry_mistral.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_complete_patch")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_complete_async_patch")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_stream_patch")
    @patch("lilypad._opentelemetry._opentelemetry_mistral.mistral_stream_async_patch")
    def test_instrument_multiple_calls(
        self,
        mock_stream_async_patch,
        mock_stream_patch,
        mock_complete_async_patch,
        mock_complete_patch,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test that _instrument can be called multiple times safely."""
        instrumentor = MistralInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_complete_patch.return_value = Mock()
        mock_complete_async_patch.return_value = Mock()
        mock_stream_patch.return_value = Mock()
        mock_stream_async_patch.return_value = Mock()

        # Call _instrument multiple times
        instrumentor._instrument()
        instrumentor._instrument()

        # Verify functions were called multiple times
        assert mock_get_tracer.call_count == 2
        assert mock_wrap_function_wrapper.call_count == 8  # 4 calls per instrument
