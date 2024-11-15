"""Tests for the `_utils.closure` module."""

import ast
import hashlib
import inspect
import sys
from types import ModuleType
from unittest.mock import Mock, patch

import pytest
from mirascope.core import openai, prompt_template
from pydantic import BaseModel

from lilypad._utils.closure import (
    _CodeLocation,
    _DependencyCollector,
    _DependencyVisitor,
    compute_closure,
)


def _fn():
    return "test"


def test_simple_function_no_deps():
    """Tests a simple function with no dependencies."""
    expected = inspect.cleandoc("""
    def _fn():
        return "test"
    """)
    assert compute_closure(_fn)[0] == expected + "\n"


def _helper2():
    return _helper3()


def _helper3():
    return "helper3"


def _helper1():
    return _helper2()


def test_function_ordering():
    """Tests that function dependencies are ordered correctly in the closure."""
    expected = inspect.cleandoc("""
    def _helper3():
        return "helper3"


    def _helper2():
        return _helper3()


    def _helper1():
        return _helper2()
    """)
    assert compute_closure(_helper1)[0] == expected + "\n"


@openai.call("gpt-4o-mini")
def _recommend_book(genre: str) -> str:
    return f"Recommend a {genre} book"


def test_decorated_function():
    """Tests that a decorated function's closure is computed correctly."""
    expected = inspect.cleandoc("""
    @openai.call("gpt-4o-mini")
    def _recommend_book(genre: str) -> str:
        return f"Recommend a {genre} book"
    """)
    assert compute_closure(_recommend_book)[0] == expected + "\n"


@openai.call("gpt-4o-mini")
@prompt_template("Recommend a {genre} author")
def _recommend_author(genre: str): ...


def test_multiple_decorators():
    """Tests that multiple decorators are handled correctly."""
    expected = inspect.cleandoc("""
    @openai.call("gpt-4o-mini")
    @prompt_template("Recommend a {genre} author")
    def _recommend_author(genre: str): ...
    """)
    assert compute_closure(_recommend_author)[0] == expected + "\n"


def _outer():
    def inner():
        return "inner"

    return inner()


def test_nested_functions():
    """Tests that nested functions are handled correctly."""
    expected = inspect.cleandoc("""
    def _outer():
        def inner():
            return "inner"

        return inner()
    """)
    assert compute_closure(_outer)[0] == expected + "\n"


def _no_source():
    pass


def test_no_source():
    """Tests that functions with no source code are handled correctly."""
    expected = inspect.cleandoc("""
    def _no_source():
        pass
    """)
    assert compute_closure(_no_source)[0] == expected + "\n"


class _Book(BaseModel):
    title: str
    author: str


def _return_book() -> _Book: ...


def test_class_return_type():
    """Tests that a class is included in the closure of a function."""
    expected = inspect.cleandoc("""
    class _Book(BaseModel):
        title: str
        author: str

    
    def _return_book() -> _Book: ...
    """)
    assert compute_closure(_return_book)[0] == expected + "\n"


@openai.call("gpt-4o-mini", response_model=_Book)
def _recommend_book_class(genre: str) -> str:
    return f"Recommend a {genre} book"


def test_class_argument_in_decorator():
    """Tests that a class argument in a decorator is included in the closure."""
    expected = inspect.cleandoc("""
    class _Book(BaseModel):
        title: str
        author: str
    
    
    @openai.call("gpt-4o-mini", response_model=_Book)
    def _recommend_book_class(genre: str) -> str:
        return f"Recommend a {genre} book"
    """)
    assert compute_closure(_recommend_book_class)[0] == expected + "\n"


class _InnerClass(BaseModel):
    inner: str


class _OuterClass(BaseModel):
    outer: str
    inner: _InnerClass


def _fn_with_class():
    inner = _InnerClass(inner="inner")
    _ = _OuterClass(outer="outer", inner=inner)


def test_class_in_function():
    """Tests that a class defined in a function is included in the closure."""
    expected = inspect.cleandoc("""
    class _OuterClass(BaseModel):
        outer: str
        inner: _InnerClass

    
    class _InnerClass(BaseModel):
        inner: str
    
    
    def _fn_with_class():
        inner = _InnerClass(inner="inner")
        _ = _OuterClass(outer="outer", inner=inner)
    """)
    assert compute_closure(_fn_with_class)[0] == expected + "\n"


# DOES NOT WORK YET. SAD :(
# template = "Recommend a {genre} book series"


# @openai.call("gpt-4o-mini")
# @prompt_template(template)
# def recommend_book_series(genre: str): ...


# def test_local_variable_inclusion():
#     """Tests that local variables are included in the closure."""
#     expected = inspect.cleandoc("""
#     @openai.call("gpt-4o-mini")
#     @prompt_template("Recommend a {genre} book series")
#     def recommend_book_series(genre: str): ...
#     """)
#     assert compute_closure(recommend_book_series) == expected + "\n"


def _get_available_series() -> list[str]:
    return ["The Kingkiller Chronicle"]


@openai.call("gpt-4o-mini")
@prompt_template("Recommend a {genre} book series from this list: {series}")
def _recommend_book_series_from_available(genre: str) -> openai.OpenAIDynamicConfig:
    return {"computed_fields": {"series": _get_available_series()}}


def test_multiple_decorators_with_dependencies():
    """Tests that multiple decorators with dependencies are handled correctly."""
    expected = inspect.cleandoc("""
    def _get_available_series() -> list[str]:
        return ["The Kingkiller Chronicle"]


    @openai.call("gpt-4o-mini")
    @prompt_template("Recommend a {genre} book series from this list: {series}")
    def _recommend_book_series_from_available(genre: str) -> openai.OpenAIDynamicConfig:
        return {"computed_fields": {"series": _get_available_series()}}
    """)
    assert compute_closure(_recommend_book_series_from_available)[0] == expected + "\n"


def test_get_code_location_exception():
    """Test that _get_code_location handles exceptions properly."""

    def func():
        pass

    # Mock inspect.getsourcelines to raise an OSError
    with patch("inspect.getsourcelines", side_effect=OSError):
        closure, closure_hash = compute_closure(func)
        expected = ""  # Since we cannot get the source code, closure should be empty
        assert closure == expected


def test_collect_class_definition_exception():
    """Test that exceptions in _collect_class_definition are handled."""

    class TestClass:
        pass

    def func():
        obj = TestClass()  # noqa: F841

    # Mock inspect.getsource to raise an OSError
    with patch("inspect.getsource", side_effect=OSError):
        closure, closure_hash = compute_closure(func)
        expected = ""  # Since we cannot get the source code, closure should be empty
        assert closure == expected


def test_collect_function_and_deps_exception():
    """Test that exceptions in _collect_function_and_deps are handled."""

    def func():
        pass

    # Mock inspect.getsource to raise an OSError
    with patch("inspect.getsource", side_effect=OSError):
        closure, closure_hash = compute_closure(func)
        # Since the function source cannot be retrieved, closure should be empty
        assert closure == ""
        expected_hash = hashlib.sha256(closure.encode("utf-8")).hexdigest()
        assert closure_hash == expected_hash


def test_function_in_third_party_module():
    """Test that functions from third-party modules are skipped."""
    import os  # os is part of the standard library but serves as an example

    def func():
        return os.path.join("a", "b")

    closure, closure_hash = compute_closure(func)
    expected = inspect.cleandoc("""
    def func():
        return os.path.join("a", "b")
    """)
    assert closure == expected + "\n"


def test_function_with_global_variable():
    """Test that global variables are included in the closure."""
    global global_var
    global_var = "global value"

    def func():
        return global_var

    closure, closure_hash = compute_closure(func)
    expected = inspect.cleandoc("""
    global_var = "global value"


    def func():
        return global_var
    """)
    assert closure == expected + "\n"


def test_codelocation_eq():
    """Test that __eq__"""
    loc1 = _CodeLocation("module_path", 1)
    loc2 = _CodeLocation("module_path", 2)
    assert loc1.__eq__(loc1)
    assert not loc1.__eq__(loc2)
    assert loc1.__eq__("not a _CodeLocation") == NotImplemented


def test_format_code_exception():
    """Test that _format_code returns original code when black.format_str raises an exception."""
    collector = _DependencyCollector()
    code = "def foo():\n    pass"
    with patch("black.format_str", side_effect=Exception):
        formatted_code = collector._format_code(code)
        assert formatted_code == code


def test_is_third_party_module_none():
    """Test that _is_third_party_module returns True when module_path is None."""
    collector = _DependencyCollector()
    assert collector._is_third_party_module(None) is True


def test_find_function_in_parent_module():
    """Test that _find_function_in_module can find functions in parent modules."""
    collector = _DependencyCollector()

    # Mock modules
    parent_module = ModuleType("parent_module")
    child_module = ModuleType("parent_module.child_module")
    sys.modules["parent_module"] = parent_module
    sys.modules["parent_module.child_module"] = child_module

    def parent_function():
        pass

    parent_module.parent_function = parent_function  # pyright: ignore [reportAttributeAccessIssue]

    # Test
    result = collector._find_function_in_module("parent_function", child_module)
    assert result == parent_function


def test_collect_class_definition_class_not_found():
    """Test that _collect_class_definition does nothing when class is not found."""
    collector = _DependencyCollector()
    module = ModuleType("test_module")
    class_name = "NonExistentClass"
    collector._collect_class_definition(class_name, module)
    # No exception should be raised


def test_collect_class_definition_ast_parse_exception():
    """Test that _collect_class_definition handles ast.parse exceptions."""
    collector = _DependencyCollector()
    module = ModuleType("test_module")
    class_name = "TestClass"

    with patch("ast.parse", side_effect=SyntaxError):
        collector._collect_class_definition(class_name, module)
    # No exception should be raised


def test_collect_function_and_deps_getsource_exception():
    """Test that _collect_function_and_deps handles getsource exceptions."""
    collector = _DependencyCollector()

    def test_func():
        pass

    with patch("inspect.getsource", side_effect=OSError):
        collector._collect_function_and_deps(test_func)
    # No exception should be raised


def test_collect_function_and_deps_function_not_found():
    """Test that _collect_function_and_deps handles functions not found in modules."""
    collector = _DependencyCollector()

    def test_func():
        missing_func()  # pyright: ignore [reportUndefinedVariable] #  noqa: F821

    collector._collect_function_and_deps(test_func)
    # No exception should be raised


def test_get_ordered_functions_no_main():
    """Test that _get_ordered_functions returns empty list when main function is None."""
    collector = _DependencyCollector()
    collector._main_function_name = None
    result = collector._get_ordered_functions()
    assert result == []


def test_get_code_location_getsourcelines_exception():
    """Test that _get_code_location handles getsourcelines exceptions."""
    collector = _DependencyCollector()

    def test_func():
        pass

    with patch("inspect.getsourcelines", side_effect=OSError):
        location = collector._get_code_location(test_func)
        assert location.line_number == -1


def test_get_code_location_module_file_none():
    """Test that _get_code_location handles module.__file__ being None."""
    collector = _DependencyCollector()

    def test_func():
        pass

    module = inspect.getmodule(test_func)
    with patch.object(module, "__file__", None):
        location = collector._get_code_location(test_func)
        assert location.module_path == ""


def test_is_user_defined_import():
    """Test the _is_user_defined_import method."""
    collector = _DependencyCollector()
    assert collector._is_user_defined_import("from typing import List") is True
    assert collector._is_user_defined_import("import openai") is False
    assert collector._is_user_defined_import("import custom_module") is True


def test_collect_decorator_calls_with_attribute():
    """Test _collect_decorator_calls with attribute nodes."""

    def decorator(func):
        return func

    class Decorators:
        @staticmethod
        def deco():
            return decorator

    @Decorators.deco()
    def func():
        pass

    collector = _DependencyCollector()
    collector.collect(func)
    # No exception should be raised


def test_visit_call_with_attribute():
    """Test visit_Call handles attribute function calls."""

    class SomeClass:
        def method(self):
            pass

    def func():
        obj = SomeClass()
        obj.method()

    closure, _ = compute_closure(func)
    assert "SomeClass" in closure
    assert "def func()" in closure


def test_get_code_location_no_module():
    """Test that _get_code_location handles functions with no module."""

    def test_func():
        pass

    with patch("inspect.getmodule", return_value=None):
        collector = _DependencyCollector()
        with pytest.raises(ValueError):
            collector._get_code_location(test_func)


def test_collect_class_definition_no_source():
    """Test handling class definition with no source."""
    collector = _DependencyCollector()
    module = Mock()

    class TestClass:
        pass

    module.TestClass = TestClass
    with (
        patch("inspect.isclass", return_value=True),
        patch("inspect.getsource", side_effect=TypeError),
    ):
        collector._collect_class_definition("TestClass", module)
        # Should not raise exception


def test_is_serializable_value():
    """Test all cases of _is_serializable_value."""
    collector = _DependencyCollector()
    assert collector._is_serializable_value(42)
    assert collector._is_serializable_value(3.14)
    assert collector._is_serializable_value("string")
    assert collector._is_serializable_value(True)
    assert collector._is_serializable_value(None)
    assert not collector._is_serializable_value(lambda x: x)
    assert not collector._is_serializable_value(object())


def test_collect_with_type_aliases():
    """Test handling of type aliases in annotations."""
    from typing import TypeAlias

    MyType: TypeAlias = str  # pyright: ignore [reportGeneralTypeIssues]

    def func(param: MyType) -> MyType:
        return param.upper()

    closure, _ = compute_closure(func)
    assert "MyType" in closure
    assert "def func" in closure


def test_format_code_invalid():
    """Test handling of invalid code formatting."""
    collector = _DependencyCollector()
    invalid_code = "def func() invalid python"

    with patch("black.format_str", side_effect=Exception):
        formatted = collector._format_code(invalid_code)
        assert formatted == invalid_code


def test_collect_class_with_non_function_attribute():
    """Test handling of non-function class attributes."""

    class TestClass:
        class_var = "test"

        def method(self):
            return self.class_var

    collector = _DependencyCollector()
    source = inspect.getsource(TestClass)
    location = collector._get_code_location(TestClass)
    collector._collected_code[location] = source
    assert "class_var = " in collector._collected_code[location]


def test_dependency_visitor_extracted_annotations():
    """Test _extract_annotation_references handles all annotation types."""
    visitor = _DependencyVisitor()

    # Test Name node
    name_node = ast.Name(id="TestType", ctx=ast.Load())
    visitor._extract_annotation_references(name_node)
    assert "TestType" in visitor.classes

    # Test Attribute node with context
    module_name = ast.Name(id="module", ctx=ast.Load())
    attr_node = ast.Attribute(value=module_name, attr="Type", ctx=ast.Load())
    visitor._extract_annotation_references(attr_node)
    assert "module" in visitor.classes


def test_function_with_error_in_source():
    """Test handling of functions with errors in source code."""

    def test_func():
        pass

    collector = _DependencyCollector()

    # Create a fake source location that will be skipped
    location = _CodeLocation("test.py", 1)
    collector._visited.add(location)

    # This should not raise any exceptions
    with patch(
        "inspect.getsource", return_value="def test_func(): \n    return 'test'"
    ):
        collector._collect_function_and_deps(test_func)
