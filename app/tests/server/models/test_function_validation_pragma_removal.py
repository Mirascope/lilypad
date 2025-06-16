"""Tests for function model validation to remove pragma: no cover comments."""

from unittest.mock import patch

import pytest
from pydantic import ValidationError

from lilypad.server.models.functions import _FunctionBase
from lilypad.server.schemas.functions import FunctionCreate


class TestFunctionValidationErrors:
    """Test function validation error cases that currently have pragma: no cover."""

    def test_function_name_too_long(self):
        """Test function name validation - exceeds 512 characters."""
        long_name = "x" * 513  # Over 512 character limit

        with pytest.raises(ValidationError) as exc_info:
            FunctionCreate(
                name=long_name,
                signature=f"def {long_name}() -> None: ...",
                code=f"def {long_name}(): pass",
                hash="test_hash",
            )

        assert "String should have at most 512 characters" in str(exc_info.value)

    def test_function_arg_type_too_long(self):
        """Test function argument type validation - exceeds max length.

        Note: The validate_arg_types method has duplicate validation for arg_type length:
        - Lines 106-109 check: if len(value[arg_name]) > MAX_TYPE_NAME_LENGTH
        - Lines 117-120 check: if len(arg_type) > MAX_TYPE_NAME_LENGTH (unreachable)

        Since arg_type and value[arg_name] are the same value in the loop,
        the first check (line 107) will always trigger before line 118.
        """
        long_type = "x" * 101  # Over MAX_TYPE_NAME_LENGTH (100)

        with pytest.raises(ValidationError) as exc_info:
            FunctionCreate(
                name="test_function",
                signature="def test_function(param1: str) -> None: ...",
                code="def test_function(param1): pass",
                hash="test_hash",
                arg_types={"param1": long_type},
            )

        assert (
            f"Invalid type name: '{long_type}'. Must be less than 100 characters."
            in str(exc_info.value)
        )

    def test_function_name_invalid_identifier(self):
        """Test function name validation - invalid Python identifier."""
        with pytest.raises(ValidationError) as exc_info:
            FunctionCreate(
                name="123invalid",  # Starts with number
                signature="def 123invalid() -> None: ...",
                code="def 123invalid(): pass",
                hash="test_hash",
            )

        assert "Name must be a valid Python identifier" in str(exc_info.value)

    def test_function_name_python_keyword(self):
        """Test function name validation - Python keyword."""
        with pytest.raises(ValidationError) as exc_info:
            FunctionCreate(
                name="def",  # Python keyword
                signature="def def() -> None: ...",
                code="def def(): pass",
                hash="test_hash",
            )

        assert "Name must not be a Python keyword" in str(exc_info.value)

    def test_function_name_with_whitespace(self):
        """Test function name validation - contains whitespace."""
        with pytest.raises(ValidationError) as exc_info:
            FunctionCreate(
                name="function with spaces",
                signature="def function_with_spaces() -> None: ...",
                code="def function_with_spaces(): pass",
                hash="test_hash",
            )

        assert "Name must be a valid Python identifier" in str(exc_info.value)

    def test_function_name_with_special_chars(self):
        """Test function name validation - contains special characters."""
        with pytest.raises(ValidationError) as exc_info:
            FunctionCreate(
                name="function-name",  # Hyphen not allowed
                signature="def function_name() -> None: ...",
                code="def function_name(): pass",
                hash="test_hash",
            )

        assert "Name must be a valid Python identifier" in str(exc_info.value)

    def test_function_arg_name_python_keyword(self):
        """Test function argument name validation - Python keyword."""
        with pytest.raises(ValidationError) as exc_info:
            FunctionCreate(
                name="test_function",
                signature="def test_function(param: str) -> None: ...",
                code="def test_function(param): pass",
                hash="test_hash",
                arg_types={
                    "def": "str"  # Python keyword as argument name
                },
            )

        assert "Name must not be a Python keyword" in str(exc_info.value)

    def test_valid_function_creation(self):
        """Test valid function creation (positive test case)."""
        # This should NOT raise an exception
        function = FunctionCreate(
            name="valid_function_name",
            signature="def valid_function_name(param1: str, param2: int) -> None: ...",
            code="def valid_function_name(param1, param2): pass",
            hash="test_hash",
            arg_types={"param1": "str", "param2": "int"},
        )

        assert function.name == "valid_function_name"
        assert "param1" in function.arg_types
        assert function.arg_types["param1"] == "str"

    def test_function_name_edge_case_512_chars(self):
        """Test function name validation - exactly 512 characters (should pass)."""
        name_512_chars = "x" * 512  # Exactly 512 characters

        # This should NOT raise an exception
        function = FunctionCreate(
            name=name_512_chars,
            signature=f"def {name_512_chars}() -> None: ...",
            code=f"def {name_512_chars}(): pass",
            hash="test_hash",
        )

        assert len(function.name) == 512

    def test_function_arg_type_edge_case_1000_chars(self):
        """Test function argument type validation - exactly 100 characters (should pass)."""
        type_100_chars = "x" * 100  # Exactly 100 characters

        # This should NOT raise an exception
        function = FunctionCreate(
            name="test_function",
            signature="def test_function(param1: str) -> None: ...",
            code="def test_function(param1): pass",
            hash="test_hash",
            arg_types={"param1": type_100_chars},
        )

        assert len(function.arg_types["param1"]) == 100

    def test_function_name_length_validation_direct(self):
        """Test custom name length validation using field_validator directly."""
        validator = _FunctionBase.validate_name

        # Create a name that's too long
        long_name = "x" * 513  # Over 512 characters

        with pytest.raises(ValueError) as exc_info:
            validator(long_name)

        assert "Name must be less than 512 characters." in str(exc_info.value)

    def test_function_parsed_args_mismatch_validation(self):
        """Test when parsed arguments don't match provided arg_types."""
        with patch(
            "lilypad.server.models.functions.extract_function_info"
        ) as mock_extract:
            # Make extract_function_info return different args than what we provided
            mock_extract.return_value = ("test_func", {"different_param": "str"})

            with pytest.raises(ValueError) as exc_info:
                FunctionCreate(
                    name="test_func",
                    signature="def test_func(param: str) -> None: ...",
                    code="def test_func(param): pass",
                    hash="hash123",
                    arg_types={
                        "param": "str"
                    },  # This won't match {"different_param": "str"}
                )

            error_msg = str(exc_info.value)
            assert "Function arguments" in error_msg
            assert "do not match parsed arguments" in error_msg

    def test_function_invalid_name_pattern(self):
        """Test function with invalid name pattern (starts with __)."""
        with pytest.raises(ValidationError) as exc_info:
            FunctionCreate(
                name="__invalid__",  # Starts with __
                signature="def __invalid__(): pass",
                code="def __invalid__(): pass",
                hash="test_hash",
                arg_types={},
            )

        assert "Name must be a valid Python identifier" in str(exc_info.value)
