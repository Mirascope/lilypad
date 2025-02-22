"""Tests for the `Closure` class"""

import importlib.metadata
import inspect
import sys
from collections.abc import Callable

import pytest

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
    closure_with_properties_fn,
    datetime_fn,
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
from .closure_test_functions.main import (
    Chatbot,
    empty_body_fn_docstrings,
    handle_issue,
    multi_joined_string_fn,
    multiple_literal_fn,
    nested_base_model_definitions,
    raw_string_fn,
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
            "extras": [
                "anthropic",
                "bedrock",
                "gemini",
                "mistral",
                "openai",
                "opentelemetry",
                "vertex",
            ],
        }
    }


def test_decorated_fn() -> None:
    """Test the `Closure` class with a decorated function."""
    closure = Closure.from_fn(decorated_fn)
    assert closure.code == _expected(decorated_fn)
    assert closure.dependencies == {
        "mirascope": {
            "version": importlib.metadata.version("mirascope"),
            "extras": [
                "anthropic",
                "bedrock",
                "gemini",
                "mistral",
                "openai",
                "opentelemetry",
                "vertex",
            ],
        }
    }


def test_multi_decorated_fn() -> None:
    """Test the `Closure` class with a multi-decorated function."""
    closure = Closure.from_fn(multi_decorated_fn)
    assert closure.code == _expected(multi_decorated_fn)
    assert closure.dependencies == {
        "mirascope": {
            "version": importlib.metadata.version("mirascope"),
            "extras": [
                "anthropic",
                "bedrock",
                "gemini",
                "mistral",
                "openai",
                "opentelemetry",
                "vertex",
            ],
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
        "openai": {
            "version": importlib.metadata.version("openai"),
            "extras": ["realtime"],
        }
    }


def test_aliased_import_fn() -> None:
    """Test the `Closure` class with an aliased import."""
    closure = Closure.from_fn(aliased_import_fn)
    assert closure.code == _expected(aliased_import_fn)
    assert closure.dependencies == {
        "openai": {
            "version": importlib.metadata.version("openai"),
            "extras": ["realtime"],
        }
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
        "openai": {
            "version": importlib.metadata.version("openai"),
            "extras": ["realtime"],
        }
    }


def test_internal_imports_fn() -> None:
    """Test the `Closure` class with internal imports."""
    closure = Closure.from_fn(internal_imports_fn)
    assert closure.code == _expected(internal_imports_fn)
    assert closure.dependencies == {
        "openai": {
            "version": importlib.metadata.version("openai"),
            "extras": ["realtime"],
        }
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
            "extras": [
                "anthropic",
                "bedrock",
                "gemini",
                "mistral",
                "openai",
                "opentelemetry",
                "vertex",
            ],
        },
        "openai": {
            "version": importlib.metadata.version("openai"),
            "extras": ["realtime"],
        },
    }


def test_import_with_different_dist_name_fn() -> None:
    """Test the `Closure` class with an import with a different distribution name."""
    closure = Closure.from_fn(import_with_different_dist_name_fn)
    assert closure.code == _expected(import_with_different_dist_name_fn)
    expected_dependencies = {
        "google-ai-generativelanguage": {"extras": None, "version": "0.6.15"},
        "google-api-core": {"extras": None, "version": "2.24.1"},
        "google-auth": {"extras": None, "version": "2.38.0"},
        "google-cloud-aiplatform": {"extras": None, "version": "1.79.0"},
        "google-cloud-bigquery": {"extras": None, "version": "3.29.0"},
        "google-cloud-core": {"extras": ["grpc"], "version": "2.4.1"},
        "google-cloud-resource-manager": {"extras": None, "version": "1.14.0"},
        "google-cloud-storage": {"extras": None, "version": "2.19.0"},
        "google-generativeai": {"extras": None, "version": "0.8.4"},
        "google-resumable-media": {
            "extras": ["aiohttp", "requests"],
            "version": "2.7.2",
        },
        "googleapis-common-protos": {"extras": None, "version": "1.66.0"},
        "grpc-google-iam-v1": {"extras": None, "version": "0.14.0"},
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
                "bedrock",
                "gemini",
                "mistral",
                "openai",
                "outlines",
                "vertex",
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
                "bedrock",
                "gemini",
                "mistral",
                "openai",
                "outlines",
                "vertex",
            ],
        }
    }


def test_closure_with_properties_fn() -> None:
    """Test the fn with properties."""
    closure = Closure.from_fn(closure_with_properties_fn)
    assert closure.code == _expected(closure_with_properties_fn)
    assert closure.dependencies == {}


def test_closure_with_long_function_name_that_wraps_around_fn() -> None:
    """Test the `Closure` class with a long function name that wraps around."""
    closure = Closure.from_fn(closure_with_long_function_name_that_wraps_around_fn)
    assert closure.code == _expected(
        closure_with_long_function_name_that_wraps_around_fn
    )
    assert closure.dependencies == {
        "openai": {
            "version": importlib.metadata.version("openai"),
            "extras": ["realtime"],
        }
    }
    assert closure.signature == inspect.cleandoc("""
        def closure_with_long_function_name_that_wraps_around_fn(
            arg1: str,
            arg2: str,
        ) -> ChatCompletionUserMessageParam: ...
        """)


def test_datetime() -> None:
    """Test the `Closure` class with a datetime function."""
    closure = Closure.from_fn(datetime_fn)
    assert closure.code == _expected(datetime_fn)
    assert closure.dependencies == {}


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
            "extras": [
                "anthropic",
                "bedrock",
                "gemini",
                "mistral",
                "openai",
                "opentelemetry",
                "vertex",
            ],
        },
        "pydantic": {
            "extras": None,
            "version": "2.10.6",
        },
    }


def test_multiple_literal_fn():
    """Test the `Closure` class with multiple literal functions."""
    closure = Closure.from_fn(multiple_literal_fn)
    assert closure.code == _expected(multiple_literal_fn)
    assert closure.dependencies == {}


def test_raw_string_fn():
    """Test the `Closure` class with a raw string."""
    closure = Closure.from_fn(raw_string_fn)
    assert closure.code == _expected(raw_string_fn)
    assert closure.dependencies == {}


@pytest.mark.skip("Skip this test for now. the pattern is broken")
def test_multi_joined_string_fn():
    """Test the `Closure` class with multiple joined strings."""
    closure = Closure.from_fn(multi_joined_string_fn)
    assert closure.code == _expected(multi_joined_string_fn)
    assert closure.dependencies == {}


def test_empty_body_fn():
    """Test the `Closure` class with an empty function body."""

    # Define an empty function body here.
    # Because it difficult to define an empty function body in main.py with the expected result.
    def empty_body_fn(): ...

    closure = Closure.from_fn(empty_body_fn)
    assert closure.code == "def empty_body_fn(): ...\n"
    assert closure.dependencies == {}


def test_empty_body_fn_docstrings():
    """Test the `Closure` class with an empty function body and docstrings."""
    closure = Closure.from_fn(empty_body_fn_docstrings)
    assert closure.code == _expected(empty_body_fn_docstrings)
    assert closure.dependencies == {}


def test_nested_base_model_definitions() -> None:
    """Test the `Closure` class with nested base model definitions."""
    closure = Closure.from_fn(nested_base_model_definitions)
    assert closure.code == _expected(nested_base_model_definitions)
    assert closure.dependencies == {
        "mirascope": {
            "version": importlib.metadata.version("mirascope"),
            "extras": [
                "anthropic",
                "bedrock",
                "gemini",
                "mistral",
                "openai",
                "opentelemetry",
                "vertex",
            ],
        },
        "pydantic": {
            "extras": None,
            "version": "2.10.6",
        },
    }


def test_nested_handle_issue_method() -> None:
    """Test the `Closure` class with nested handle issue method."""
    closure = Closure.from_fn(handle_issue)
    assert closure.code == _expected(handle_issue)
    assert closure.dependencies == {
        "mirascope": {
            "version": importlib.metadata.version("mirascope"),
            "extras": [
                "anthropic",
                "bedrock",
                "gemini",
                "mistral",
                "openai",
                "opentelemetry",
                "vertex",
            ],
        },
        "pydantic": {
            "extras": None,
            "version": "2.10.6",
        },
    }


def test_instance_method() -> None:
    """Test the `Closure` class with instance method."""
    closure = Closure.from_fn(Chatbot.instance_method)
    assert closure.code == _expected(Chatbot.instance_method)
    assert closure.dependencies == {
        "mirascope": {
            "version": importlib.metadata.version("mirascope"),
            "extras": [
                "anthropic",
                "bedrock",
                "gemini",
                "mistral",
                "openai",
                "opentelemetry",
                "vertex",
            ],
        },
    }


def test_closure_run_with_instance_method() -> None:
    """Tests the `Closure.run` method."""

    class Chatbot:
        def __init__(self, name: str) -> None:
            self.name = name

        def greet(self, comment) -> str:
            return f"Hello, {comment}! I'm {self.name}."

    closure = Closure.from_fn(Chatbot)
    assert closure.run(name="world").greet("nice")
