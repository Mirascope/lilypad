"""Tests for Bedrock instrumentor."""

import pytest
from unittest.mock import Mock, patch
from collections.abc import Collection

from lilypad._opentelemetry._opentelemetry_bedrock import BedrockInstrumentor


class TestBedrockInstrumentor:
    """Test BedrockInstrumentor class."""

    def test_init(self):
        """Test BedrockInstrumentor initialization."""
        instrumentor = BedrockInstrumentor()
        assert isinstance(instrumentor, BedrockInstrumentor)

    def test_instrumentation_dependencies(self):
        """Test instrumentation_dependencies method."""
        instrumentor = BedrockInstrumentor()
        dependencies = instrumentor.instrumentation_dependencies()

        assert isinstance(dependencies, Collection)
        assert len(dependencies) == 2
        assert "aioboto3>=13.2.0,<15" in dependencies
        assert "boto3>=1.35.36,<2" in dependencies

    @patch("lilypad._opentelemetry._opentelemetry_bedrock.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_bedrock.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_bedrock.make_api_call_patch")
    @patch("lilypad._opentelemetry._opentelemetry_bedrock.make_api_call_async_patch")
    def test_instrument_basic(
        self,
        mock_api_call_async_patch,
        mock_api_call_patch,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test basic _instrument functionality."""
        instrumentor = BedrockInstrumentor()

        # Mock tracer
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Mock patch functions
        mock_api_call_wrapper = Mock()
        mock_api_call_async_wrapper = Mock()

        mock_api_call_patch.return_value = mock_api_call_wrapper
        mock_api_call_async_patch.return_value = mock_api_call_async_wrapper

        # Call _instrument
        instrumentor._instrument()

        # Verify get_tracer was called correctly
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_bedrock",
            "0.1.0",
            None,
            schema_url="https://opentelemetry.io/schemas/1.28.0",
        )

        # Verify patch functions were called with tracer
        mock_api_call_patch.assert_called_once_with(mock_tracer)
        mock_api_call_async_patch.assert_called_once_with(mock_tracer)

        # Verify wrap_function_wrapper was called for all methods
        assert mock_wrap_function_wrapper.call_count == 2

        # Check individual wrapper calls
        expected_calls = [
            ("botocore.client", "BaseClient._make_api_call", mock_api_call_wrapper),
            ("aiobotocore.client", "AioBaseClient._make_api_call", mock_api_call_async_wrapper),
        ]

        for i, (module, name, wrapper) in enumerate(expected_calls):
            call_args = mock_wrap_function_wrapper.call_args_list[i]
            assert call_args[0] == (module, name, wrapper)

    @patch("lilypad._opentelemetry._opentelemetry_bedrock.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_bedrock.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_bedrock.make_api_call_patch")
    @patch("lilypad._opentelemetry._opentelemetry_bedrock.make_api_call_async_patch")
    def test_instrument_with_tracer_provider(
        self,
        mock_api_call_async_patch,
        mock_api_call_patch,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test _instrument with custom tracer_provider."""
        instrumentor = BedrockInstrumentor()

        # Mock tracer provider
        mock_tracer_provider = Mock()
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Mock patch functions
        mock_api_call_patch.return_value = Mock()
        mock_api_call_async_patch.return_value = Mock()

        # Call _instrument with tracer_provider
        instrumentor._instrument(tracer_provider=mock_tracer_provider)

        # Verify get_tracer was called with custom tracer_provider
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_bedrock",
            "0.1.0",
            mock_tracer_provider,
            schema_url="https://opentelemetry.io/schemas/1.28.0",
        )

    @patch("lilypad._opentelemetry._opentelemetry_bedrock.unwrap")
    def test_uninstrument_basic(self, mock_unwrap):
        """Test basic _uninstrument functionality."""
        instrumentor = BedrockInstrumentor()

        # Create mock client classes
        mock_base_client = Mock(spec=["_make_api_call"])
        mock_aio_base_client = Mock(spec=["_make_api_call"])

        # Create mock client modules
        mock_botocore_client = Mock()
        mock_botocore_client.BaseClient = mock_base_client

        mock_aiobotocore_client = Mock()
        mock_aiobotocore_client.AioBaseClient = mock_aio_base_client

        # Create main modules with client submodules
        mock_botocore = Mock()
        mock_botocore.client = mock_botocore_client

        mock_aiobotocore = Mock()
        mock_aiobotocore.client = mock_aiobotocore_client

        # Mock the complete module structure
        mock_modules = {
            "botocore": mock_botocore,
            "botocore.client": mock_botocore_client,
            "aiobotocore": mock_aiobotocore,
            "aiobotocore.client": mock_aiobotocore_client,
        }

        # Patch the imports
        with patch.dict("sys.modules", mock_modules):
            # Call _uninstrument
            instrumentor._uninstrument()

            # Verify unwrap was called for all methods
            assert mock_unwrap.call_count == 2

            # Check that unwrap was called with the correct objects and method names
            expected_calls = [
                (mock_base_client, "_make_api_call"),
                (mock_aio_base_client, "_make_api_call"),
            ]

            actual_calls = mock_unwrap.call_args_list
            for i, expected_call in enumerate(expected_calls):
                assert actual_calls[i][0] == expected_call

    @patch("lilypad._opentelemetry._opentelemetry_bedrock.unwrap")
    def test_uninstrument_with_kwargs(self, mock_unwrap):
        """Test _uninstrument with additional kwargs."""
        instrumentor = BedrockInstrumentor()

        # Create mock client classes
        mock_base_client = Mock(spec=["_make_api_call"])
        mock_aio_base_client = Mock(spec=["_make_api_call"])

        # Create mock client modules
        mock_botocore_client = Mock()
        mock_botocore_client.BaseClient = mock_base_client

        mock_aiobotocore_client = Mock()
        mock_aiobotocore_client.AioBaseClient = mock_aio_base_client

        # Create main modules with client submodules
        mock_botocore = Mock()
        mock_botocore.client = mock_botocore_client

        mock_aiobotocore = Mock()
        mock_aiobotocore.client = mock_aiobotocore_client

        # Mock the complete module structure
        mock_modules = {
            "botocore": mock_botocore,
            "botocore.client": mock_botocore_client,
            "aiobotocore": mock_aiobotocore,
            "aiobotocore.client": mock_aiobotocore_client,
        }

        # Patch the imports
        with patch.dict("sys.modules", mock_modules):
            # Call _uninstrument with kwargs (should be ignored)
            instrumentor._uninstrument(some_kwarg="value")

            # Verify unwrap was still called correctly
            assert mock_unwrap.call_count == 2

    @patch(
        "lilypad._opentelemetry._opentelemetry_bedrock.wrap_function_wrapper",
        side_effect=Exception("Wrapper error"),
    )
    @patch("lilypad._opentelemetry._opentelemetry_bedrock.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_bedrock.make_api_call_patch")
    def test_instrument_wrapper_error(self, mock_api_call_patch, mock_get_tracer, mock_wrap_function_wrapper):
        """Test _instrument handling of wrapper errors."""
        instrumentor = BedrockInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_api_call_patch.return_value = Mock()

        # Should raise exception when wrapper fails
        with pytest.raises(Exception, match="Wrapper error"):
            instrumentor._instrument()

    def test_uninstrument_import_error(self):
        """Test _uninstrument handling of import errors."""
        instrumentor = BedrockInstrumentor()

        # Patch the import statement to raise ImportError
        with (
            patch("builtins.__import__", side_effect=ImportError("Module not found")),
            pytest.raises(ImportError, match="Module not found"),
        ):
            instrumentor._uninstrument()

    @patch("lilypad._opentelemetry._opentelemetry_bedrock.unwrap", side_effect=Exception("Unwrap error"))
    def test_uninstrument_unwrap_error(self, mock_unwrap):
        """Test _uninstrument handling of unwrap errors."""
        instrumentor = BedrockInstrumentor()

        # Create mock client classes
        mock_base_client = Mock(spec=["_make_api_call"])
        mock_aio_base_client = Mock(spec=["_make_api_call"])

        # Create mock client modules
        mock_botocore_client = Mock()
        mock_botocore_client.BaseClient = mock_base_client

        mock_aiobotocore_client = Mock()
        mock_aiobotocore_client.AioBaseClient = mock_aio_base_client

        # Create main modules with client submodules
        mock_botocore = Mock()
        mock_botocore.client = mock_botocore_client

        mock_aiobotocore = Mock()
        mock_aiobotocore.client = mock_aiobotocore_client

        # Mock the complete module structure
        mock_modules = {
            "botocore": mock_botocore,
            "botocore.client": mock_botocore_client,
            "aiobotocore": mock_aiobotocore,
            "aiobotocore.client": mock_aiobotocore_client,
        }

        # Patch the imports
        with patch.dict("sys.modules", mock_modules), pytest.raises(Exception, match="Unwrap error"):
            # Should raise exception when unwrap fails
            instrumentor._uninstrument()

    def test_inheritance(self):
        """Test that BedrockInstrumentor properly inherits from BaseInstrumentor."""
        from opentelemetry.instrumentation.instrumentor import BaseInstrumentor

        instrumentor = BedrockInstrumentor()
        assert isinstance(instrumentor, BaseInstrumentor)

        # Verify required methods exist
        assert hasattr(instrumentor, "_instrument")
        assert hasattr(instrumentor, "_uninstrument")
        assert hasattr(instrumentor, "instrumentation_dependencies")
        assert callable(instrumentor._instrument)
        assert callable(instrumentor._uninstrument)
        assert callable(instrumentor.instrumentation_dependencies)

    @patch("lilypad._opentelemetry._opentelemetry_bedrock.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_bedrock.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_bedrock.make_api_call_patch")
    @patch("lilypad._opentelemetry._opentelemetry_bedrock.make_api_call_async_patch")
    def test_instrument_tracer_version_and_schema(
        self,
        mock_api_call_async_patch,
        mock_api_call_patch,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test that tracer is created with correct version and schema."""
        instrumentor = BedrockInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_api_call_patch.return_value = Mock()
        mock_api_call_async_patch.return_value = Mock()

        instrumentor._instrument()

        # Verify tracer was created with correct parameters
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_bedrock",
            "0.1.0",  # Instrumentor version
            None,  # tracer_provider (default)
            schema_url="https://opentelemetry.io/schemas/1.28.0",  # Schema URL
        )

    @patch("lilypad._opentelemetry._opentelemetry_bedrock.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_bedrock.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_bedrock.make_api_call_patch")
    @patch("lilypad._opentelemetry._opentelemetry_bedrock.make_api_call_async_patch")
    def test_instrument_multiple_calls(
        self,
        mock_api_call_async_patch,
        mock_api_call_patch,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test that _instrument can be called multiple times safely."""
        instrumentor = BedrockInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_api_call_patch.return_value = Mock()
        mock_api_call_async_patch.return_value = Mock()

        # Call _instrument multiple times
        instrumentor._instrument()
        instrumentor._instrument()

        # Verify functions were called multiple times
        assert mock_get_tracer.call_count == 2
        assert mock_wrap_function_wrapper.call_count == 4  # 2 calls per instrument
