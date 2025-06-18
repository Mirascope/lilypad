"""Test cases for functions utilities."""

from typing import Optional, Union, List, Dict, Any


from lilypad._utils.functions import (
    get_signature,
    _get_type_str,
    inspect_arguments,
    ArgTypes,
    ArgValues,
)


def test_get_signature():
    """Test get_signature function."""

    def sample_func(a: int, b: str = "default") -> str:
        return f"{a} - {b}"

    sig = get_signature(sample_func)
    assert len(sig.parameters) == 2
    assert "a" in sig.parameters
    assert "b" in sig.parameters
    assert sig.parameters["b"].default == "default"

    # Test that it's cached
    sig2 = get_signature(sample_func)
    assert sig is sig2  # Same object due to caching


def test_get_type_str_primitives():
    """Test _get_type_str with primitive types."""
    assert _get_type_str(str) == "str"
    assert _get_type_str(int) == "int"
    assert _get_type_str(float) == "float"
    assert _get_type_str(bool) == "bool"
    assert _get_type_str(type(None)) == "None"


def test_get_type_str_optional():
    """Test _get_type_str with Optional types."""
    # Traditional Optional syntax
    assert _get_type_str(Optional[str]) == "Optional[str]"
    assert _get_type_str(Optional[int]) == "Optional[int]"
    assert _get_type_str(Optional[List[str]]) == "Optional[list[str]]"

    # New | operator syntax (Python 3.10+)
    assert _get_type_str(str | None) == "Optional[str]"
    assert _get_type_str(int | None) == "Optional[int]"


def test_get_type_str_union():
    """Test _get_type_str with Union types."""
    # Traditional Union syntax
    assert _get_type_str(Union[str, int]) == "Union[str, int]"
    assert _get_type_str(Union[str, int, float]) == "Union[str, int, float]"

    # New | operator syntax (Python 3.10+)
    assert _get_type_str(str | int) == "Union[str, int]"
    assert _get_type_str(str | int | float) == "Union[str, int, float]"


def test_get_type_str_generic():
    """Test _get_type_str with generic types."""
    assert _get_type_str(List[str]) == "list[str]"
    assert _get_type_str(Dict[str, int]) == "dict[str, int]"
    assert _get_type_str(List[Union[str, int]]) == "list[Union[str, int]]"
    assert _get_type_str(Dict[str, Optional[int]]) == "dict[str, Optional[int]]"

    # Unparameterized generics
    assert _get_type_str(list) == "list"
    assert _get_type_str(dict) == "dict"


def test_get_type_str_custom_types():
    """Test _get_type_str with custom types."""

    class CustomClass:
        pass

    assert _get_type_str(CustomClass) == "CustomClass"


def test_inspect_arguments_simple():
    """Test inspect_arguments with simple function."""

    def simple_func(a: int, b: str) -> str:
        return f"{a} - {b}"

    arg_types, arg_values = inspect_arguments(simple_func, 42, "hello")

    assert arg_types == {"a": "int", "b": "str"}
    assert arg_values == {"a": 42, "b": "hello"}


def test_inspect_arguments_with_defaults():
    """Test inspect_arguments with default values."""

    def func_with_defaults(a: int, b: str = "default", c: float = 3.14) -> None:
        pass

    # Only provide required argument
    arg_types, arg_values = inspect_arguments(func_with_defaults, 10)
    assert arg_types == {"a": "int", "b": "str", "c": "float"}
    assert arg_values == {"a": 10, "b": "default", "c": 3.14}

    # Override defaults
    arg_types, arg_values = inspect_arguments(func_with_defaults, 20, "custom", 2.71)
    assert arg_values == {"a": 20, "b": "custom", "c": 2.71}


def test_inspect_arguments_kwargs():
    """Test inspect_arguments with keyword arguments."""

    def func_with_kwargs(a: int, b: str = "default") -> None:
        pass

    arg_types, arg_values = inspect_arguments(func_with_kwargs, b="keyword", a=100)
    assert arg_types == {"a": "int", "b": "str"}
    assert arg_values == {"a": 100, "b": "keyword"}


def test_inspect_arguments_no_annotations():
    """Test inspect_arguments with function lacking type annotations."""

    def untyped_func(a, b, c=None):
        pass

    arg_types, arg_values = inspect_arguments(untyped_func, 42, "hello", [1, 2, 3])

    # Types should be inferred from values
    assert arg_types == {"a": "int", "b": "str", "c": "list"}
    assert arg_values == {"a": 42, "b": "hello", "c": [1, 2, 3]}


def test_inspect_arguments_complex_types():
    """Test inspect_arguments with complex type annotations."""

    def complex_func(
        required: str,
        optional: Optional[int] = None,
        union_type: Union[str, int] = "default",
        list_type: List[str] = None,
        dict_type: Dict[str, Any] = None,
    ) -> None:
        pass

    arg_types, arg_values = inspect_arguments(complex_func, "test", 42, 100, ["a", "b"], {"key": "value"})

    assert arg_types == {
        "required": "str",
        "optional": "Optional[int]",
        "union_type": "Union[str, int]",
        "list_type": "list[str]",
        "dict_type": "dict[str, Any]",
    }
    assert arg_values == {
        "required": "test",
        "optional": 42,
        "union_type": 100,
        "list_type": ["a", "b"],
        "dict_type": {"key": "value"},
    }


def test_inspect_arguments_varargs_kwargs():
    """Test inspect_arguments with *args and **kwargs."""

    def varargs_func(a: int, *args: str, **kwargs: Any) -> None:
        pass

    arg_types, arg_values = inspect_arguments(varargs_func, 10, "extra1", "extra2", key1="value1", key2="value2")

    # Note: *args and **kwargs are typically not included in bound arguments
    # Only the explicitly named parameter 'a' should be present
    assert "a" in arg_types
    assert arg_types["a"] == "int"
    assert arg_values["a"] == 10


def test_inspect_arguments_class_methods():
    """Test inspect_arguments with class methods."""

    class TestClass:
        def method(self, a: int, b: str = "default") -> None:
            pass

        @classmethod
        def class_method(cls, a: int) -> None:
            pass

        @staticmethod
        def static_method(a: int, b: float) -> None:
            pass

    obj = TestClass()

    # Instance method - when called on bound method, self is not in args
    arg_types, arg_values = inspect_arguments(obj.method, 42, "test")
    assert arg_values["a"] == 42
    assert arg_values["b"] == "test"

    # Static method
    arg_types, arg_values = inspect_arguments(TestClass.static_method, 10, 3.14)
    assert arg_types == {"a": "int", "b": "float"}
    assert arg_values == {"a": 10, "b": 3.14}


def test_type_aliases():
    """Test that ArgTypes and ArgValues are properly defined."""
    # These should be type aliases
    arg_types: ArgTypes = {"a": "int", "b": "str"}
    arg_values: ArgValues = {"a": 42, "b": "hello"}

    assert isinstance(arg_types, dict)
    assert isinstance(arg_values, dict)


def test_get_type_str_no_name_attribute():
    """Test _get_type_str with type that lacks __name__ attribute (line 50)."""

    # Create a mock type object without __name__ attribute
    class TypeWithoutName:
        def __str__(self):
            return "CustomTypeWithoutName"

    mock_type = TypeWithoutName()
    result = _get_type_str(mock_type)
    assert result == "CustomTypeWithoutName"


def test_get_type_str_generic_no_args():
    """Test _get_type_str with generic type that has no args (line 66)."""
    from unittest.mock import patch

    # Mock a scenario where get_origin returns something but get_args returns empty
    with (
        patch("lilypad._utils.functions.get_origin") as mock_origin,
        patch("lilypad._utils.functions.get_args") as mock_args,
    ):
        # Create a mock origin that has __name__
        class MockOrigin:
            __name__ = "MockGeneric"

        mock_origin.return_value = MockOrigin
        mock_args.return_value = ()  # Empty args tuple

        result = _get_type_str("dummy_type")
        assert result == "MockOrigin"
