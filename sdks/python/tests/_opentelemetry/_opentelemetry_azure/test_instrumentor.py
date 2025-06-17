"""Tests for Azure instrumentor."""

import pytest
from unittest.mock import Mock, patch
from collections.abc import Collection

from lilypad._opentelemetry._opentelemetry_azure import AzureInstrumentor


class TestAzureInstrumentor:
    """Test AzureInstrumentor class."""

    def test_init(self):
        """Test AzureInstrumentor initialization."""
        instrumentor = AzureInstrumentor()
        assert isinstance(instrumentor, AzureInstrumentor)

    def test_instrumentation_dependencies(self):
        """Test instrumentation_dependencies method."""
        instrumentor = AzureInstrumentor()
        dependencies = instrumentor.instrumentation_dependencies()

        assert isinstance(dependencies, Collection)
        assert len(dependencies) == 1
        assert "azure-ai-inference>=1.0.0b9,<2.0" in dependencies

    @patch("lilypad._opentelemetry._opentelemetry_azure.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_azure.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_azure.chat_completions_complete")
    @patch("lilypad._opentelemetry._opentelemetry_azure.chat_completions_complete_async")
    def test_instrument_basic(
        self,
        mock_complete_async,
        mock_complete,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test basic _instrument functionality."""
        instrumentor = AzureInstrumentor()

        # Mock tracer
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Mock patch functions
        mock_complete_wrapper = Mock()
        mock_complete_async_wrapper = Mock()

        mock_complete.return_value = mock_complete_wrapper
        mock_complete_async.return_value = mock_complete_async_wrapper

        # Call _instrument
        instrumentor._instrument()

        # Verify get_tracer was called correctly
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_azure",
            "0.1.0",
            None,
            schema_url="https://opentelemetry.io/schemas/1.28.0",
        )

        # Verify patch functions were called with tracer
        mock_complete.assert_called_once_with(mock_tracer)
        mock_complete_async.assert_called_once_with(mock_tracer)

        # Verify wrap_function_wrapper was called for all methods
        assert mock_wrap_function_wrapper.call_count == 2

        # Check individual wrapper calls
        expected_calls = [
            ("azure.ai.inference", "ChatCompletionsClient.complete", mock_complete_wrapper),
            ("azure.ai.inference.aio", "ChatCompletionsClient.complete", mock_complete_async_wrapper),
        ]

        for i, (module, name, wrapper) in enumerate(expected_calls):
            call_args = mock_wrap_function_wrapper.call_args_list[i]
            call_kwargs = call_args[1]
            assert call_kwargs["module"] == module
            assert call_kwargs["name"] == name
            assert call_kwargs["wrapper"] == wrapper

    @patch("lilypad._opentelemetry._opentelemetry_azure.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_azure.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_azure.chat_completions_complete")
    @patch("lilypad._opentelemetry._opentelemetry_azure.chat_completions_complete_async")
    def test_instrument_with_tracer_provider(
        self,
        mock_complete_async,
        mock_complete,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test _instrument with custom tracer_provider."""
        instrumentor = AzureInstrumentor()

        # Mock tracer provider
        mock_tracer_provider = Mock()
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Mock patch functions
        mock_complete.return_value = Mock()
        mock_complete_async.return_value = Mock()

        # Call _instrument with tracer_provider
        instrumentor._instrument(tracer_provider=mock_tracer_provider)

        # Verify get_tracer was called with custom tracer_provider
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_azure",
            "0.1.0",
            mock_tracer_provider,
            schema_url="https://opentelemetry.io/schemas/1.28.0",
        )

    @patch("lilypad._opentelemetry._opentelemetry_azure.unwrap")
    def test_uninstrument_basic(self, mock_unwrap):
        """Test basic _uninstrument functionality."""
        instrumentor = AzureInstrumentor()

        # Create mock azure modules and classes
        mock_sync_client = Mock(spec=["complete"])
        mock_async_client = Mock(spec=["complete"])

        # Mock the imports
        mock_modules = {
            "azure.ai.inference": Mock(),
            "azure.ai.inference.aio": Mock(),
        }
        mock_modules["azure.ai.inference"].ChatCompletionsClient = mock_sync_client
        mock_modules["azure.ai.inference.aio"].ChatCompletionsClient = mock_async_client

        # Patch the imports
        with patch.dict("sys.modules", mock_modules):
            # Call _uninstrument
            instrumentor._uninstrument()

            # Verify unwrap was called for all methods
            assert mock_unwrap.call_count == 2

            # Check that unwrap was called with the correct objects and method names
            expected_calls = [
                (mock_sync_client, "complete"),
                (mock_async_client, "complete"),
            ]

            actual_calls = mock_unwrap.call_args_list
            for i, expected_call in enumerate(expected_calls):
                assert actual_calls[i][0] == expected_call

    @patch("lilypad._opentelemetry._opentelemetry_azure.unwrap")
    def test_uninstrument_with_kwargs(self, mock_unwrap):
        """Test _uninstrument with additional kwargs."""
        instrumentor = AzureInstrumentor()

        # Create mock azure modules and classes
        mock_sync_client = Mock(spec=["complete"])
        mock_async_client = Mock(spec=["complete"])

        # Mock the imports
        mock_modules = {
            "azure.ai.inference": Mock(),
            "azure.ai.inference.aio": Mock(),
        }
        mock_modules["azure.ai.inference"].ChatCompletionsClient = mock_sync_client
        mock_modules["azure.ai.inference.aio"].ChatCompletionsClient = mock_async_client

        # Patch the imports
        with patch.dict("sys.modules", mock_modules):
            # Call _uninstrument with kwargs (should be ignored)
            instrumentor._uninstrument(some_kwarg="value")

            # Verify unwrap was still called correctly
            assert mock_unwrap.call_count == 2

    @patch(
        "lilypad._opentelemetry._opentelemetry_azure.wrap_function_wrapper",
        side_effect=Exception("Wrapper error"),
    )
    @patch("lilypad._opentelemetry._opentelemetry_azure.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_azure.chat_completions_complete")
    def test_instrument_wrapper_error(self, mock_complete, mock_get_tracer, mock_wrap_function_wrapper):
        """Test _instrument handling of wrapper errors."""
        instrumentor = AzureInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_complete.return_value = Mock()

        # Should raise exception when wrapper fails
        with pytest.raises(Exception, match="Wrapper error"):
            instrumentor._instrument()

    def test_uninstrument_import_error(self):
        """Test _uninstrument handling of import errors."""
        instrumentor = AzureInstrumentor()

        # Patch the import statement to raise ImportError
        with (
            patch("builtins.__import__", side_effect=ImportError("Module not found")),
            pytest.raises(ImportError, match="Module not found"),
        ):
            instrumentor._uninstrument()

    @patch("lilypad._opentelemetry._opentelemetry_azure.unwrap", side_effect=Exception("Unwrap error"))
    def test_uninstrument_unwrap_error(self, mock_unwrap):
        """Test _uninstrument handling of unwrap errors."""
        instrumentor = AzureInstrumentor()

        # Create mock azure modules and classes
        mock_sync_client = Mock(spec=["complete"])
        mock_async_client = Mock(spec=["complete"])

        # Mock the imports
        mock_modules = {
            "azure.ai.inference": Mock(),
            "azure.ai.inference.aio": Mock(),
        }
        mock_modules["azure.ai.inference"].ChatCompletionsClient = mock_sync_client
        mock_modules["azure.ai.inference.aio"].ChatCompletionsClient = mock_async_client

        # Patch the imports
        with patch.dict("sys.modules", mock_modules), pytest.raises(Exception, match="Unwrap error"):
            # Should raise exception when unwrap fails
            instrumentor._uninstrument()

    def test_inheritance(self):
        """Test that AzureInstrumentor properly inherits from BaseInstrumentor."""
        from opentelemetry.instrumentation.instrumentor import BaseInstrumentor

        instrumentor = AzureInstrumentor()
        assert isinstance(instrumentor, BaseInstrumentor)

        # Verify required methods exist
        assert hasattr(instrumentor, "_instrument")
        assert hasattr(instrumentor, "_uninstrument")
        assert hasattr(instrumentor, "instrumentation_dependencies")
        assert callable(instrumentor._instrument)
        assert callable(instrumentor._uninstrument)
        assert callable(instrumentor.instrumentation_dependencies)

    @patch("lilypad._opentelemetry._opentelemetry_azure.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_azure.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_azure.chat_completions_complete")
    @patch("lilypad._opentelemetry._opentelemetry_azure.chat_completions_complete_async")
    def test_instrument_tracer_version_and_schema(
        self,
        mock_complete_async,
        mock_complete,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test that tracer is created with correct version and schema."""
        instrumentor = AzureInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_complete.return_value = Mock()
        mock_complete_async.return_value = Mock()

        instrumentor._instrument()

        # Verify tracer was created with correct parameters
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_azure",
            "0.1.0",  # Instrumentor version
            None,  # tracer_provider (default)
            schema_url="https://opentelemetry.io/schemas/1.28.0",  # Schema URL
        )

    @patch("lilypad._opentelemetry._opentelemetry_azure.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_azure.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_azure.chat_completions_complete")
    @patch("lilypad._opentelemetry._opentelemetry_azure.chat_completions_complete_async")
    def test_instrument_multiple_calls(
        self,
        mock_complete_async,
        mock_complete,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test that _instrument can be called multiple times safely."""
        instrumentor = AzureInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_complete.return_value = Mock()
        mock_complete_async.return_value = Mock()

        # Call _instrument multiple times
        instrumentor._instrument()
        instrumentor._instrument()

        # Verify functions were called multiple times
        assert mock_get_tracer.call_count == 2
        assert mock_wrap_function_wrapper.call_count == 4  # 2 calls per instrument
