"""Tests for functions schemas."""

import pytest
from pydantic import ValidationError

from lilypad.server.schemas.functions import (
    MAX_DICT_KEYS,
    MAX_LIST_LENGTH,
    MAX_NESTING_DEPTH,
    MAX_STRING_LENGTH,
    PlaygroundErrorDetail,
    PlaygroundErrorType,
    PlaygroundParameters,
    PlaygroundSuccessResponse,
    Provider,
    TraceContextModel,
    _validate_object,
)


class TestValidateObject:
    """Test the _validate_object function."""

    def test_validate_simple_values(self):
        """Test validation of simple values."""
        assert _validate_object(42) == 42
        assert _validate_object(3.14) == 3.14
        assert _validate_object(True) is True
        assert _validate_object("hello") == "hello"

    def test_validate_list(self):
        """Test validation of lists."""
        simple_list = [1, 2, 3, "hello", True]
        assert _validate_object(simple_list) == simple_list

    def test_validate_dict(self):
        """Test validation of dictionaries."""
        simple_dict = {"key1": "value1", "key2": 42, "key3": True}
        assert _validate_object(simple_dict) == simple_dict

    def test_validate_nested_structures(self):
        """Test validation of nested structures."""
        nested = {
            "list": [1, 2, {"nested": "dict"}],
            "dict": {"inner": [3, 4, 5]},
            "value": "simple",
        }
        assert _validate_object(nested) == nested

    def test_max_nesting_depth_exceeded(self):
        """Test that maximum nesting depth is enforced."""
        # Create a deeply nested structure
        nested = "value"
        for _ in range(MAX_NESTING_DEPTH + 2):
            nested = {"key": nested}

        with pytest.raises(ValueError, match="Maximum nesting depth exceeded"):
            _validate_object(nested)

    def test_max_list_length_exceeded(self):
        """Test that maximum list length is enforced."""
        long_list = [1] * (MAX_LIST_LENGTH + 1)

        with pytest.raises(ValueError, match="List exceeds maximum length"):
            _validate_object(long_list)

    def test_max_dict_keys_exceeded(self):
        """Test that maximum dictionary keys limit is enforced."""
        large_dict = {f"key_{i}": i for i in range(MAX_DICT_KEYS + 1)}

        with pytest.raises(ValueError, match="Dictionary exceeds maximum keys"):
            _validate_object(large_dict)

    def test_dict_key_not_string(self):
        """Test that non-string dictionary keys are rejected."""
        invalid_dict = {123: "value"}

        with pytest.raises(ValueError, match="Dictionary keys must be strings"):
            _validate_object(invalid_dict)

    def test_dict_key_too_long(self):
        """Test that overly long dictionary keys are rejected."""
        long_key = "a" * (MAX_STRING_LENGTH + 1)
        invalid_dict = {long_key: "value"}

        with pytest.raises(ValueError, match="Dictionary key too long"):
            _validate_object(invalid_dict)

    def test_string_too_long(self):
        """Test that overly long strings are rejected."""
        long_string = "a" * (MAX_STRING_LENGTH + 1)

        with pytest.raises(ValueError, match="String too long"):
            _validate_object(long_string)

    def test_valid_max_length_values(self):
        """Test that values at the maximum allowed lengths are accepted."""
        # Test string at max length
        max_string = "a" * MAX_STRING_LENGTH
        assert _validate_object(max_string) == max_string

        # Test dict key at max length
        max_key = "k" * MAX_STRING_LENGTH
        max_dict = {max_key: "value"}
        assert _validate_object(max_dict) == max_dict

        # Test list at max length
        max_list = [1] * MAX_LIST_LENGTH
        assert _validate_object(max_list) == max_list

        # Test dict at max keys
        max_keys_dict = {f"k{i}": i for i in range(MAX_DICT_KEYS)}
        assert _validate_object(max_keys_dict) == max_keys_dict

    def test_nested_validation_with_depth_tracking(self):
        """Test that depth is properly tracked through nested validation."""
        # Create a structure that's right at the depth limit
        nested = "value"
        for i in range(MAX_NESTING_DEPTH):
            nested = {"key": nested} if i % 2 == 0 else [nested]

        # This should pass
        result = _validate_object(nested)
        assert result is not None

        # Adding one more level should fail
        nested = {"key": nested}
        with pytest.raises(ValueError, match="Maximum nesting depth exceeded"):
            _validate_object(nested)

    def test_empty_containers(self):
        """Test validation of empty containers."""
        assert _validate_object([]) == []
        assert _validate_object({}) == {}
        assert _validate_object("") == ""


class TestPlaygroundParameters:
    """Test PlaygroundParameters model."""

    def test_valid_playground_parameters(self):
        """Test creation of valid playground parameters."""
        params = PlaygroundParameters(
            arg_values={"arg1": "value1", "arg2": 42},
            arg_types={"arg1": "str", "arg2": "int"},
            provider=Provider.OPENAI,
            model="gpt-4",
            prompt_template="Hello {arg1}",
            call_params={"temperature": 0.7},
        )

        assert params.arg_values == {"arg1": "value1", "arg2": 42}
        assert params.provider == Provider.OPENAI
        assert params.model == "gpt-4"

    def test_playground_parameters_with_none_values(self):
        """Test playground parameters with None values."""
        params = PlaygroundParameters(
            arg_values={},
            arg_types=None,
            provider=Provider.ANTHROPIC,
            model="claude-3",
            prompt_template="Test prompt",
            call_params={},  # Use empty dict instead of None
        )

        assert params.arg_types is None
        assert params.call_params == {}

    def test_playground_parameters_validation_error(self):
        """Test validation error in playground parameters."""
        # Create arg_values that violate validation rules
        large_dict = {f"key_{i}": i for i in range(MAX_DICT_KEYS + 1)}

        with pytest.raises(ValidationError):
            PlaygroundParameters(
                arg_values=large_dict,  # type: ignore
                arg_types=None,
                provider=Provider.OPENAI,
                model="gpt-4",
                prompt_template="Test",
                call_params=None,
            )

    def test_playground_parameters_call_params_validation(self):
        """Test call_params validation in playground parameters."""
        # Test that the field validator works for valid call_params
        params = PlaygroundParameters(
            arg_values={"test": "value"},
            arg_types=None,
            provider=Provider.OPENAI,
            model="gpt-4",
            prompt_template="Test",
            call_params={"temperature": 0.7},
        )
        assert params.call_params == {"temperature": 0.7}
        assert params.arg_values == {"test": "value"}


class TestPlaygroundModels:
    """Test playground-related models."""

    def test_playground_error_detail(self):
        """Test PlaygroundErrorDetail model."""
        error = PlaygroundErrorDetail(
            type=PlaygroundErrorType.TIMEOUT,
            reason="Request timed out",
            details="Execution exceeded 60 seconds",
        )

        assert error.type == PlaygroundErrorType.TIMEOUT
        assert error.reason == "Request timed out"
        assert error.details == "Execution exceeded 60 seconds"

    def test_playground_error_detail_with_string_type(self):
        """Test PlaygroundErrorDetail with string type."""
        error = PlaygroundErrorDetail(
            type="CustomError", reason="Custom error occurred"
        )

        assert error.type == "CustomError"
        assert error.details is None

    def test_trace_context_model(self):
        """Test TraceContextModel."""
        context = TraceContextModel(span_uuid="span-123")
        assert context.span_uuid == "span-123"

        # Test with None
        context_none = TraceContextModel()  # type: ignore
        assert context_none.span_uuid is None

    def test_playground_success_response(self):
        """Test PlaygroundSuccessResponse model."""
        response = PlaygroundSuccessResponse(
            result={"message": "success", "value": 42},
            trace_context=TraceContextModel(span_uuid="span-456"),
        )

        assert response.result == {"message": "success", "value": 42}
        assert response.trace_context.span_uuid == "span-456"  # type: ignore

    def test_playground_success_response_without_trace(self):
        """Test PlaygroundSuccessResponse without trace context."""
        response = PlaygroundSuccessResponse(result="simple result")  # type: ignore

        assert response.result == "simple result"
        assert response.trace_context is None


class TestProviderEnum:
    """Test Provider enum."""

    def test_provider_values(self):
        """Test that all provider values are correct."""
        assert Provider.OPENAI == "openai"
        assert Provider.ANTHROPIC == "anthropic"
        assert Provider.OPENROUTER == "openrouter"
        assert Provider.GEMINI == "gemini"

    def test_provider_in_playground_parameters(self):
        """Test using providers in playground parameters."""
        for provider in Provider:
            params = PlaygroundParameters(
                arg_values={},
                arg_types=None,
                provider=provider,
                model="test-model",
                prompt_template="test",
                call_params={},  # Use empty dict instead of None
            )
            assert params.provider == provider


class TestPlaygroundErrorTypes:
    """Test PlaygroundErrorType enum."""

    def test_error_type_values(self):
        """Test that all error type values are correct."""
        assert PlaygroundErrorType.TIMEOUT == "TimeoutError"
        assert PlaygroundErrorType.CONFIGURATION == "ConfigurationError"
        assert PlaygroundErrorType.SUBPROCESS == "SubprocessError"
        assert PlaygroundErrorType.OUTPUT_PARSING == "OutputParsingError"
        assert PlaygroundErrorType.OUTPUT_MARKER == "OutputMarkerError"
        assert PlaygroundErrorType.INTERNAL == "InternalPlaygroundError"
        assert PlaygroundErrorType.EXECUTION_ERROR == "ExecutionError"
        assert PlaygroundErrorType.BAD_REQUEST == "BadRequestError"
        assert PlaygroundErrorType.NOT_FOUND == "NotFoundError"
        assert PlaygroundErrorType.INVALID_INPUT == "InvalidInputError"
        assert PlaygroundErrorType.API_KEY_ISSUE == "ApiKeyIssue"
        assert PlaygroundErrorType.UNEXPECTED == "UnexpectedServerError"
