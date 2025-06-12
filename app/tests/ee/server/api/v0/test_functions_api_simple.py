"""Simple tests for the EE functions API utility functions to achieve coverage."""

import base64
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

# Import the functions to test
from lilypad.ee.server.api.v0.functions_api import (
    _decode_bytes,
    _limit_resources,
    _validate_api_keys,
    _validate_function_data,
    _validate_provider_api_key,
    _validate_python_identifier,
    _validate_template_string,
    _validate_template_values,
    sanitize_arg_types_and_values,
)


class TestValidationFunctions:
    """Test validation utility functions."""

    def test_validate_python_identifier_valid(self):
        """Test valid Python identifiers."""
        assert _validate_python_identifier("valid_name")
        assert _validate_python_identifier("_private")
        assert _validate_python_identifier("CamelCase")
        assert _validate_python_identifier("snake_case_123")

    def test_validate_python_identifier_invalid(self):
        """Test invalid Python identifiers."""
        assert not _validate_python_identifier("")
        assert not _validate_python_identifier("123invalid")
        assert not _validate_python_identifier("invalid-name")
        assert not _validate_python_identifier("invalid.name")
        assert not _validate_python_identifier("class")  # Python keyword

    def test_validate_template_string_valid(self):
        """Test valid template strings."""
        assert _validate_template_string(None)
        assert _validate_template_string("")
        assert _validate_template_string("Hello {name}")
        assert _validate_template_string("Multiple {arg1} and {arg2}")

    def test_validate_template_string_invalid(self):
        """Test invalid template strings."""
        assert not _validate_template_string("Hello {__dunder__}")
        assert not _validate_template_string("Bad {'key': 'value'}")
        assert not _validate_template_string("Escape {\\n}")
        assert not _validate_template_string("Comment {# comment}")
        assert not _validate_template_string("Eval {eval(...)}")
        assert not _validate_template_string("Exec {exec(...)}")
        assert not _validate_template_string("Import {import os}")
        assert not _validate_template_string("File {open(...)}")
        assert not _validate_template_string("System {system(...)}")
        assert not _validate_template_string("Unbalanced {brace")
        assert not _validate_template_string("Invalid {123invalid}")

    def test_validate_template_values_valid(self):
        """Test valid template values."""
        assert _validate_template_values("openai", "gpt-4")
        assert _validate_template_values("anthropic", "claude-3")
        assert _validate_template_values("provider_1.2", "model-name_123")

    def test_validate_template_values_invalid(self):
        """Test invalid template values."""
        assert not _validate_template_values("bad$provider", "model")
        assert not _validate_template_values("provider", "bad$model")
        assert not _validate_template_values("provider;", "model")

    def test_validate_function_data_valid(self):
        """Test valid function data."""
        function = Mock()
        function.name = "valid_function"
        function.prompt_template = "Hello {arg1}"
        function.call_params = {"temperature": 0.7}
        function.arg_types = {"arg1": "str"}
        
        assert _validate_function_data(function)

    def test_validate_function_data_invalid_name(self):
        """Test function data with invalid name."""
        function = Mock()
        function.name = "123invalid"
        function.prompt_template = "Hello {arg1}"
        function.call_params = {"temperature": 0.7}
        function.arg_types = {"arg1": "str"}
        
        assert not _validate_function_data(function)

    def test_validate_function_data_invalid_template(self):
        """Test function data with invalid template."""
        function = Mock()
        function.name = "valid_function"
        function.prompt_template = "Hello {__dunder__}"
        function.call_params = {"temperature": 0.7}
        function.arg_types = {"arg1": "str"}
        
        assert not _validate_function_data(function)

    def test_validate_function_data_invalid_call_params(self):
        """Test function data with non-serializable call_params."""
        function = Mock()
        function.name = "valid_function"
        function.prompt_template = "Hello {arg1}"
        function.call_params = {"func": lambda x: x}  # Not JSON serializable
        function.arg_types = {"arg1": "str"}
        
        assert not _validate_function_data(function)

    def test_validate_function_data_invalid_arg_types(self):
        """Test function data with invalid argument names."""
        function = Mock()
        function.name = "valid_function"
        function.prompt_template = "Hello {arg1}"
        function.call_params = {"temperature": 0.7}
        function.arg_types = {"123invalid": "str"}
        
        assert not _validate_function_data(function)

    def test_validate_api_keys_valid(self):
        """Test API key validation with valid keys."""
        env_vars = {
            "OPENAI_API_KEY": "sk-1234567890abcdef1234567890abcdef",
            "ANTHROPIC_API_KEY": "sk-ant-abcdef1234567890",
            "OTHER_VAR": "some_value",
        }
        
        result = _validate_api_keys(env_vars)
        
        assert "OPENAI_API_KEY" in result
        assert "ANTHROPIC_API_KEY" in result
        assert "OTHER_VAR" in result

    def test_validate_api_keys_invalid_injection(self):
        """Test API key validation removes injection attempts."""
        env_vars = {
            "OPENAI_API_KEY": "sk-test; rm -rf /",
            "ANTHROPIC_API_KEY": "sk-test`whoami`",
            "GOOGLE_API_KEY": "valid_key_with_underscore_and_dash-123",
        }
        
        result = _validate_api_keys(env_vars)
        
        assert result["OPENAI_API_KEY"] == ""
        assert result["ANTHROPIC_API_KEY"] == ""
        assert result["GOOGLE_API_KEY"] == "valid_key_with_underscore_and_dash-123"

    def test_validate_api_keys_invalid_format(self):
        """Test API key validation removes invalid formats."""
        env_vars = {
            "OPENAI_API_KEY": "too_short",
            "ANTHROPIC_API_KEY": "way_too_long_" + "x" * 200,
        }
        
        result = _validate_api_keys(env_vars)
        
        assert result["OPENAI_API_KEY"] == ""
        assert result["ANTHROPIC_API_KEY"] == ""

    def test_validate_provider_api_key_valid(self):
        """Test provider API key validation."""
        api_keys = {
            "OPENAI_API_KEY": "sk-test123",
            "ANTHROPIC_API_KEY": "sk-ant-test123",
        }
        
        assert _validate_provider_api_key("openai", api_keys)
        assert _validate_provider_api_key("anthropic", api_keys)
        assert not _validate_provider_api_key("gemini", api_keys)
        assert not _validate_provider_api_key("unknown", api_keys)

    def test_sanitize_arg_types_and_values(self):
        """Test argument sanitization."""
        arg_types = {"arg1": "str", "arg2": "int", "arg3": "bytes"}
        arg_values = {"arg1": "hello", "arg2": 42, "arg4": "extra"}
        
        result = sanitize_arg_types_and_values(arg_types, arg_values)
        
        expected = {
            "arg1": ("str", "hello"),
            "arg2": ("int", 42),
        }
        assert result == expected


class TestDecodeBytes:
    """Test byte decoding functionality."""

    def test_decode_bytes_valid_base64(self):
        """Test decoding valid base64 strings."""
        test_data = b"hello world"
        encoded = base64.b64encode(test_data).decode("utf-8")
        
        arg_types_and_values = {
            "image": ("bytes", encoded),
            "text": ("str", "hello"),
        }
        
        result = _decode_bytes(arg_types_and_values)
        
        assert result["image"] == test_data
        assert result["text"] == "hello"

    def test_decode_bytes_invalid_base64(self):
        """Test decoding invalid base64 strings."""
        arg_types_and_values = {
            "image": ("bytes", "invalid_base64!"),
        }
        
        with pytest.raises(ValueError, match="Invalid Base64 encoding"):
            _decode_bytes(arg_types_and_values)

    def test_decode_bytes_none_value(self):
        """Test decoding None values."""
        arg_types_and_values = {
            "image": ("bytes", None),
        }
        
        result = _decode_bytes(arg_types_and_values)
        assert result["image"] is None

    def test_decode_bytes_already_bytes(self):
        """Test when value is already bytes."""
        test_data = b"hello world"
        arg_types_and_values = {
            "image": ("bytes", test_data),
        }
        
        result = _decode_bytes(arg_types_and_values)
        assert result["image"] == test_data

    def test_decode_bytes_invalid_type(self):
        """Test when value is wrong type for bytes."""
        arg_types_and_values = {
            "image": ("bytes", 123),  # Invalid type
        }
        
        with pytest.raises(ValueError, match="Expected base64 encoded string"):
            _decode_bytes(arg_types_and_values)


class TestLimitResources:
    """Test resource limiting functionality."""

    @patch("lilypad.ee.server.api.v0.functions_api.CAN_LIMIT_RESOURCES", True)
    @patch("lilypad.ee.server.api.v0.functions_api.resource")
    def test_limit_resources_success(self, mock_resource):
        """Test successful resource limiting."""
        mock_resource.getrlimit.return_value = (8192, 16384)
        
        _limit_resources(180, 8192)
        
        mock_resource.setrlimit.assert_any_call(mock_resource.RLIMIT_CPU, (180, 180))
        mock_resource.setrlimit.assert_any_call(
            mock_resource.RLIMIT_AS, (8192 * 1024 * 1024, 8192 * 1024 * 1024)
        )

    @patch("lilypad.ee.server.api.v0.functions_api.CAN_LIMIT_RESOURCES", False)
    def test_limit_resources_not_available(self):
        """Test when resource limiting is not available."""
        result = _limit_resources(180, 8192)
        assert result is None

    @patch("lilypad.ee.server.api.v0.functions_api.CAN_LIMIT_RESOURCES", True)
    @patch("lilypad.ee.server.api.v0.functions_api.resource")
    def test_limit_resources_exception(self, mock_resource):
        """Test resource limiting with exception."""
        mock_resource.setrlimit.side_effect = Exception("Permission denied")
        
        # Should not raise exception, just log error
        _limit_resources(180, 8192)


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_template_edge_cases(self):
        """Test template validation edge cases."""
        # Empty and None templates should be valid
        assert _validate_template_string(None)
        assert _validate_template_string("")
        
        # Balanced braces
        assert _validate_template_string("No braces")
        assert _validate_template_string("Single {var}")
        assert _validate_template_string("Multiple {var1} and {var2}")
        
        # Unbalanced braces should be invalid
        assert not _validate_template_string("Missing close {var")
        assert not _validate_template_string("Missing open var}")
        assert not _validate_template_string("Too many close {var}}")

    def test_provider_mapping_edge_cases(self):
        """Test provider API key mapping edge cases."""
        api_keys = {"OPENAI_API_KEY": "test", "ANTHROPIC_API_KEY": "test2"}
        
        # Case insensitive provider names
        assert _validate_provider_api_key("OpenAI", api_keys)
        assert _validate_provider_api_key("ANTHROPIC", api_keys)
        
        # Unknown providers
        assert not _validate_provider_api_key("unknown_provider", api_keys)
        assert not _validate_provider_api_key("", api_keys)

    def test_decode_bytes_edge_cases(self):
        """Test byte decoding edge cases."""
        # Empty base64 string
        arg_types_and_values = {"data": ("bytes", "")}
        result = _decode_bytes(arg_types_and_values)
        assert result["data"] == b""
        
        # Valid base64 with padding
        test_data = "test"
        encoded = base64.b64encode(test_data.encode()).decode()
        arg_types_and_values = {"data": ("bytes", encoded)}
        result = _decode_bytes(arg_types_and_values)
        assert result["data"] == test_data.encode()

    def test_api_key_validation_edge_cases(self):
        """Test API key validation edge cases."""
        # Empty values
        env_vars = {"OPENAI_API_KEY": ""}
        result = _validate_api_keys(env_vars)
        assert result["OPENAI_API_KEY"] == ""
        
        # Missing keys
        env_vars = {}
        result = _validate_api_keys(env_vars)
        assert result == {}

    def test_function_data_edge_cases(self):
        """Test function data validation edge cases."""
        # Function with trace_ctx argument (should be ignored)
        function = Mock()
        function.name = "valid_function"
        function.prompt_template = "Hello {arg1}"
        function.call_params = {"temperature": 0.7}
        function.arg_types = {"arg1": "str", "trace_ctx": "TraceContext"}
        
        assert _validate_function_data(function)
        
        # Function with None values
        function = Mock()
        function.name = "valid_function"
        function.prompt_template = None
        function.call_params = None
        function.arg_types = {}
        
        # Should still validate successfully
        assert _validate_function_data(function)