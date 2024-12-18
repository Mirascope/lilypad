"""Tests for the `Closure` class"""

import importlib.metadata
import inspect
import sys
from collections.abc import Callable

from lilypad._utils import Closure

from .closure_test_functions import (
    aliased_import_fn,
    aliased_module_import_fn,
    annotated_assignment_fn,
    annotated_input_arg_fn,
    built_in_fn,
    closure_inside_decorator_fn,
    closure_inside_imported_decorator_fn,
    closure_with_long_function_name_that_wraps_around_fn,
    decorated_fn,
    dotted_import_fn,
    fn_inside_class_fn,
    global_var_fn,
    import_with_different_dist_name_fn,
    inner_class_fn,
    inner_fn,
    inner_sub_fn,
    internal_imports_fn,
    mirascope_response_model_fn,
    multi_decorated_fn,
    self_fn_class_fn,
    single_fn,
    standard_import_fn,
    sub_fn,
    sub_fn_inside_class_fn,
    third_party_fn,
    type_alias_fn,
    user_defined_aliased_class_import_fn,
    user_defined_aliased_dotted_import_fn,
    user_defined_aliased_import_fn,
    user_defined_aliased_module_import_class_fn,
    user_defined_aliased_module_import_fn,
    user_defined_class_from_import_fn,
    user_defined_class_import_fn,
    user_defined_dotted_import_fn,
    user_defined_from_import_fn,
    user_defined_import_fn,
)


def _expected(fn: Callable) -> str:
    return inspect.cleandoc(fn.__doc__ or "") + "\n"


def test_single_fn() -> None:
    """Test the `Closure` class with a single function."""
    closure = Closure.from_fn(single_fn)
    assert closure.code == _expected(single_fn)
    assert closure.dependencies == {}


def test_sub_fn() -> None:
    """Test the `Closure` class with a sub function."""
    closure = Closure.from_fn(sub_fn)
    assert closure.code == _expected(sub_fn)
    assert closure.dependencies == {}


def test_inner_fn() -> None:
    """Test the `Closure` class with an inner function."""
    closure = Closure.from_fn(inner_fn)
    assert closure.code == _expected(inner_fn)
    assert closure.dependencies == {}


def test_inner_class_fn() -> None:
    """Test the `Closure` class with an inner class."""
    closure = Closure.from_fn(inner_class_fn)
    assert closure.code == _expected(inner_class_fn)
    assert closure.dependencies == {}


def test_inner_sub_fn() -> None:
    """Test the `Closure` class with an inner method."""
    closure = Closure.from_fn(inner_sub_fn)
    assert closure.code == _expected(inner_sub_fn)
    assert closure.dependencies == {}


def test_built_in_fn() -> None:
    """Test the `Closure` class with a built-in function."""
    closure = Closure.from_fn(built_in_fn)
    assert closure.code == _expected(built_in_fn)
    assert closure.dependencies == {}


def test_third_party_fn() -> None:
    """Test the `Closure` class with a third-party function."""
    closure = Closure.from_fn(third_party_fn)
    assert closure.code == _expected(third_party_fn)
    assert closure.dependencies == {
        "mirascope": {
            "version": importlib.metadata.version("mirascope"),
            "extras": ["anthropic", "gemini", "openai", "opentelemetry"],
        }
    }


def test_decorated_fn() -> None:
    """Test the `Closure` class with a decorated function."""
    closure = Closure.from_fn(decorated_fn)
    assert closure.code == _expected(decorated_fn)
    assert closure.dependencies == {
        "mirascope": {
            "version": importlib.metadata.version("mirascope"),
            "extras": ["anthropic", "gemini", "openai", "opentelemetry"],
        }
    }


def test_multi_decorated_fn() -> None:
    """Test the `Closure` class with a multi-decorated function."""
    closure = Closure.from_fn(multi_decorated_fn)
    assert closure.code == _expected(multi_decorated_fn)
    assert closure.dependencies == {
        "mirascope": {
            "version": importlib.metadata.version("mirascope"),
            "extras": ["anthropic", "gemini", "openai", "opentelemetry"],
        }
    }


def test_user_defined_import_fn() -> None:
    """Test the `Closure` class with a user-defined import."""
    closure = Closure.from_fn(user_defined_import_fn)
    assert closure.code == _expected(user_defined_import_fn)
    assert closure.dependencies == {}


def test_user_defined_from_import_fn() -> None:
    """Test the `Closure` class with a user-defined from import."""
    closure = Closure.from_fn(user_defined_from_import_fn)
    assert closure.code == _expected(user_defined_from_import_fn)
    assert closure.dependencies == {}


def test_user_defined_class_import_fn() -> None:
    """Test the `Closure` class with a user-defined class import."""
    closure = Closure.from_fn(user_defined_class_import_fn)
    assert closure.code == _expected(user_defined_class_import_fn)
    assert closure.dependencies == {}


def test_user_defined_class_from_import_fn() -> None:
    """Test the `Closure` class with a user-defined class from import."""
    closure = Closure.from_fn(user_defined_class_from_import_fn)
    assert closure.code == _expected(user_defined_class_from_import_fn)
    assert closure.dependencies == {}


def test_fn_inside_class_fn() -> None:
    """Test the `Closure` class with a function inside a class."""
    closure = Closure.from_fn(fn_inside_class_fn)
    assert closure.code == _expected(fn_inside_class_fn)
    assert closure.dependencies == {}


def test_sub_fn_inside_class_fn() -> None:
    """Test the `Closure` class with a sub function inside a class."""
    closure = Closure.from_fn(sub_fn_inside_class_fn)
    assert closure.code == _expected(sub_fn_inside_class_fn)
    assert closure.dependencies == {}


def test_self_fn_class_fn() -> None:
    """Test the `Closure` class with a method inside a class."""
    closure = Closure.from_fn(self_fn_class_fn)
    assert closure.code == _expected(self_fn_class_fn)
    assert closure.dependencies == {}


def test_standard_import_fn() -> None:
    """Test the `Closure` class with a standard import."""
    closure = Closure.from_fn(standard_import_fn)
    assert closure.code == _expected(standard_import_fn)
    assert closure.dependencies == {}


def test_dot_import_fn() -> None:
    """Test the `Closure` class with a dotted import."""
    closure = Closure.from_fn(dotted_import_fn)
    assert closure.code == _expected(dotted_import_fn)
    assert closure.dependencies == {}


def test_aliased_module_import_fn() -> None:
    """Test the `Closure` class with an aliased module import."""
    closure = Closure.from_fn(aliased_module_import_fn)
    assert closure.code == _expected(aliased_module_import_fn)
    assert closure.dependencies == {
        "openai": {"version": importlib.metadata.version("openai"), "extras": None}
    }


def test_aliased_import_fn() -> None:
    """Test the `Closure` class with an aliased import."""
    closure = Closure.from_fn(aliased_import_fn)
    assert closure.code == _expected(aliased_import_fn)
    assert closure.dependencies == {
        "openai": {"version": importlib.metadata.version("openai"), "extras": None}
    }


def test_user_defined_aliased_module_import_fn() -> None:
    """Test the `Closure` class with a user-defined aliased module import."""
    closure = Closure.from_fn(user_defined_aliased_module_import_fn)
    assert closure.code == _expected(user_defined_aliased_module_import_fn)
    assert closure.dependencies == {}


def test_user_defined_aliased_module_import_class_fn() -> None:
    """Test the `Closure` class with a user-defined aliased module import."""
    closure = Closure.from_fn(user_defined_aliased_module_import_class_fn)
    assert closure.code == _expected(user_defined_aliased_module_import_class_fn)
    assert closure.dependencies == {}


def test_user_defined_aliased_import_fn() -> None:
    """Test the `Closure` class with a user-defined aliased import."""
    closure = Closure.from_fn(user_defined_aliased_import_fn)
    assert closure.code == _expected(user_defined_aliased_import_fn)
    assert closure.dependencies == {}


def test_user_defined_aliased_class_import_fn() -> None:
    """Test the `Closure` class with a user-defined aliased class import."""
    closure = Closure.from_fn(user_defined_aliased_class_import_fn)
    assert closure.code == _expected(user_defined_aliased_class_import_fn)
    assert closure.dependencies == {}


def test_user_defined_dotted_import_fn() -> None:
    """Test the `Closure` class with a user-defined dotted import."""
    closure = Closure.from_fn(user_defined_dotted_import_fn)
    assert closure.code == _expected(user_defined_dotted_import_fn)
    assert closure.dependencies == {}


def test_user_defined_aliased_dotted_import_fn() -> None:
    """Test the `Closure` class with a user-defined aliased dotted import."""
    closure = Closure.from_fn(user_defined_aliased_dotted_import_fn)
    assert closure.code == _expected(user_defined_aliased_dotted_import_fn)
    assert closure.dependencies == {}


def test_annotated_input_arg_fn() -> None:
    """Test the `Closure` class with an annotated input argument."""
    closure = Closure.from_fn(annotated_input_arg_fn)
    assert closure.code == _expected(annotated_input_arg_fn)
    assert closure.dependencies == {}


def test_annotated_assignment_fn() -> None:
    """Test the `Closure` class with an annotated assignment."""
    closure = Closure.from_fn(annotated_assignment_fn)
    assert closure.code == _expected(annotated_assignment_fn)
    assert closure.dependencies == {
        "openai": {"version": importlib.metadata.version("openai"), "extras": None}
    }


def test_internal_imports_fn() -> None:
    """Test the `Closure` class with internal imports."""
    closure = Closure.from_fn(internal_imports_fn)
    assert closure.code == _expected(internal_imports_fn)
    assert closure.dependencies == {
        "openai": {"version": importlib.metadata.version("openai"), "extras": None}
    }


def test_type_alias_fn() -> None:
    """Test the `Closure` class with a type alias."""
    closure = Closure.from_fn(type_alias_fn)
    assert closure.code == _expected(type_alias_fn)
    assert closure.dependencies == {}


def test_global_var_fn() -> None:
    """Test the `Closure` class with a global variable."""
    closure = Closure.from_fn(global_var_fn)
    assert closure.code == _expected(global_var_fn)
    assert closure.dependencies == {
        "mirascope": {
            "version": importlib.metadata.version("mirascope"),
            "extras": ["anthropic", "gemini", "openai", "opentelemetry"],
        },
        "openai": {"version": importlib.metadata.version("openai"), "extras": None},
    }


def test_import_with_different_dist_name_fn() -> None:
    """Test the `Closure` class with an import with a different distribution name."""
    closure = Closure.from_fn(import_with_different_dist_name_fn)
    assert closure.code == _expected(import_with_different_dist_name_fn)
    expected_dependencies = {
        "google-generativeai": {
            "version": importlib.metadata.version("google-generativeai"),
            "extras": None,
        },
        "googleapis-common-protos": {
            "version": importlib.metadata.version("googleapis-common-protos"),
            "extras": None,
        },
        "google-auth": {
            "version": importlib.metadata.version("google-auth"),
            "extras": None,
        },
        "google-ai-generativelanguage": {
            "version": importlib.metadata.version("google-ai-generativelanguage"),
            "extras": None,
        },
        "google-api-core": {
            "version": importlib.metadata.version("google-api-core"),
            "extras": None,
        },
    }
    if sys.version_info >= (3, 11):
        expected_dependencies["protobuf"] = {
            "version": importlib.metadata.version("protobuf"),
            "extras": None,
        }
    assert closure.dependencies == expected_dependencies


def test_closure_inside_decorator_fn() -> None:
    """Test the `Closure` class inside a decorator."""
    closure = closure_inside_decorator_fn()
    assert closure.code == _expected(closure_inside_decorator_fn)
    assert closure.dependencies == {
        "python-lilypad": {
            "version": importlib.metadata.version("python-lilypad"),
            "extras": [
                "anthropic",
                "gemini",
                "openai",
                "outlines",
            ],
        }
    }


def test_closure_inside_imported_decorator_fn() -> None:
    """Test the `Closure` class inside an imported decorator."""
    closure = closure_inside_imported_decorator_fn()
    assert closure.code == _expected(closure_inside_imported_decorator_fn)
    assert closure.dependencies == {
        "python-lilypad": {
            "version": importlib.metadata.version("python-lilypad"),
            "extras": [
                "anthropic",
                "gemini",
                "openai",
                "outlines",
            ],
        }
    }


def test_closure_with_long_function_name_that_wraps_around_fn() -> None:
    """Test the `Closure` class with a long function name that wraps around."""
    closure = Closure.from_fn(closure_with_long_function_name_that_wraps_around_fn)
    assert closure.code == _expected(
        closure_with_long_function_name_that_wraps_around_fn
    )
    assert closure.dependencies == {
        "openai": {"version": importlib.metadata.version("openai"), "extras": None}
    }
    assert closure.signature == inspect.cleandoc("""
        def closure_with_long_function_name_that_wraps_around_fn(
            arg1: str, arg2: str
        ) -> ChatCompletionUserMessageParam: ...
        """)


def test_closure_run() -> None:
    """Tests the `Closure.run` method."""

    def fn(arg: str) -> str:
        return arg

    closure = Closure.from_fn(fn)
    assert closure.run("Hello, world!") == "Hello, world!"


def test_mirascope_response_model_fn() -> None:
    """Test the `Closure` class with a Mirascope response model."""
    closure = Closure.from_fn(mirascope_response_model_fn)
    assert closure.code == _expected(mirascope_response_model_fn)
    assert closure.dependencies == {
        "mirascope": {
            "version": importlib.metadata.version("mirascope"),
            "extras": ["anthropic", "gemini", "openai", "opentelemetry"],
        },
        "pydantic": {
            "extras": None,
            "version": "2.10.3",
        },
    }
