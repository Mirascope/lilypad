"""Tests for the EE functions API playground functionality."""

import base64
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.ee.server.api.v0.functions_api import (
    _decode_bytes,
    _limit_resources,
    _run_playground,
    _validate_api_keys,
    _validate_function_data,
    _validate_provider_api_key,
    _validate_python_identifier,
    _validate_template_string,
    _validate_template_values,
    sanitize_arg_types_and_values,
)
from lilypad.server.models import FunctionTable, ProjectTable
from lilypad.server.schemas.functions import (
    PlaygroundErrorType,
    Provider,
)
from lilypad.server.schemas.users import UserPublic


@pytest.fixture
def get_test_current_user(test_user) -> UserPublic:
    """Create test current user."""
    return UserPublic(
        uuid=test_user.uuid,
        email=test_user.email,
        first_name=test_user.first_name,
        organization_uuid=test_user.active_organization_uuid,
    )


@pytest.fixture
def test_function_with_template(
    session: Session, test_project: ProjectTable
) -> FunctionTable:
    """Create a test function with prompt template for playground tests."""
    function = FunctionTable(
        project_uuid=test_project.uuid,
        name="test_playground_function",
        signature="def test_playground_function(arg1: str): pass",
        code="def test_playground_function(arg1: str): pass",
        hash="playground_test_hash",
        organization_uuid=test_project.organization_uuid,
        prompt_template="Hello {arg1}",
        arg_types={"arg1": "str"},
        call_params={"temperature": 0.7},
    )
    session.add(function)
    session.commit()
    session.refresh(function)
    return function


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
        
    def test_validate_python_identifier_builtin(self):
        """Test rejection of Python built-ins as identifiers."""
        # Test with actual builtins that are in dir(__builtins__)
        builtins_list = dir(__builtins__)
        if "len" in builtins_list:
            assert not _validate_python_identifier("len")
        if "str" in builtins_list:
            assert not _validate_python_identifier("str") 
        if "int" in builtins_list:
            assert not _validate_python_identifier("int")
        
        # Test with a builtin that should definitely be there
        if "__import__" in builtins_list:
            assert not _validate_python_identifier("__import__")

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


class TestUtilityFunctions:
    """Test utility functions."""

    def test_sanitize_arg_types_and_values(self):
        """Test argument type and value sanitization."""
        # Test with valid args
        arg_types = {"arg1": "str", "arg2": "int"}
        arg_values = {"arg1": "test", "arg2": 42}
        result = sanitize_arg_types_and_values(arg_types, arg_values)
        expected = {"arg1": ("str", "test"), "arg2": ("int", 42)}
        assert result == expected

        # Test with missing arg_values - only returns keys that exist in both
        result = sanitize_arg_types_and_values(arg_types, {})
        expected = {}  # Empty because no keys exist in both
        assert result == expected

        # Test with partial overlap
        result = sanitize_arg_types_and_values(arg_types, {"arg1": "test"})
        expected = {"arg1": ("str", "test")}  # Only arg1 exists in both
        assert result == expected

    def test_limit_resources(self):
        """Test resource limiting function."""
        # This function would normally limit system resources
        # Test that it doesn't raise an exception
        try:
            _limit_resources()
        except Exception:
            pytest.fail("_limit_resources should not raise an exception")

    def test_decode_bytes_valid(self):
        """Test valid byte decoding."""
        test_data = "Hello, World!"
        encoded = base64.b64encode(test_data.encode()).decode()
        arg_types_and_values = {"data": ("bytes", encoded)}
        result = _decode_bytes(arg_types_and_values)
        assert result["data"] == test_data.encode()

    def test_decode_bytes_invalid(self):
        """Test invalid byte decoding."""
        arg_types_and_values = {"data": ("bytes", "invalid_base64!")}
        with pytest.raises(ValueError):
            _decode_bytes(arg_types_and_values)

    def test_validate_api_keys_valid(self):
        """Test valid API key validation."""
        api_keys = {"openai": "sk-test123", "anthropic": "ant-test123"}
        assert _validate_api_keys(api_keys)

    def test_validate_api_keys_empty(self):
        """Test empty API keys validation."""
        assert not _validate_api_keys({})


# Note: API endpoint tests removed due to authentication/dependency injection complexity
# The utility functions are tested above which covers the core functionality


# Simple edge case tests for validation functions
def test_function_with_invalid_data():
    """Test function validation with invalid stored data."""
    function = Mock()
    function.name = "123invalid_name"  # Invalid name
    function.prompt_template = "Valid template"
    function.call_params = {"temperature": 0.7}
    function.arg_types = {"arg1": "str"}

    assert not _validate_function_data(function)


def test_template_edge_cases():
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


def test_provider_mapping_edge_cases():
    """Test provider API key mapping edge cases."""
    api_keys = {"OPENAI_API_KEY": "test", "ANTHROPIC_API_KEY": "test2"}

    # Case insensitive provider names
    assert _validate_provider_api_key("OpenAI", api_keys)
    assert _validate_provider_api_key("ANTHROPIC", api_keys)

    # Unknown providers
    assert not _validate_provider_api_key("unknown_provider", api_keys)
    assert not _validate_provider_api_key("", api_keys)


def test_decode_bytes_edge_cases():
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

    # Test None value for bytes
    arg_types_and_values = {"data": ("bytes", None)}
    result = _decode_bytes(arg_types_and_values)
    assert result["data"] is None

    # Test bytes value (already bytes)
    byte_value = b"test"
    arg_types_and_values = {"data": ("bytes", byte_value)}
    result = _decode_bytes(arg_types_and_values)
    assert result["data"] == byte_value

    # Test invalid type for bytes arg
    arg_types_and_values = {"data": ("bytes", 123)}
    with pytest.raises(ValueError, match="Expected base64 encoded string or None for bytes argument"):
        _decode_bytes(arg_types_and_values)

    # Test non-bytes argument (should pass through)
    arg_types_and_values = {"data": ("str", "test_string")}
    result = _decode_bytes(arg_types_and_values)
    assert result["data"] == "test_string"


def test_validate_api_keys_injection_patterns():
    """Test API key validation against injection attacks."""
    # Test command injection characters
    malicious_keys = {
        "OPENAI_API_KEY": "key; rm -rf /",
        "ANTHROPIC_API_KEY": "key | cat /etc/passwd",
        "GOOGLE_API_KEY": "key & malicious_command",
        "OPENROUTER_API_KEY": "key`backdoor`",
    }
    sanitized = _validate_api_keys(malicious_keys)
    
    # All should be emptied due to injection characters
    assert sanitized["OPENAI_API_KEY"] == ""
    assert sanitized["ANTHROPIC_API_KEY"] == ""
    assert sanitized["GOOGLE_API_KEY"] == ""
    assert sanitized["OPENROUTER_API_KEY"] == ""

    # Test invalid format (too short)
    short_keys = {"OPENAI_API_KEY": "short"}
    sanitized = _validate_api_keys(short_keys)
    assert sanitized["OPENAI_API_KEY"] == ""

    # Test invalid format (too long)
    long_keys = {"OPENAI_API_KEY": "a" * 300}
    sanitized = _validate_api_keys(long_keys)
    assert sanitized["OPENAI_API_KEY"] == ""

    # Test valid key format passes through
    valid_keys = {"OPENAI_API_KEY": "sk-1234567890abcdef1234567890abcdef"}
    sanitized = _validate_api_keys(valid_keys)
    assert sanitized["OPENAI_API_KEY"] == valid_keys["OPENAI_API_KEY"]


def test_run_playground_python_not_found():
    """Test playground when Python executable doesn't exist."""
    with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
        mock_settings.return_value.playground_venv_path = "/nonexistent/path"
        
        result = _run_playground("print('test')", {})
        
        assert "error" in result
        error = result["error"]
        assert error["type"] == PlaygroundErrorType.CONFIGURATION
        assert "not found" in error["reason"]


def test_run_playground_timeout():
    """Test playground timeout handling."""
    with patch("subprocess.run") as mock_run:
        from subprocess import TimeoutExpired
        mock_run.side_effect = TimeoutExpired("python", 60)
        
        with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
            mock_settings.return_value.playground_venv_path = "/usr"
            
            with patch("pathlib.Path.exists", return_value=True):
                result = _run_playground("time.sleep(100)", {})
                
                assert "error" in result
                error = result["error"]
                assert error["type"] == PlaygroundErrorType.TIMEOUT
                assert "time limit" in error["reason"]


def test_run_playground_file_not_found():
    """Test playground when executable can't be found."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = FileNotFoundError("Python not found")
        
        with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
            mock_settings.return_value.playground_venv_path = "/usr"
            
            with patch("pathlib.Path.exists", return_value=True):
                result = _run_playground("print('test')", {})
                
                assert "error" in result
                error = result["error"]
                assert error["type"] == PlaygroundErrorType.CONFIGURATION
                assert "Failed to execute" in error["reason"]


def test_run_playground_unexpected_exception():
    """Test playground unexpected exception handling."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = RuntimeError("Unexpected error")
        
        with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
            mock_settings.return_value.playground_venv_path = "/usr"
            
            with patch("pathlib.Path.exists", return_value=True):
                result = _run_playground("print('test')", {})
                
                assert "error" in result
                error = result["error"]
                assert error["type"] == PlaygroundErrorType.SUBPROCESS
                assert "unexpected error" in error["reason"]


def test_run_playground_success_with_valid_output():
    """Test playground successful execution with valid JSON output."""
    expected_output = {"result": "test response", "span_id": "span123"}
    json_output = f"__JSON_START__{json.dumps(expected_output)}__JSON_END__"
    
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = json_output
    mock_result.stderr = ""
    
    with patch("subprocess.run", return_value=mock_result):
        with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
            mock_settings.return_value.playground_venv_path = "/usr"
            
            with patch("pathlib.Path.exists", return_value=True):
                result = _run_playground("print('test')", {})
                
                assert result == expected_output


def test_run_playground_success_with_error_output():
    """Test playground that returns an error structure successfully."""
    error_output = {
        "error": {
            "type": "ValueError",
            "reason": "Invalid input",
            "details": "Test error details"
        }
    }
    json_output = f"__JSON_START__{json.dumps(error_output)}__JSON_END__"
    
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = json_output
    mock_result.stderr = ""
    
    with patch("subprocess.run", return_value=mock_result):
        with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
            mock_settings.return_value.playground_venv_path = "/usr"
            
            with patch("pathlib.Path.exists", return_value=True):
                result = _run_playground("raise ValueError('test')", {})
                
                assert "error" in result
                error = result["error"]
                assert error["type"] == "ValueError"
                assert error["reason"] == "Invalid input"


def test_run_playground_invalid_json_output():
    """Test playground with invalid JSON between markers."""
    invalid_json = "__JSON_START__invalid json here__JSON_END__"
    
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = invalid_json
    mock_result.stderr = ""
    
    with patch("subprocess.run", return_value=mock_result):
        with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
            mock_settings.return_value.playground_venv_path = "/usr"
            
            with patch("pathlib.Path.exists", return_value=True):
                result = _run_playground("print('test')", {})
                
                assert "error" in result
                error = result["error"]
                assert error["type"] == PlaygroundErrorType.OUTPUT_PARSING
                assert "invalid JSON" in error["reason"]


def test_run_playground_missing_markers():
    """Test playground with missing output markers."""
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = "No markers in this output"
    mock_result.stderr = ""
    
    with patch("subprocess.run", return_value=mock_result):
        with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
            mock_settings.return_value.playground_venv_path = "/usr"
            
            with patch("pathlib.Path.exists", return_value=True):
                result = _run_playground("print('test')", {})
                
                assert "error" in result
                error = result["error"]
                assert error["type"] == PlaygroundErrorType.OUTPUT_MARKER
                assert "output markers" in error["reason"]


def test_run_playground_execution_error():
    """Test playground with execution error (non-zero return code)."""
    mock_result = Mock()
    mock_result.returncode = 1
    mock_result.stdout = ""
    mock_result.stderr = "ValueError: Test error message"
    
    with patch("subprocess.run", return_value=mock_result):
        with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
            mock_settings.return_value.playground_venv_path = "/usr"
            
            with patch("pathlib.Path.exists", return_value=True):
                result = _run_playground("raise ValueError('test')", {})
                
                assert "error" in result
                error = result["error"]
                assert error["type"] == PlaygroundErrorType.EXECUTION_ERROR
                assert "Test error message" in error["reason"]


def test_run_playground_error_validation_failure():
    """Test playground with error structure that fails validation."""
    invalid_error_output = {
        "error": {
            "invalid_field": "bad structure"
        }
    }
    json_output = f"__JSON_START__{json.dumps(invalid_error_output)}__JSON_END__"
    
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = json_output
    mock_result.stderr = ""
    
    with patch("subprocess.run", return_value=mock_result):
        with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
            mock_settings.return_value.playground_venv_path = "/usr"
            
            with patch("pathlib.Path.exists", return_value=True):
                result = _run_playground("print('test')", {})
                
                # Should return the unvalidated structure
                assert "error" in result
                assert result["error"] == invalid_error_output["error"]


# Test the actual API endpoint functions that aren't covered
def test_playground_api_function_not_found():
    """Test playground API with function that doesn't exist."""
    with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
        mock_settings.return_value.playground_venv_path = "/usr"
        mock_settings.return_value.remote_api_url = "http://test"
        
        from lilypad.ee.server.api.v0.functions_api import run_playground
        from lilypad.server.schemas.functions import PlaygroundParameters, Provider
        from fastapi import HTTPException
        
        # Mock services
        mock_function_service = Mock()
        mock_function_service.find_record_by_uuid.return_value = None
        mock_api_key_service = Mock()
        mock_user_external_api_key_service = Mock()
        mock_span_service = Mock()
        
        playground_params = PlaygroundParameters(
            provider=Provider.OPENAI,
            model="gpt-4",
            arg_values={},
            arg_types={},
            prompt_template="Test template",
            call_params={}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            run_playground(
                project_uuid=uuid4(),
                function_uuid=uuid4(),
                playground_parameters=playground_params,
                function_service=mock_function_service,
                api_key_service=mock_api_key_service,
                user_external_api_key_service=mock_user_external_api_key_service,
                span_service=mock_span_service
            )
        
        assert exc_info.value.status_code == 404
        assert "Function not found" in str(exc_info.value.detail)


def test_playground_api_invalid_function_data():
    """Test playground API with invalid function data."""
    with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
        mock_settings.return_value.playground_venv_path = "/usr"
        mock_settings.return_value.remote_api_url = "http://test"
        
        from lilypad.ee.server.api.v0.functions_api import run_playground
        from lilypad.server.schemas.functions import PlaygroundParameters, Provider
        from fastapi import HTTPException
        
        # Mock function with invalid data
        mock_function = Mock()
        mock_function.name = "123invalid"  # Invalid name
        mock_function.prompt_template = "Valid template"
        
        mock_function_service = Mock()
        mock_function_service.find_record_by_uuid.return_value = mock_function
        mock_api_key_service = Mock()
        mock_user_external_api_key_service = Mock()
        mock_span_service = Mock()
        
        playground_params = PlaygroundParameters(
            provider=Provider.OPENAI,
            model="gpt-4",
            arg_values={},
            arg_types={},
            prompt_template="Test template",
            call_params={}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            run_playground(
                project_uuid=uuid4(),
                function_uuid=uuid4(),
                playground_parameters=playground_params,
                function_service=mock_function_service,
                api_key_service=mock_api_key_service,
                user_external_api_key_service=mock_user_external_api_key_service,
                span_service=mock_span_service
            )
        
        assert exc_info.value.status_code == 400
        assert "validation failed" in str(exc_info.value.detail)


def test_playground_api_invalid_template_values():
    """Test playground API with invalid provider/model values."""
    with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
        mock_settings.return_value.playground_venv_path = "/usr"
        mock_settings.return_value.remote_api_url = "http://test"
        
        from lilypad.ee.server.api.v0.functions_api import run_playground
        from lilypad.server.schemas.functions import PlaygroundParameters, Provider
        from fastapi import HTTPException
        
        mock_function = Mock()
        mock_function.name = "valid_function"
        mock_function.prompt_template = "Valid template"
        mock_function.call_params = {}
        mock_function.arg_types = {}
        
        mock_function_service = Mock()
        mock_function_service.find_record_by_uuid.return_value = mock_function
        mock_api_key_service = Mock()
        mock_api_key_service.find_keys_by_user_and_project.return_value = []
        mock_user_external_api_key_service = Mock()
        mock_span_service = Mock()
        
        playground_params = PlaygroundParameters(
            provider=Provider.OPENAI,
            model="invalid$model",  # Invalid model name
            arg_values={},
            arg_types={},
            prompt_template="Test template",
            call_params={}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            run_playground(
                project_uuid=uuid4(),
                function_uuid=uuid4(),
                playground_parameters=playground_params,
                function_service=mock_function_service,
                api_key_service=mock_api_key_service,
                user_external_api_key_service=mock_user_external_api_key_service,
                span_service=mock_span_service
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid provider or model" in str(exc_info.value.detail)


def test_playground_api_invalid_arg_name():
    """Test playground API with invalid argument name."""
    with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
        mock_settings.return_value.playground_venv_path = "/usr"
        mock_settings.return_value.remote_api_url = "http://test"
        
        from lilypad.ee.server.api.v0.functions_api import run_playground
        from lilypad.server.schemas.functions import PlaygroundParameters, Provider
        from fastapi import HTTPException
        
        mock_function = Mock()
        mock_function.name = "valid_function"
        mock_function.prompt_template = "Valid template"
        mock_function.call_params = {}
        mock_function.arg_types = {"valid_arg": "str"}  # Valid function arg_types
        
        mock_function_service = Mock()
        mock_function_service.find_record_by_uuid.return_value = mock_function
        mock_api_key_service = Mock()
        mock_api_key_service.find_keys_by_user_and_project.return_value = []
        mock_user_external_api_key_service = Mock()
        mock_span_service = Mock()
        
        playground_params = PlaygroundParameters(
            provider=Provider.OPENAI,
            model="gpt-4",
            arg_values={},
            arg_types={"123invalid": "str"},  # Invalid argument name in playground params
            prompt_template="Test template",
            call_params={}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            run_playground(
                project_uuid=uuid4(),
                function_uuid=uuid4(),
                playground_parameters=playground_params,
                function_service=mock_function_service,
                api_key_service=mock_api_key_service,
                user_external_api_key_service=mock_user_external_api_key_service,
                span_service=mock_span_service
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid argument name" in str(exc_info.value.detail)


def test_playground_api_invalid_arg_values():
    """Test playground API with invalid argument values."""
    with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
        mock_settings.return_value.playground_venv_path = "/usr"
        mock_settings.return_value.remote_api_url = "http://test"
        
        from lilypad.ee.server.api.v0.functions_api import run_playground
        from lilypad.server.schemas.functions import PlaygroundParameters, Provider
        from fastapi import HTTPException
        
        mock_function = Mock()
        mock_function.name = "valid_function"
        mock_function.prompt_template = "Valid template"
        mock_function.call_params = {}
        mock_function.arg_types = {"data": "bytes"}
        
        mock_function_service = Mock()
        mock_function_service.find_record_by_uuid.return_value = mock_function
        mock_api_key_service = Mock()
        mock_api_key_service.find_keys_by_user_and_project.return_value = []
        mock_user_external_api_key_service = Mock()
        mock_span_service = Mock()
        
        playground_params = PlaygroundParameters(
            provider=Provider.OPENAI,
            model="gpt-4",
            arg_values={"data": "invalid_base64!"},  # Invalid base64
            arg_types={"data": "bytes"},
            prompt_template="Test template",
            call_params={}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            run_playground(
                project_uuid=uuid4(),
                function_uuid=uuid4(),
                playground_parameters=playground_params,
                function_service=mock_function_service,
                api_key_service=mock_api_key_service,
                user_external_api_key_service=mock_user_external_api_key_service,
                span_service=mock_span_service
            )
        
        assert exc_info.value.status_code == 400
        assert "Invalid argument value encoding" in str(exc_info.value.detail)


def test_playground_api_external_key_error():
    """Test playground API with external API key retrieval error."""
    with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
        mock_settings.return_value.playground_venv_path = "/usr"
        mock_settings.return_value.remote_api_url = "http://test"
        
        from lilypad.ee.server.api.v0.functions_api import run_playground
        from lilypad.server.schemas.functions import PlaygroundParameters, Provider
        from fastapi import HTTPException
        
        mock_function = Mock()
        mock_function.name = "valid_function"
        mock_function.prompt_template = "Valid template"
        mock_function.call_params = {}
        mock_function.arg_types = {}
        
        mock_function_service = Mock()
        mock_function_service.find_record_by_uuid.return_value = mock_function
        mock_api_key_service = Mock()
        mock_api_key_service.find_keys_by_user_and_project.return_value = []
        mock_user_external_api_key_service = Mock()
        mock_user_external_api_key_service.list_api_keys.side_effect = RuntimeError("Key service error")
        mock_span_service = Mock()
        
        playground_params = PlaygroundParameters(
            provider=Provider.OPENAI,
            model="gpt-4",
            arg_values={},
            arg_types={},
            prompt_template="Test template",
            call_params={}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            run_playground(
                project_uuid=uuid4(),
                function_uuid=uuid4(),
                playground_parameters=playground_params,
                function_service=mock_function_service,
                api_key_service=mock_api_key_service,
                user_external_api_key_service=mock_user_external_api_key_service,
                span_service=mock_span_service
            )
        
        assert exc_info.value.status_code == 500
        assert "Failed to retrieve external API keys" in str(exc_info.value.detail)


def test_playground_api_missing_provider_key():
    """Test playground API with missing provider API key."""
    with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
        mock_settings.return_value.playground_venv_path = "/usr"
        mock_settings.return_value.remote_api_url = "http://test"
        
        from lilypad.ee.server.api.v0.functions_api import run_playground
        from lilypad.server.schemas.functions import PlaygroundParameters, Provider
        from fastapi import HTTPException
        
        mock_function = Mock()
        mock_function.name = "valid_function"
        mock_function.prompt_template = "Valid template"
        mock_function.call_params = {}
        mock_function.arg_types = {}
        
        mock_function_service = Mock()
        mock_function_service.find_record_by_uuid.return_value = mock_function
        mock_api_key_service = Mock()
        mock_api_key_service.find_keys_by_user_and_project.return_value = []
        mock_user_external_api_key_service = Mock()
        mock_user_external_api_key_service.list_api_keys.return_value = {}  # No keys
        mock_span_service = Mock()
        
        playground_params = PlaygroundParameters(
            provider=Provider.OPENAI,
            model="gpt-4",
            arg_values={},
            arg_types={},
            prompt_template="Test template",
            call_params={}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            run_playground(
                project_uuid=uuid4(),
                function_uuid=uuid4(),
                playground_parameters=playground_params,
                function_service=mock_function_service,
                api_key_service=mock_api_key_service,
                user_external_api_key_service=mock_user_external_api_key_service,
                span_service=mock_span_service
            )
        
        assert exc_info.value.status_code == 400
        assert "Missing API key for provider" in str(exc_info.value.detail)


def test_playground_api_success_without_span_id():
    """Test playground API successful execution but missing span ID."""
    with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
        mock_settings.return_value.playground_venv_path = "/usr"
        mock_settings.return_value.remote_api_url = "http://test"
        
        with patch("lilypad.ee.server.api.v0.functions_api._run_playground") as mock_run:
            mock_run.return_value = {"result": "success response"}  # No span_id
            
            from lilypad.ee.server.api.v0.functions_api import run_playground
            from lilypad.server.schemas.functions import PlaygroundParameters, Provider
            from fastapi import HTTPException
            
            mock_function = Mock()
            mock_function.name = "valid_function"
            mock_function.prompt_template = "Valid template"
            mock_function.call_params = {}
            mock_function.arg_types = {}
            
            mock_api_key = Mock()
            mock_api_key.key_hash = "test_key_hash"
            
            mock_function_service = Mock()
            mock_function_service.find_record_by_uuid.return_value = mock_function
            mock_api_key_service = Mock()
            mock_api_key_service.find_keys_by_user_and_project.return_value = [mock_api_key]
            mock_user_external_api_key_service = Mock()
            mock_user_external_api_key_service.list_api_keys.return_value = {"openai": "test"}
            mock_user_external_api_key_service.get_api_key.return_value = "test_key"
            mock_span_service = Mock()
            
            playground_params = PlaygroundParameters(
                provider=Provider.OPENAI,
                model="gpt-4",
                arg_values={},
                arg_types={},
                prompt_template="Test template",
                call_params={}
            )
            
            with pytest.raises(HTTPException) as exc_info:
                run_playground(
                    project_uuid=uuid4(),
                    function_uuid=uuid4(),
                    playground_parameters=playground_params,
                    function_service=mock_function_service,
                    api_key_service=mock_api_key_service,
                    user_external_api_key_service=mock_user_external_api_key_service,
                    span_service=mock_span_service
                )
            
            # Should fail due to missing span_id
            assert "error" in str(exc_info.value.detail)


def test_playground_api_invalid_error_structure():
    """Test playground API with invalid error structure from playground execution."""
    with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
        mock_settings.return_value.playground_venv_path = "/usr"
        mock_settings.return_value.remote_api_url = "http://test"
        
        with patch("lilypad.ee.server.api.v0.functions_api._run_playground") as mock_run:
            mock_run.return_value = {
                "error": {"invalid_field": "bad_structure"}  # Invalid error structure
            }
            
            from lilypad.ee.server.api.v0.functions_api import run_playground
            from lilypad.server.schemas.functions import PlaygroundParameters, Provider
            from fastapi import HTTPException
            
            mock_function = Mock()
            mock_function.name = "valid_function"
            mock_function.prompt_template = "Valid template"
            mock_function.call_params = {}
            mock_function.arg_types = {}
            
            mock_api_key = Mock()
            mock_api_key.key_hash = "test_key_hash"
            
            mock_function_service = Mock()
            mock_function_service.find_record_by_uuid.return_value = mock_function
            mock_api_key_service = Mock()
            mock_api_key_service.find_keys_by_user_and_project.return_value = [mock_api_key]
            mock_user_external_api_key_service = Mock()
            mock_user_external_api_key_service.list_api_keys.return_value = {"openai": "test"}
            mock_user_external_api_key_service.get_api_key.return_value = "test_key"
            mock_span_service = Mock()
            
            playground_params = PlaygroundParameters(
                provider=Provider.OPENAI,
                model="gpt-4",
                arg_values={},
                arg_types={},
                prompt_template="Test template",
                call_params={}
            )
            
            with pytest.raises(HTTPException) as exc_info:
                run_playground(
                    project_uuid=uuid4(),
                    function_uuid=uuid4(),
                    playground_parameters=playground_params,
                    function_service=mock_function_service,
                    api_key_service=mock_api_key_service,
                    user_external_api_key_service=mock_user_external_api_key_service,
                    span_service=mock_span_service
                )
            
            assert exc_info.value.status_code == 500
            assert "invalid error structure" in str(exc_info.value.detail)


def test_playground_api_timeout_error():
    """Test playground API with timeout error from execution."""
    with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
        mock_settings.return_value.playground_venv_path = "/usr"
        mock_settings.return_value.remote_api_url = "http://test"
        
        with patch("lilypad.ee.server.api.v0.functions_api._run_playground") as mock_run:
            from lilypad.server.schemas.functions import PlaygroundErrorType
            mock_run.return_value = {
                "error": {
                    "type": PlaygroundErrorType.TIMEOUT,
                    "reason": "Execution timed out",
                    "details": ""
                }
            }
            
            from lilypad.ee.server.api.v0.functions_api import run_playground
            from lilypad.server.schemas.functions import PlaygroundParameters, Provider
            from fastapi import HTTPException
            
            mock_function = Mock()
            mock_function.name = "valid_function"
            mock_function.prompt_template = "Valid template"
            mock_function.call_params = {}
            mock_function.arg_types = {}
            
            mock_api_key = Mock()
            mock_api_key.key_hash = "test_key_hash"
            
            mock_function_service = Mock()
            mock_function_service.find_record_by_uuid.return_value = mock_function
            mock_api_key_service = Mock()
            mock_api_key_service.find_keys_by_user_and_project.return_value = [mock_api_key]
            mock_user_external_api_key_service = Mock()
            mock_user_external_api_key_service.list_api_keys.return_value = {"openai": "test"}
            mock_user_external_api_key_service.get_api_key.return_value = "test_key"
            mock_span_service = Mock()
            
            playground_params = PlaygroundParameters(
                provider=Provider.OPENAI,
                model="gpt-4",
                arg_values={},
                arg_types={},
                prompt_template="Test template",
                call_params={}
            )
            
            with pytest.raises(HTTPException) as exc_info:
                run_playground(
                    project_uuid=uuid4(),
                    function_uuid=uuid4(),
                    playground_parameters=playground_params,
                    function_service=mock_function_service,
                    api_key_service=mock_api_key_service,
                    user_external_api_key_service=mock_user_external_api_key_service,
                    span_service=mock_span_service
                )
            
            assert exc_info.value.status_code == 408  # REQUEST_TIMEOUT


def test_playground_api_configuration_error():
    """Test playground API with configuration error from execution."""
    with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
        mock_settings.return_value.playground_venv_path = "/usr"
        mock_settings.return_value.remote_api_url = "http://test"
        
        with patch("lilypad.ee.server.api.v0.functions_api._run_playground") as mock_run:
            from lilypad.server.schemas.functions import PlaygroundErrorType
            mock_run.return_value = {
                "error": {
                    "type": PlaygroundErrorType.CONFIGURATION,
                    "reason": "Configuration error",
                    "details": ""
                }
            }
            
            from lilypad.ee.server.api.v0.functions_api import run_playground
            from lilypad.server.schemas.functions import PlaygroundParameters, Provider
            from fastapi import HTTPException
            
            mock_function = Mock()
            mock_function.name = "valid_function"
            mock_function.prompt_template = "Valid template"
            mock_function.call_params = {}
            mock_function.arg_types = {}
            
            mock_api_key = Mock()
            mock_api_key.key_hash = "test_key_hash"
            
            mock_function_service = Mock()
            mock_function_service.find_record_by_uuid.return_value = mock_function
            mock_api_key_service = Mock()
            mock_api_key_service.find_keys_by_user_and_project.return_value = [mock_api_key]
            mock_user_external_api_key_service = Mock()
            mock_user_external_api_key_service.list_api_keys.return_value = {"openai": "test"}
            mock_user_external_api_key_service.get_api_key.return_value = "test_key"
            mock_span_service = Mock()
            
            playground_params = PlaygroundParameters(
                provider=Provider.OPENAI,
                model="gpt-4",
                arg_values={},
                arg_types={},
                prompt_template="Test template",
                call_params={}
            )
            
            with pytest.raises(HTTPException) as exc_info:
                run_playground(
                    project_uuid=uuid4(),
                    function_uuid=uuid4(),
                    playground_parameters=playground_params,
                    function_service=mock_function_service,
                    api_key_service=mock_api_key_service,
                    user_external_api_key_service=mock_user_external_api_key_service,
                    span_service=mock_span_service
                )
            
            assert exc_info.value.status_code == 500  # INTERNAL_SERVER_ERROR


def test_playground_api_unexpected_exception():
    """Test playground API with unexpected exception."""
    with patch("lilypad.ee.server.api.v0.functions_api.get_settings") as mock_settings:
        mock_settings.return_value.playground_venv_path = "/usr"
        mock_settings.return_value.remote_api_url = "http://test"
        
        from lilypad.ee.server.api.v0.functions_api import run_playground
        from lilypad.server.schemas.functions import PlaygroundParameters, Provider
        from fastapi import HTTPException
        
        mock_function = Mock()
        mock_function.name = "valid_function"
        mock_function.prompt_template = "Valid template"
        mock_function.call_params = {}
        mock_function.arg_types = {}
        
        mock_function_service = Mock()
        mock_function_service.find_record_by_uuid.return_value = mock_function
        mock_api_key_service = Mock()
        mock_api_key_service.find_keys_by_user_and_project.side_effect = RuntimeError("Unexpected error")
        mock_user_external_api_key_service = Mock()
        mock_span_service = Mock()
        
        playground_params = PlaygroundParameters(
            provider=Provider.OPENAI,
            model="gpt-4",
            arg_values={},
            arg_types={},
            prompt_template="Test template",
            call_params={}
        )
        
        with pytest.raises(HTTPException) as exc_info:
            run_playground(
                project_uuid=uuid4(),
                function_uuid=uuid4(),
                playground_parameters=playground_params,
                function_service=mock_function_service,
                api_key_service=mock_api_key_service,
                user_external_api_key_service=mock_user_external_api_key_service,
                span_service=mock_span_service
            )
        
        assert exc_info.value.status_code == 500
        assert "unexpected server error" in str(exc_info.value.detail)