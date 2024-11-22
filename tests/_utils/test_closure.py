"""Tests for the `_utils.closure` module."""

import ast
import hashlib
import inspect
import sys
import textwrap
from types import ModuleType
from unittest.mock import Mock, patch

import pytest
from mirascope.core import openai, prompt_template

from lilypad._utils.closure import (
    _CodeLocation,
    _DependencyCollector,
    _DependencyVisitor,
    compute_closure,
)


def test_simple_function_no_deps():
    """Tests a simple function with no dependencies."""

    def fn():
        return "test"

    expected = inspect.cleandoc("""
    def fn():
        return "test"
    """)
    assert compute_closure(fn)[0] == expected + "\n"


def test_function_ordering():
    """Tests that function dependencies are ordered correctly in the closure."""
    expected = inspect.cleandoc("""
    def helper3():
        return "helper3"


    def helper2():
        return helper3()


    def helper1():
        return helper2()
    """)

    def helper2():
        return helper3()

    def helper3():
        return "helper3"

    def helper1():
        return helper2()

    # Mock module with all required attributes
    module = Mock(spec=["__name__", "__file__"])
    module.__name__ = "test_module"
    module.__file__ = "test_module.py"  # Add file attribute
    module.helper1 = helper1
    module.helper2 = helper2
    module.helper3 = helper3

    with patch("inspect.getmodule", return_value=module):
        assert compute_closure(helper1)[0] == expected + "\n"


def test_decorated_function():
    """Tests that a decorated function's closure is computed correctly."""

    @openai.call("gpt-4o-mini")
    def recommend_book(genre: str) -> str:
        return f"Recommend a {genre} book"

    expected = inspect.cleandoc("""
    @openai.call("gpt-4o-mini")
    def recommend_book(genre: str) -> str:
        return f"Recommend a {genre} book"
    """)
    assert compute_closure(recommend_book)[0] == expected + "\n"


def test_multiple_decorators():
    """Tests that multiple decorators are handled correctly."""

    @openai.call("gpt-4o-mini")
    @prompt_template("Recommend a {genre} author")
    def recommend_author(genre: str): ...

    expected = inspect.cleandoc("""
    @openai.call("gpt-4o-mini")
    @prompt_template("Recommend a {genre} author")
    def recommend_author(genre: str): ...
    """)
    assert compute_closure(recommend_author)[0] == expected + "\n"


def test_nested_functions():
    """Tests that nested functions are handled correctly."""

    def outer():
        def inner():
            return "inner"

        return inner()

    expected = inspect.cleandoc("""
    def outer():
    
        def inner():
            return "inner"

        return inner()
    """)
    closure, _ = compute_closure(outer)
    assert closure == expected + "\n"


def test_no_source():
    """Tests that functions with no source code are handled correctly."""

    def no_source():
        pass

    expected = inspect.cleandoc("""
    def no_source():
        pass
    """)
    assert compute_closure(no_source)[0] == expected + "\n"


def test_class_return_type(tmp_path):
    """Tests that a class is included in the closure of a function."""
    # Create a temporary module file
    module_path = tmp_path / "test_module.py"
    module_path.write_text(
        textwrap.dedent("""
        from pydantic import BaseModel

        class Book(BaseModel):
            title: str
            author: str

        def return_book() -> Book:
            ...
    """)
    )

    # Import the temporary module
    import sys

    sys.path.insert(0, str(tmp_path))
    try:
        import test_module

        expected = inspect.cleandoc("""
        class Book(BaseModel):
            title: str
            author: str


        def return_book() -> Book: ...
        """)

        assert compute_closure(test_module.return_book)[0] == expected + "\n"
    finally:
        # Clean up
        sys.path.pop(0)
        if "test_module" in sys.modules:
            del sys.modules["test_module"]


def test_class_argument_in_decorator(tmp_path):
    """Tests that a class argument in a decorator is included in the closure."""
    # Create a temporary module file
    module_path = tmp_path / "test_module.py"
    module_path.write_text(
        textwrap.dedent("""
        from pydantic import BaseModel
        from mirascope.core import openai

        class Book(BaseModel):
            title: str
            author: str

        @openai.call("gpt-4o-mini", response_model=Book)
        def recommend_book_class(genre: str) -> str:
            return f"Recommend a {genre} book"
    """)
    )

    # Import the temporary module
    import sys

    sys.path.insert(0, str(tmp_path))
    try:
        import test_module

        expected = inspect.cleandoc("""
        class Book(BaseModel):
            title: str
            author: str


        @openai.call("gpt-4o-mini", response_model=Book)
        def recommend_book_class(genre: str) -> str:
            return f"Recommend a {genre} book"
        """)

        assert compute_closure(test_module.recommend_book_class)[0] == expected + "\n"
    finally:
        sys.path.pop(0)
        if "test_module" in sys.modules:
            del sys.modules["test_module"]


def test_class_in_function(tmp_path):
    """Tests that a class defined in a function is included in the closure."""
    module_path = tmp_path / "test_module.py"
    module_path.write_text(
        textwrap.dedent("""
        from pydantic import BaseModel

        class InnerClass(BaseModel):
            inner: str

        class OuterClass(BaseModel):
            outer: str
            inner: InnerClass

        def fn_with_class():
            inner = InnerClass(inner="inner")
            _ = OuterClass(outer="outer", inner=inner)
    """)
    )

    import sys

    sys.path.insert(0, str(tmp_path))
    try:
        import test_module

        expected = inspect.cleandoc("""
        class InnerClass(BaseModel):
            inner: str


        class OuterClass(BaseModel):
            outer: str
            inner: InnerClass


        def fn_with_class():
            inner = InnerClass(inner="inner")
            _ = OuterClass(outer="outer", inner=inner)
        """)

        assert compute_closure(test_module.fn_with_class)[0] == expected + "\n"

    finally:
        sys.path.pop(0)
        if "test_module" in sys.modules:
            del sys.modules["test_module"]


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


def test_multiple_decorators_with_dependencies(tmp_path):
    """Tests that multiple decorators with dependencies are handled correctly."""
    module_path = tmp_path / "test_module.py"
    module_path.write_text(
        textwrap.dedent("""
        from mirascope.core import openai, prompt_template

        def get_available_series() -> list[str]:
            return ["The Kingkiller Chronicle"]

        @openai.call("gpt-4o-mini")
        @prompt_template("Recommend a {genre} book series from this list: {series}")
        def recommend_book_series_from_available(genre: str) -> openai.OpenAIDynamicConfig:
            return {"computed_fields": {"series": get_available_series()}}
    """)
    )

    import sys

    sys.path.insert(0, str(tmp_path))
    try:
        import test_module

        expected = inspect.cleandoc("""
        def get_available_series() -> list[str]:
            return ["The Kingkiller Chronicle"]


        @openai.call("gpt-4o-mini")
        @prompt_template("Recommend a {genre} book series from this list: {series}")
        def recommend_book_series_from_available(genre: str) -> openai.OpenAIDynamicConfig:
            return {"computed_fields": {"series": get_available_series()}}
        """)

        assert (
            compute_closure(test_module.recommend_book_series_from_available)[0]
            == expected + "\n"
        )
    finally:
        sys.path.pop(0)
        if "test_module" in sys.modules:
            del sys.modules["test_module"]


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
    loc3 = _CodeLocation("module_path", 1)
    assert loc1.__eq__(loc1)
    assert not loc1.__eq__(loc2)
    assert loc1.__eq__("not a _CodeLocation") == NotImplemented
    assert loc1 == loc3


def test_format_code_exception():
    """Test that _format_code returns original code when black.format_str raises an exception."""
    collector = _DependencyCollector()

    def foo():
        pass

    collector.collect(foo)
    with patch("black.format_str", side_effect=Exception):
        formatted_code = collector._format_output()
        assert formatted_code == "def foo():\n    pass"


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
    """Test that _get_code_location raises functions with no module."""

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

    MyType: TypeAlias = str

    def func(param: MyType) -> MyType:
        return param.upper()

    closure, _ = compute_closure(func)
    print(closure)  # For debugging

    expected_func_def = "def func(param: str) -> str:"

    # Type alias definition should NOT be included in the closure
    assert "MyType: TypeAlias = str" not in closure

    # Function definition should have type alias replaced with the original type
    assert expected_func_def in closure



def test_compute_closure_with_type_alias_change():
    """Test that changing a type alias affects the closure and hash."""
    from typing import TypeAlias

    def outer():
        MyType: TypeAlias = str

        def func(param: MyType) -> MyType:
            return param.upper()

        return func

    func1 = outer()
    closure1, hash1 = compute_closure(func1)

    def outer():
        MyType: TypeAlias = int

        def func(param: MyType) -> MyType:
            return param + 1

        return func

    func2 = outer()
    closure2, hash2 = compute_closure(func2)

    assert closure1 != closure2
    assert hash1 != hash2


def test_compute_closure_with_same_type_alias():
    """Test that keeping the same type alias results in the same closure and hash."""
    from typing import TypeAlias

    def outer():
        MyType: TypeAlias = str

        def func(param: MyType) -> MyType:
            return param.upper()

        return func

    func1 = outer()
    closure1, hash1 = compute_closure(func1)

    func2 = outer()
    closure2, hash2 = compute_closure(func2)

    assert closure1 == closure2
    assert hash1 == hash2



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


def test_import_statements():
    """Test handling of various import statement types in _DependencyVisitor."""
    visitor = _DependencyVisitor()

    # Test simple import
    import_node = ast.Import(names=[ast.alias(name="os", asname=None)])
    visitor.visit_Import(import_node)
    assert "import os" in visitor.imports

    # Test import with alias
    import_node = ast.Import(names=[ast.alias(name="os.path", asname="path")])
    visitor.visit_Import(import_node)
    assert "import os.path as path" in visitor.imports

    # Test from import
    from_node = ast.ImportFrom(
        module="typing", names=[ast.alias(name="List", asname=None)], level=0
    )
    visitor.visit_ImportFrom(from_node)
    assert "from typing import List" in visitor.imports

    # Test from import with alias
    from_node = ast.ImportFrom(
        module="typing", names=[ast.alias(name="List", asname="TypeList")], level=0
    )
    visitor.visit_ImportFrom(from_node)
    assert "from typing import List as TypeList" in visitor.imports

    # Test from import without module (relative import)
    from_node = ast.ImportFrom(
        module=None, names=[ast.alias(name="helper", asname=None)], level=1
    )
    visitor.visit_ImportFrom(from_node)
    assert "from . import helper" in visitor.imports


def test_multiple_imports_from_same_module():
    """Test handling of multiple imports from the same module."""
    visitor = _DependencyVisitor()

    # Test multiple names in from import
    from_node = ast.ImportFrom(
        module="typing",
        names=[
            ast.alias(name="List", asname=None),
            ast.alias(name="Dict", asname="Dictionary"),
            ast.alias(name="Optional", asname=None),
        ],
        level=0,
    )
    visitor.visit_ImportFrom(from_node)
    assert "from typing import List" in visitor.imports
    assert "from typing import Dict as Dictionary" in visitor.imports
    assert "from typing import Optional" in visitor.imports

    # Test multiple regular imports
    import_node = ast.Import(
        names=[
            ast.alias(name="os", asname=None),
            ast.alias(name="sys", asname="system"),
            ast.alias(name="json", asname=None),
        ]
    )
    visitor.visit_Import(import_node)
    assert "import os" in visitor.imports
    assert "import sys as system" in visitor.imports
    assert "import json" in visitor.imports


def test_relative_imports():
    """Test handling of relative imports with different levels."""
    visitor = _DependencyVisitor()

    # Test single dot relative import
    from_node = ast.ImportFrom(
        module="utils", names=[ast.alias(name="helper", asname=None)], level=1
    )
    visitor.visit_ImportFrom(from_node)
    assert "from .utils import helper" in visitor.imports

    # Test double dot relative import
    from_node = ast.ImportFrom(
        module="utils", names=[ast.alias(name="helper", asname=None)], level=2
    )
    visitor.visit_ImportFrom(from_node)
    assert "from ..utils import helper" in visitor.imports

    # Test relative import without module name
    from_node = ast.ImportFrom(
        module=None, names=[ast.alias(name="helper", asname=None)], level=3
    )
    visitor.visit_ImportFrom(from_node)
    assert "from ... import helper" in visitor.imports


def test_import_in_function_dependencies():
    """Test that imports are correctly collected from function dependencies."""

    def func_with_imports():
        import os as operating_system

        return [operating_system.path.join("a", "b")]

    closure, _ = compute_closure(func_with_imports)
    # Note: The import os might not appear in closure as it's a standard library import
    assert "def func_with_imports():" in closure


def test_basic_imports():
    """Test handling of basic import statement types in _DependencyVisitor."""
    visitor = _DependencyVisitor()

    # Test simple import
    import_node = ast.Import(names=[ast.alias(name="os", asname=None)])
    visitor.visit_Import(import_node)
    assert "import os" in visitor.imports

    # Test import with alias
    import_node = ast.Import(names=[ast.alias(name="os.path", asname="path")])
    visitor.visit_Import(import_node)
    assert "import os.path as path" in visitor.imports


def test_from_imports():
    """Test handling of from-import statements in _DependencyVisitor."""
    visitor = _DependencyVisitor()

    # Test simple from import
    from_node = ast.ImportFrom(
        module="typing", names=[ast.alias(name="List", asname=None)], level=0
    )
    visitor.visit_ImportFrom(from_node)
    assert "from typing import List" in visitor.imports

    # Test from import with alias
    from_node = ast.ImportFrom(
        module="typing", names=[ast.alias(name="List", asname="TypeList")], level=0
    )
    visitor.visit_ImportFrom(from_node)
    assert "from typing import List as TypeList" in visitor.imports


def test_multiple_imports():
    """Test handling of multiple imports in a single statement."""
    visitor = _DependencyVisitor()

    # Test multiple names in from import
    from_node = ast.ImportFrom(
        module="typing",
        names=[
            ast.alias(name="List", asname=None),
            ast.alias(name="Dict", asname="Dictionary"),
            ast.alias(name="Optional", asname=None),
        ],
        level=0,
    )
    visitor.visit_ImportFrom(from_node)
    assert "from typing import List" in visitor.imports
    assert "from typing import Dict as Dictionary" in visitor.imports
    assert "from typing import Optional" in visitor.imports


def test_import_in_function():
    """Test that imports are correctly collected from function dependencies."""

    def func_with_imports():
        import os as operating_system  # noqa: F401
        from typing import List  # noqa: F401, UP035

        return ["test"]

    closure, _ = compute_closure(func_with_imports)
    assert "from typing import List" in closure
    assert "def func_with_imports():" in closure


def test_import_handling_edge_cases():
    """Test edge cases in import handling."""
    visitor = _DependencyVisitor()

    # Test import with empty module name
    from_node = ast.ImportFrom(
        module="", names=[ast.alias(name="helper", asname=None)], level=0
    )
    visitor.visit_ImportFrom(from_node)
    assert "from  import helper" in visitor.imports

    # Test import with None module name
    from_node = ast.ImportFrom(
        module=None, names=[ast.alias(name="helper", asname=None)], level=0
    )
    visitor.visit_ImportFrom(from_node)
    assert "from  import helper" in visitor.imports


def test_class_with_inner_function():
    """Test collecting class that uses functions defined within module."""

    def helper_function():
        return "helper"

    class TestClassWithFunction:
        def method(self):
            return helper_function()

    module = Mock()
    module.helper_function = helper_function
    module.TestClassWithFunction = TestClassWithFunction

    collector = _DependencyCollector()
    with (
        patch("inspect.isclass", return_value=True),
        patch(
            "inspect.getsource",
            return_value="class TestClassWithFunction:\n    def method(self):\n        return helper_function()\n",
        ),
    ):
        collector._collect_class_definition("TestClassWithFunction", module)
        assert "helper_function" in collector._visited_functions


def test_already_visited_function():
    """Test handling of already visited functions."""

    def test_func():
        pass

    collector = _DependencyCollector()
    collector._visited_functions.add("test_func")
    collector._collect_function_and_deps(test_func)
    # Should return early without adding to collected_code
    assert not collector._collected_code


def test_third_party_module_function():
    """Test handling of functions from third-party modules."""

    def test_func():
        pass

    collector = _DependencyCollector()
    with (
        patch("inspect.getmodule") as mock_getmodule,
        patch("inspect.getsource", side_effect=OSError),
    ):  # Simulate failure to get source
        mock_module = Mock()
        mock_module.__file__ = "/usr/lib/python3.10/site-packages/some_package.py"
        mock_getmodule.return_value = mock_module

        collector._collect_function_and_deps(test_func)
        # Should return early without adding to collected_code
        assert not collector._collected_code


def test_cached_module_function_lookup():
    """Test finding function in cached modules."""

    def target_func():
        return "target"

    def calling_func():
        return target_func()

    collector = _DependencyCollector()
    mock_module = Mock()
    mock_module.__file__ = "user_module.py"  # Not a third-party path
    mock_module.target_func = target_func

    collector._module_cache["test_module"] = mock_module

    with patch("inspect.getmodule") as mock_getmodule:
        mock_getmodule.return_value = mock_module
        collector._collect_function_and_deps(calling_func)

        assert "target_func" in collector._visited_functions


def test_visit_already_visited_function():
    """Test visiting already visited function in dependency ordering."""
    collector = _DependencyCollector()
    collector._main_function_name = "main_func"
    collector._dependency_graph = {"main_func": {"helper_func"}, "helper_func": set()}

    visited = set()
    ordered = []

    def mock_visit(func_name: str) -> None:
        if func_name in visited:
            return
        visited.add(func_name)
        ordered.append(func_name)

    with patch.object(collector, "_get_ordered_functions"):
        collector._get_ordered_functions()
        assert len(ordered) <= len(collector._dependency_graph)


def test_complex_decorator_calls():
    """Test collecting complex decorator calls with various node types."""
    visitor = _DependencyVisitor()

    # Test function call decorator
    func_call = ast.Call(
        func=ast.Name(id="decorator", ctx=ast.Load()),
        args=[ast.Name(id="ArgClass", ctx=ast.Load())],
        keywords=[
            ast.keyword(arg="kwarg", value=ast.Name(id="KwargClass", ctx=ast.Load()))
        ],
    )
    visitor._collect_decorator_calls(func_call)
    assert "decorator" in visitor.functions
    assert "ArgClass" in visitor.classes
    assert "KwargClass" in visitor.classes

    # Test attribute decorator
    attr_call = ast.Call(
        func=ast.Attribute(
            value=ast.Name(id="module", ctx=ast.Load()),
            attr="decorator",
            ctx=ast.Load(),
        ),
        args=[],
        keywords=[],
    )
    visitor._collect_decorator_calls(attr_call)
    assert "module" in visitor.variables

    # Test name decorator
    name_node = ast.Name(id="simple_decorator", ctx=ast.Load())
    visitor._collect_decorator_calls(name_node)
    assert "simple_decorator" in visitor.functions


def test_complex_function_calls():
    """Test visiting complex function calls with nested calls and arguments."""
    visitor = _DependencyVisitor()

    # Create a complex call with nested calls and name arguments
    call_node = ast.Call(
        func=ast.Name(id="outer_func", ctx=ast.Load()),
        args=[
            ast.Call(
                func=ast.Name(id="inner_func", ctx=ast.Load()), args=[], keywords=[]
            ),
            ast.Name(id="ArgClass", ctx=ast.Load()),
        ],
        keywords=[
            ast.keyword(
                arg="kwarg1",
                value=ast.Call(
                    func=ast.Name(id="factory_func", ctx=ast.Load()),
                    args=[],
                    keywords=[],
                ),
            ),
            ast.keyword(arg="kwarg2", value=ast.Name(id="KwargClass", ctx=ast.Load())),
        ],
    )

    visitor.visit_Call(call_node)

    # Check that all function and class names were collected
    assert "outer_func" in visitor.functions
    assert "inner_func" in visitor.functions
    assert "factory_func" in visitor.functions
    assert "ArgClass" in visitor.classes
    assert "KwargClass" in visitor.classes
    assert "ArgClass" in visitor.variables
    assert "KwargClass" in visitor.variables


def test_visited_function_early_return():
    """Test early return for already visited function."""

    def test_func():
        pass

    collector = _DependencyCollector()

    # Add function name to visited set
    collector._visited_functions.add(test_func.__name__)

    # This should trigger early return
    collector._collect_function_and_deps(test_func)
    assert test_func.__name__ in collector._visited_functions
    assert not collector._collected_code  # Should be empty due to early return


def test_cached_module_function_third_party():
    """Test early return when finding third-party function in cached modules."""

    def target_func():
        pass

    def calling_func():
        return target_func()  # noqa: F821

    collector = _DependencyCollector()

    # Setup main module mock with necessary attributes
    mock_module = Mock()
    mock_module.__file__ = "/usr/lib/site-packages/test.py"  # Third-party path
    mock_module.__name__ = "test_module"
    mock_module.target_func = target_func
    mock_module.calling_func = calling_func

    # Setup cache module mock with necessary attributes
    cache_module = Mock()
    cache_module.__file__ = "/usr/lib/site-packages/cache_module.py"
    cache_module.__name__ = "cache_module"
    cache_module.target_func = target_func

    collector._module_cache["test_module"] = cache_module

    with (
        patch("inspect.getmodule") as mock_getmodule,
        patch("inspect.getsource") as mock_getsource,
    ):
        # Return mock_module first for the main function, then None for subsequent calls
        mock_getmodule.side_effect = [mock_module]
        # Should never reach getsource due to early return
        mock_getsource.assert_not_called()

        collector._collect_function_and_deps(calling_func)
        assert not collector._collected_code


def test_visited_functions_early_return():
    """Test early return when function is already in visited functions."""

    def test_func():
        pass

    collector = _DependencyCollector()
    # Add function to visited set before collection
    collector._visited_functions.add(test_func.__name__)

    # Should return immediately without adding to collected_code
    collector._collect_function_and_deps(test_func)
    assert len(collector._collected_code) == 0


def test_collect_function_early_returns():
    """Test early returns in _collect_function_and_deps."""
    mock_sys_paths = [
        "/usr/lib/python3.10/site-packages",
        "/usr/local/lib/python3/site-packages",
    ]

    def test_func():
        pass

    with patch.object(sys, "path", mock_sys_paths):
        collector = _DependencyCollector()

        # Case 1: Already visited function
        collector._visited_functions.add(test_func.__name__)
        collector._collect_function_and_deps(test_func)
        assert (
            len(collector._collected_code) == 0
        ), "Should return early for visited function"

        # Case 2: Third party module function
        collector._visited_functions.clear()

        mock_module = Mock()
        mock_module.__file__ = "/usr/lib/python3.10/site-packages/third_party.py"

        with (
            patch("inspect.getmodule", return_value=mock_module),
            patch("inspect.getsource") as mock_getsource,
        ):
            collector._collect_function_and_deps(test_func)

            # Should return early without calling getsource
            mock_getsource.assert_not_called()
            assert len(collector._collected_code) == 0
            # assert test_func.__name__ not in collector._visited_functions


def test_collect_regular_function():
    """Test normal case without early returns."""
    mock_sys_paths = [
        "/usr/lib/python3.10/site-packages",
        "/usr/local/lib/python3/site-packages",
    ]

    def test_func():
        pass

    with patch.object(sys, "path", mock_sys_paths):
        collector = _DependencyCollector()

        mock_module = Mock()
        mock_module.__file__ = "/home/user/project/local.py"  # Not a third party path

        with (
            patch("inspect.getmodule", return_value=mock_module),
            patch("inspect.getsource", return_value="def test_func():\n    pass\n"),
            patch(
                "inspect.getsourcelines",
                return_value=(["def test_func():\n", "    pass\n"], 1),
            ),
        ):
            collector._collect_function_and_deps(test_func)

            # Should proceed with collection
            assert test_func.__name__ in collector._visited_functions
            assert len(collector._collected_code) == 1


def test_cached_module_loop_break():
    """Test that the loop breaks after finding a non-third-party function in cached modules."""
    mock_sys_paths = [
        "/usr/lib/python3.8/site-packages",
    ]

    def main_func():
        helper_func()  # noqa: F821

    def helper_func():
        return "test"

    with patch.object(sys, "path", mock_sys_paths):
        collector = _DependencyCollector()

        # Setup main module
        main_module = Mock(spec=["__file__", "__name__"])
        main_module.__file__ = "/home/user/project/main.py"
        main_module.__name__ = "main_module"

        # Setup multiple cached modules
        cache_module1 = Mock(spec=["__file__", "__name__", "helper_func"])
        cache_module1.__file__ = "/home/user/project1/local.py"  # Not third party
        cache_module1.__name__ = "cache_module1"
        cache_module1.helper_func = helper_func

        cache_module2 = Mock(spec=["__file__", "__name__", "helper_func"])
        cache_module2.__file__ = "/home/user/project2/local.py"  # Not third party
        cache_module2.__name__ = "cache_module2"
        cache_module2.helper_func = helper_func

        # Add modules to cache in order
        collector._module_cache["module1"] = cache_module1
        collector._module_cache["module2"] = cache_module2

        main_source = textwrap.dedent("""
            def main_func():
                helper_func()
        """)

        call_count = 0
        original_find_function = collector._find_function_in_module

        def mock_find_function(name, module):
            nonlocal call_count
            call_count += 1
            if name == "helper_func" and module in (cache_module1, cache_module2):
                return helper_func
            return original_find_function(name, module)

        with (
            patch.object(
                collector, "_find_function_in_module", side_effect=mock_find_function
            ),
            patch("inspect.getmodule") as mock_getmodule,
            patch("inspect.getsource") as mock_getsource,
            patch("inspect.getsourcelines") as mock_getsourcelines,
            patch("ast.parse") as mock_parse,
        ):
            mock_getmodule.side_effect = lambda f: {
                main_func: main_module,  # Return main_module for main_func
                helper_func: cache_module1,  # Return cache_module1 for helper_func
            }.get(f)

            # Setup source code returns
            mock_getsource.return_value = main_source
            mock_getsourcelines.return_value = (main_source.splitlines(True), 1)

            # Setup AST to include helper_func in visitor.functions
            call_node = ast.Call(
                func=ast.Name(id="helper_func", ctx=ast.Load()), args=[], keywords=[]
            )
            func_node = ast.FunctionDef(
                name="main_func",
                args=ast.arguments([], [], None, [], [], None, []),
                body=[ast.Expr(call_node)],
                decorator_list=[],
            )
            mock_parse.return_value = ast.Module(body=[func_node], type_ignores=[])

            collector._collect_function_and_deps(main_func)

            # Verify the cache was searched
            assert call_count >= 1, "Should have searched cache modules"

            # Verify both functions were processed
            assert "main_func" in collector._visited_functions
            assert "helper_func" in collector._visited_functions


def test_global_function_collection(tmp_path):
    """Test collection of functions defined in global scope."""
    # Create a temporary module file
    module_path = tmp_path / "test_module.py"
    module_path.write_text(
        textwrap.dedent("""
        def helper_global():
            return "global helper"

        def main_func():
            return helper_global()
        """)
    )

    # Import the temporary module
    sys.path.insert(0, str(tmp_path))
    try:
        import test_module

        collector = _DependencyCollector()
        collector._collect_function_and_deps(test_module.main_func)

        # Verify both functions were collected
        assert "main_func" in collector._visited_functions
        assert "helper_global" in collector._visited_functions

        # Verify the source code was collected
        assert any(
            "helper_global" in code for code in collector._collected_code.values()
        )
        assert any("main_func" in code for code in collector._collected_code.values())

    finally:
        # Clean up
        sys.path.pop(0)
        if "test_module" in sys.modules:
            del sys.modules["test_module"]


def test_function_dependency_cycle(tmp_path):
    """Test collection of functions with cyclic dependencies."""
    # Create a temporary module file with cyclic dependencies
    module_path = tmp_path / "test_module.py"
    module_path.write_text(
        textwrap.dedent("""
        def first():
            # first depends on second and third
            second()
            third()
            return "first"

        def second():
            # second depends on third
            third()
            return "second"

        def third():
            # third is at the bottom of dependency chain
            return "third"
        """)
    )

    # Import the temporary module
    sys.path.insert(0, str(tmp_path))
    try:
        collector = _DependencyCollector()

        # Add some pre-existing dependencies to force revisiting
        collector._dependency_graph = {
            "first": {"second", "third"},
            "second": {"third"},
            "third": set(),
        }
        collector._main_function_name = "first"

        # This should cause 'third' to be visited multiple times
        # but only included once in the output
        ordered_functions = collector._get_ordered_functions()

        # Verify order and uniqueness
        assert ordered_functions == ["third", "second", "first"]

        # Verify that each function appears exactly once
        assert len(ordered_functions) == len(set(ordered_functions))

    finally:
        # Clean up
        sys.path.pop(0)
        if "test_module" in sys.modules:
            del sys.modules["test_module"]


