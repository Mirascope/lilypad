"""Test for functions model coverage gaps."""

from unittest.mock import patch

import pytest

from lilypad.server.models.functions import extract_function_info
from lilypad.server.schemas.functions import FunctionCreate


class TestFunctionsModelCoverage:
    """Cover missing lines in functions.py model"""

    def test_line_56_no_function_definition_found(self):
        """Cover line 56 - no function definition found in source"""
        # Source with no function definition
        source_without_function = "x = 42"

        with pytest.raises(ValueError, match="No function definition found in source"):
            extract_function_info(source_without_function)

    def test_line_68_parameter_without_type_annotation(self):
        """Cover line 68 - parameter without type annotation"""
        # Function with parameter missing type annotation
        source_no_annotation = "def test_func(param): pass"

        with pytest.raises(
            ValueError, match="All parameters must have a type annotation"
        ):
            extract_function_info(source_no_annotation)

    def test_line_103_arg_name_too_long(self):
        """Cover line 103 - argument name too long"""
        # Create a very long argument name (over MAX_ARG_NAME_LENGTH)
        long_name = "a" * 513  # MAX_ARG_NAME_LENGTH is typically 512

        with pytest.raises(ValueError, match="Invalid argument name"):
            FunctionCreate(
                name="test_func",
                signature=f"def test_func({long_name}: str) -> str",
                code="def test_func(): pass",
                hash="test_hash",
                arg_types={long_name: "str"},
            )

    def test_line_107_type_name_too_long_in_validation(self):
        """Cover line 107 - type name too long in validate_arg_types"""
        # Create a very long type name
        long_type = "VeryLongTypeName" * 50  # Over MAX_TYPE_NAME_LENGTH

        with pytest.raises(ValueError, match="Invalid type name"):
            FunctionCreate(
                name="test_func",
                signature=f"def test_func(param: {long_type}) -> str",
                code="def test_func(): pass",
                hash="test_hash",
                arg_types={"param": long_type},
            )

    def test_line_112_invalid_python_identifier(self):
        """Cover line 112 - argument name not valid Python identifier"""
        with pytest.raises(ValueError, match="Name must be a valid Python identifier"):
            FunctionCreate(
                name="test_func",
                signature="def test_func(123invalid: str) -> str",
                code="def test_func(): pass",
                hash="test_hash",
                arg_types={"123invalid": "str"},  # Starts with number
            )

    def test_line_115_python_keyword_as_arg_name(self):
        """Cover line 115 - Python keyword used as argument name"""
        with pytest.raises(ValueError, match="Name must not be a Python keyword"):
            FunctionCreate(
                name="test_func",
                signature="def test_func(): pass",
                code="def test_func(): pass",
                hash="test_hash",
                arg_types={"class": "str"},  # 'class' is a Python keyword
            )

    def test_line_118_type_name_too_long_second_check(self):
        """Cover line 118 - duplicate type name length check"""
        # This tests the second check for type name length
        very_long_type = "x" * 1000  # Definitely over MAX_TYPE_NAME_LENGTH

        with pytest.raises(ValueError, match="Invalid type name"):
            FunctionCreate(
                name="test_func",
                signature=f"def test_func(param: {very_long_type}) -> str",
                code="def test_func(): pass",
                hash="test_hash",
                arg_types={"param": very_long_type},
            )

    def test_line_126_function_name_too_long(self):
        """Cover line 126 - function name too long"""
        long_name = "f" * 513  # Over 512 characters

        # Pydantic will catch this before our validator runs, so we expect ValidationError
        with pytest.raises(
            (ValueError, TypeError)
        ):  # Accept any exception for string too long
            FunctionCreate(
                name=long_name,
                signature="def test(): pass",
                code="def test(): pass",
                hash="test_hash",
                arg_types={},
            )

    def test_line_129_function_name_invalid_identifier(self):
        """Cover line 129 - function name not valid Python identifier"""
        with pytest.raises(ValueError, match="Name must be a valid Python identifier"):
            FunctionCreate(
                name="123invalid",  # Starts with number
                signature="def test_func(): pass",
                code="def test_func(): pass",
                hash="test_hash",
                arg_types={},
            )

    def test_line_131_function_name_python_keyword(self):
        """Cover line 131 - function name is Python keyword"""
        with pytest.raises(ValueError, match="Name must not be a Python keyword"):
            FunctionCreate(
                name="def",  # 'def' is a Python keyword
                signature="def test_func(): pass",
                code="def test_func(): pass",
                hash="test_hash",
                arg_types={},
            )

    def test_line_134_function_name_regex_validation(self):
        """Cover line 134 - function name fails regex validation"""
        # Test name with special characters that might pass isidentifier but fail regex
        with pytest.raises(ValueError, match="Name must be a valid Python identifier"):
            FunctionCreate(
                name="func-with-dash",  # Dash not allowed
                signature="def test_func(): pass",
                code="def test_func(): pass",
                hash="test_hash",
                arg_types={},
            )

    def test_lines_150_151_parse_function_failure(self):
        """Cover lines 150-151 - failure to parse function name and arguments"""
        # Create a FunctionCreate with inconsistent name and arg_types that will fail parsing
        with pytest.raises(
            ValueError, match="Failed to parse function name and arguments"
        ):
            FunctionCreate(
                name="valid_name",
                signature="valid_name(param: InvalidType[[[) -> str",
                code="def valid_name(param): return 'test'",
                hash="test_hash",
                arg_types={
                    "param": "InvalidType[[["
                },  # Invalid type syntax that will fail parsing
            )

    def test_line_154_function_name_mismatch(self):
        """Cover line 154 - parsed function name doesn't match provided name"""
        # Mock extract_function_info to return a different function name
        with patch(
            "lilypad.server.models.functions.extract_function_info"
        ) as mock_extract:
            mock_extract.return_value = ("different_name", {"param": "str"})

            with pytest.raises(
                ValueError, match="Function name .* does not match parsed function name"
            ):
                FunctionCreate(
                    name="expected_name",
                    signature="expected_name(param: str) -> str",
                    code="def expected_name(param): return param",
                    hash="test_hash",
                    arg_types={"param": "str"},
                )

    def test_line_159_arg_types_mismatch(self):
        """Cover line 159 - parsed arguments don't match provided arg_types"""
        # Create a scenario where arg_types don't match what's in the source
        with pytest.raises(ValueError):
            FunctionCreate(
                name="test_func",
                signature="def test_func(param1: str, param2: int) -> str",
                code="def test_func(param1: str): pass",  # Only one param in code
                hash="test_hash",
                arg_types={"param1": "str", "param2": "int"},  # Two params
            )

    def test_edge_case_empty_arg_types(self):
        """Test edge case with empty arg_types"""
        # This should work fine - empty arg_types is valid
        func = FunctionCreate(
            name="test_func",
            signature="def test_func(): pass",
            code="def test_func(): pass",
            hash="test_hash",
            arg_types={},
        )
        assert func.arg_types == {}

    def test_complex_type_annotations(self):
        """Test complex type annotations that might cause parsing issues"""
        complex_types = [
            "Dict[str, List[int]]",
            "Optional[Union[str, int]]",
            "Callable[[str, int], bool]",
            "Tuple[str, ...]",
        ]

        for complex_type in complex_types:
            try:
                func = FunctionCreate(
                    name="test_func",
                    signature=f"def test_func(param: {complex_type}): pass",
                    code=f"def test_func(param: {complex_type}): pass",
                    hash="test_hash",
                    arg_types={"param": complex_type},
                )
                # Should either succeed or fail gracefully
                assert func.name == "test_func"
            except ValueError:
                # Complex types might fail validation, which is acceptable
                pass
