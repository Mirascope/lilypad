"""Tests for OpenAI instrumentor."""

from unittest.mock import Mock, patch
from collections.abc import Collection

from lilypad._opentelemetry._opentelemetry_openai import OpenAIInstrumentor


class TestOpenAIInstrumentor:
    """Test OpenAIInstrumentor class."""

    def test_init(self):
        """Test OpenAIInstrumentor initialization."""
        instrumentor = OpenAIInstrumentor()
        assert isinstance(instrumentor, OpenAIInstrumentor)

    def test_instrumentation_dependencies(self):
        """Test instrumentation_dependencies method."""
        instrumentor = OpenAIInstrumentor()
        dependencies = instrumentor.instrumentation_dependencies()

        assert isinstance(dependencies, Collection)
        assert len(dependencies) == 1
        assert "openai>=1.6.0,<2" in dependencies

    @patch("lilypad._opentelemetry._opentelemetry_openai.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_openai.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_create")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_create_async")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_parse")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_parse_async")
    def test_instrument_basic(
        self,
        mock_parse_async,
        mock_parse,
        mock_create_async,
        mock_create,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test basic _instrument functionality."""
        instrumentor = OpenAIInstrumentor()

        # Mock tracer
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Mock patch functions
        mock_create_wrapper = Mock()
        mock_create_async_wrapper = Mock()
        mock_parse_wrapper = Mock()
        mock_parse_async_wrapper = Mock()

        mock_create.return_value = mock_create_wrapper
        mock_create_async.return_value = mock_create_async_wrapper
        mock_parse.return_value = mock_parse_wrapper
        mock_parse_async.return_value = mock_parse_async_wrapper

        mock_wrap_function_wrapper.side_effect = [None, None, None, None]

        # Call _instrument
        instrumentor._instrument()

        # Verify get_tracer was called correctly
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_openai",
            "0.1.0",
            None,
            schema_url="https://opentelemetry.io/schemas/1.28.0",
        )

        # Verify patch functions were called with tracer
        assert mock_create.call_count == 1
        assert mock_create_async.call_count == 1
        assert mock_parse.call_count == 1
        assert mock_parse_async.call_count == 1

        # Verify wrap_function_wrapper was called for all methods
        assert mock_wrap_function_wrapper.call_count == 4

        # Check individual wrapper calls
        expected_calls = [
            ("openai.resources.chat.completions", "Completions.create", mock_create_wrapper),
            ("openai.resources.chat.completions", "AsyncCompletions.create", mock_create_async_wrapper),
            ("openai.resources.chat.completions", "Completions.parse", mock_parse_wrapper),
            ("openai.resources.chat.completions", "AsyncCompletions.parse", mock_parse_async_wrapper),
        ]

        for i, (module, name, wrapper) in enumerate(expected_calls):
            call_args = mock_wrap_function_wrapper.call_args_list[i]
            call_kwargs = call_args[1]
            assert call_kwargs["module"] == module
            assert call_kwargs["name"] == name
            assert call_kwargs["wrapper"] == wrapper

    @patch("lilypad._opentelemetry._opentelemetry_openai.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_openai.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_create")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_create_async")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_parse")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_parse_async")
    def test_instrument_parse_in_beta(
        self,
        mock_parse_async,
        mock_parse,
        mock_create_async,
        mock_create,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test _instrument functionality when parse is in beta (OpenAI < 1.92.0)."""
        instrumentor = OpenAIInstrumentor()

        # Mock tracer
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Mock patch functions
        mock_create_wrapper = Mock()
        mock_create_async_wrapper = Mock()
        mock_parse_wrapper = Mock()
        mock_parse_async_wrapper = Mock()

        mock_create.return_value = mock_create_wrapper
        mock_create_async.return_value = mock_create_async_wrapper
        mock_parse.return_value = mock_parse_wrapper
        mock_parse_async.return_value = mock_parse_async_wrapper

        # Simulate that parse is NOT in non-beta location (OpenAI < 1.92.0)
        # First two calls succeed (create methods), next two fail (non-beta parse), last two succeed (beta parse)
        def side_effect(*args, **kwargs):
            module = kwargs.get("module", "")
            name = kwargs.get("name", "")
            if "beta" not in module and "parse" in name.lower():
                raise ImportError("No module named 'openai.resources.chat.completions.parse'")
            return None

        mock_wrap_function_wrapper.side_effect = side_effect

        instrumentor._instrument()

        assert mock_wrap_function_wrapper.call_count == 6

        parse_calls = [call for call in mock_wrap_function_wrapper.call_args_list if "parse" in str(call)]
        beta_parse_calls = [call for call in parse_calls if "beta" in call[1]["module"]]
        assert len(beta_parse_calls) == 2

    @patch("lilypad._opentelemetry._opentelemetry_openai.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_openai.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_create")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_create_async")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_parse")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_parse_async")
    def test_instrument_with_tracer_provider(
        self,
        mock_parse_async,
        mock_parse,
        mock_create_async,
        mock_create,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test _instrument with custom tracer_provider."""
        instrumentor = OpenAIInstrumentor()

        # Mock tracer provider
        mock_tracer_provider = Mock()
        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer

        # Mock patch functions
        mock_create.return_value = Mock()
        mock_create_async.return_value = Mock()
        mock_parse.return_value = Mock()
        mock_parse_async.return_value = Mock()

        # Call _instrument with tracer_provider
        instrumentor._instrument(tracer_provider=mock_tracer_provider)

        # Verify get_tracer was called with custom tracer_provider
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_openai",
            "0.1.0",
            mock_tracer_provider,
            schema_url="https://opentelemetry.io/schemas/1.28.0",
        )

    @patch("lilypad._opentelemetry._opentelemetry_openai.unwrap")
    def test_uninstrument_basic(self, mock_unwrap):
        """Test basic _uninstrument functionality."""
        instrumentor = OpenAIInstrumentor()

        # Create mock openai module structure for OpenAI >= 1.92.0
        # where parse is in non-beta location
        mock_openai = Mock()
        mock_completions = Mock(spec=["create", "parse"])
        mock_async_completions = Mock(spec=["create", "parse"])

        mock_openai.resources.chat.completions.Completions = mock_completions
        mock_openai.resources.chat.completions.AsyncCompletions = mock_async_completions

        # Add beta structure too (will fail to unwrap but that's expected)
        mock_beta_completions = Mock(spec=[])
        mock_beta_async_completions = Mock(spec=[])
        mock_openai.resources.beta.chat.completions.Completions = mock_beta_completions
        mock_openai.resources.beta.chat.completions.AsyncCompletions = mock_beta_async_completions

        # Patch the import to return our mock
        with patch.dict("sys.modules", {"openai": mock_openai}):
            # Call _uninstrument
            instrumentor._uninstrument()

            # Verify unwrap was called for methods that exist
            assert mock_unwrap.call_count == 4

            # Check that unwrap was called with the correct method names
            method_names = []
            for call in mock_unwrap.call_args_list:
                method_names.append(call[0][1])  # Second argument is method name

            expected_methods = ["create", "create", "parse", "parse"]
            assert method_names == expected_methods

    @patch("lilypad._opentelemetry._opentelemetry_openai.unwrap")
    def test_uninstrument_parse_in_beta(self, mock_unwrap):
        """Test _uninstrument when parse is in beta (OpenAI < 1.92.0)."""
        instrumentor = OpenAIInstrumentor()

        # Create mock openai module structure for OpenAI < 1.92.0
        mock_openai = Mock()
        mock_completions = Mock(spec=["create"])
        mock_async_completions = Mock(spec=["create"])
        mock_beta_completions = Mock(spec=["parse"])
        mock_beta_async_completions = Mock(spec=["parse"])

        mock_openai.resources.chat.completions.Completions = mock_completions
        mock_openai.resources.chat.completions.AsyncCompletions = mock_async_completions
        mock_openai.resources.beta.chat.completions.Completions = mock_beta_completions
        mock_openai.resources.beta.chat.completions.AsyncCompletions = mock_beta_async_completions

        with patch.dict("sys.modules", {"openai": mock_openai}):
            instrumentor._uninstrument()

            assert mock_unwrap.call_count == 4

            unwrapped_targets = []
            for call in mock_unwrap.call_args_list:
                target = call[0][0]
                method = call[0][1]
                unwrapped_targets.append((target, method))

            assert any(method == "create" for _, method in unwrapped_targets)
            assert any(method == "parse" for _, method in unwrapped_targets)

    @patch("lilypad._opentelemetry._opentelemetry_openai.unwrap")
    def test_uninstrument_with_kwargs(self, mock_unwrap):
        """Test _uninstrument with additional kwargs."""
        instrumentor = OpenAIInstrumentor()

        # Create mock openai module structure
        mock_openai = Mock()
        mock_completions = Mock(spec=["create", "parse"])
        mock_async_completions = Mock(spec=["create", "parse"])

        mock_openai.resources.chat.completions.Completions = mock_completions
        mock_openai.resources.chat.completions.AsyncCompletions = mock_async_completions

        # Add beta structure for completeness
        mock_openai.resources.beta.chat.completions.Completions = Mock(spec=[])
        mock_openai.resources.beta.chat.completions.AsyncCompletions = Mock(spec=[])

        # Patch the import to return our mock
        with patch.dict("sys.modules", {"openai": mock_openai}):
            # Call _uninstrument with kwargs (should be ignored)
            instrumentor._uninstrument(some_kwarg="value")

            # Verify unwrap was still called correctly
            assert mock_unwrap.call_count == 4  # 2 create + 2 parse from non-beta

    @patch(
        "lilypad._opentelemetry._opentelemetry_openai.wrap_function_wrapper",
        side_effect=Exception("Wrapper error"),
    )
    @patch("lilypad._opentelemetry._opentelemetry_openai.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_create")
    def test_instrument_wrapper_error(self, mock_create, mock_get_tracer, mock_wrap_function_wrapper):
        """Test _instrument handling of wrapper errors."""
        instrumentor = OpenAIInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_create.return_value = Mock()

        instrumentor._instrument()

        assert mock_wrap_function_wrapper.call_count >= 4  # At least 4 attempts

    def test_uninstrument_import_error(self):
        """Test _uninstrument handling of import errors."""
        instrumentor = OpenAIInstrumentor()

        # Patch the import statement to raise ImportError
        with patch("builtins.__import__", side_effect=ImportError("Module not found")):
            instrumentor._uninstrument()

    @patch("lilypad._opentelemetry._opentelemetry_openai.unwrap", side_effect=Exception("Unwrap error"))
    def test_uninstrument_unwrap_error(self, mock_unwrap):
        """Test _uninstrument handling of unwrap errors."""
        instrumentor = OpenAIInstrumentor()

        # Create mock openai module structure
        mock_openai = Mock()
        mock_completions = Mock(spec=["create", "parse"])
        mock_async_completions = Mock(spec=["create", "parse"])

        mock_openai.resources.chat.completions.Completions = mock_completions
        mock_openai.resources.chat.completions.AsyncCompletions = mock_async_completions
        mock_openai.resources.beta.chat.completions.Completions = Mock(spec=["parse"])
        mock_openai.resources.beta.chat.completions.AsyncCompletions = Mock(spec=["parse"])

        # Patch the import to return our mock
        with patch.dict("sys.modules", {"openai": mock_openai}):
            # Should not raise exception when unwrap fails - errors are caught and logged
            instrumentor._uninstrument()

            assert mock_unwrap.call_count > 0

    def test_inheritance(self):
        """Test that OpenAIInstrumentor properly inherits from BaseInstrumentor."""
        from opentelemetry.instrumentation.instrumentor import BaseInstrumentor

        instrumentor = OpenAIInstrumentor()
        assert isinstance(instrumentor, BaseInstrumentor)

        # Verify required methods exist
        assert hasattr(instrumentor, "_instrument")
        assert hasattr(instrumentor, "_uninstrument")
        assert hasattr(instrumentor, "instrumentation_dependencies")
        assert callable(instrumentor._instrument)
        assert callable(instrumentor._uninstrument)
        assert callable(instrumentor.instrumentation_dependencies)

    @patch("lilypad._opentelemetry._opentelemetry_openai.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_openai.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_create")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_create_async")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_parse")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_parse_async")
    def test_instrument_tracer_version_and_schema(
        self,
        mock_parse_async,
        mock_parse,
        mock_create_async,
        mock_create,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test that tracer is created with correct version and schema."""
        instrumentor = OpenAIInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_create.return_value = Mock()
        mock_create_async.return_value = Mock()
        mock_parse.return_value = Mock()
        mock_parse_async.return_value = Mock()

        instrumentor._instrument()

        # Verify tracer was created with correct parameters
        mock_get_tracer.assert_called_once_with(
            "lilypad._opentelemetry._opentelemetry_openai",
            "0.1.0",  # Instrumentor version
            None,  # tracer_provider (default)
            schema_url="https://opentelemetry.io/schemas/1.28.0",  # Schema URL
        )

    @patch("lilypad._opentelemetry._opentelemetry_openai.get_tracer")
    @patch("lilypad._opentelemetry._opentelemetry_openai.wrap_function_wrapper")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_create")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_create_async")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_parse")
    @patch("lilypad._opentelemetry._opentelemetry_openai.chat_completions_parse_async")
    def test_instrument_multiple_calls(
        self,
        mock_parse_async,
        mock_parse,
        mock_create_async,
        mock_create,
        mock_wrap_function_wrapper,
        mock_get_tracer,
    ):
        """Test that _instrument can be called multiple times safely."""
        instrumentor = OpenAIInstrumentor()

        mock_tracer = Mock()
        mock_get_tracer.return_value = mock_tracer
        mock_create.return_value = Mock()
        mock_create_async.return_value = Mock()
        mock_parse.return_value = Mock()
        mock_parse_async.return_value = Mock()

        # Call _instrument multiple times
        instrumentor._instrument()
        instrumentor._instrument()

        # Verify functions were called multiple times
        assert mock_get_tracer.call_count == 2
        assert mock_wrap_function_wrapper.call_count == 8  # 4 successful calls per instrument

    @patch("lilypad._opentelemetry._opentelemetry_openai.logger")
    @patch("lilypad._opentelemetry._opentelemetry_openai.wrap_function_wrapper")
    def test_wrap_parse_methods_version_exception(
        self,
        mock_wrap_function_wrapper,
        mock_logger,
    ):
        """Test _wrap_parse_methods when getting OpenAI version raises exception."""
        instrumentor = OpenAIInstrumentor()

        # Mock tracer
        mock_tracer = Mock()

        # Make all wrap attempts fail to trigger version check
        mock_wrap_function_wrapper.side_effect = Exception("Failed to wrap")

        # Mock openai module that raises exception when accessing __version__
        with patch.dict("sys.modules", {"openai": Mock(side_effect=Exception("Import error"))}):
            # Call _wrap_parse_methods directly
            instrumentor._wrap_parse_methods(mock_tracer)

            # Verify warning was logged
            warning_calls = mock_logger.warning.call_args_list
            assert len(warning_calls) == 1
            # The warning message should not contain version info since the exception occurred
            warning_msg = warning_calls[0][0][0]
            # Should not have version info in parentheses
            assert "(OpenAI SDK version:" not in warning_msg
            assert warning_msg.endswith("This may be due to OpenAI SDK version incompatibility.")
