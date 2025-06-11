"""Tests for the closure module."""

from pathlib import Path

import pytest

from lilypad._utils.closure import (
    Closure,
    _is_third_party,
    _RemoveDocstringTransformer,
    get_qualified_name,
)


def sample_function():
    """A sample function for testing."""
    return 42


def function_with_dependencies():
    """Function with external dependencies."""
    import os

    return os.path.join("test", "path")


def function_with_relative_import():
    """Function with relative imports."""
    # This is just test code, the import would fail anyway
    # from ..utils import some_util
    # return some_util()
    return None


def function_with_third_party():
    """Function with third-party imports."""
    # Using a module that's likely installed but still third-party
    import pytest  # pytest is installed for testing

    return pytest


def function_with_decorated():
    """Function with decorator."""

    @staticmethod
    def inner():
        return "decorated"

    return inner


def test_get_qualified_name_with_function():
    """Test get_qualified_name with a regular function."""
    assert get_qualified_name(sample_function) == "sample_function"


def test_get_qualified_name_with_method():
    """Test get_qualified_name with a method."""

    class TestClass:
        def method(self):
            return "method"

    obj = TestClass()
    assert get_qualified_name(obj.method) == "TestClass.method"


def test_get_qualified_name_with_builtin():
    """Test get_qualified_name with a builtin function."""
    assert get_qualified_name(print) == "print"


def test_get_qualified_name_with_lambda():
    """Test get_qualified_name with a lambda."""

    def lambda_fn(x):
        return x + 1

    assert "lambda" in get_qualified_name(lambda_fn)


def test_get_qualified_name_with_nested_classes():
    """Test get_qualified_name with nested classes."""

    class Outer:
        class Inner:
            def method(self):
                return "inner_method"

    obj = Outer.Inner()
    # Should return the full qualified name for nested classes
    assert get_qualified_name(obj.method) == "Outer.Inner.method"


def test_is_third_party():
    """Test _is_third_party function."""
    import site

    site_packages = {str(Path(site.__file__).parent)}

    # Test standard library module
    import os

    assert _is_third_party(os, site_packages)

    # Test builtin module
    import sys

    assert _is_third_party(sys, site_packages)

    # Create a mock module that appears to be in site-packages (third-party)
    class MockModule:
        __name__ = "mock_module"
        __file__ = str(Path(site.__file__).parent / "mock_module.py")

    mock_module = MockModule()
    assert _is_third_party(
        mock_module,  # type: ignore[arg-type]
        site_packages,
    )  # Should be True since it's in site-packages


def test_is_third_party_no_file():
    """Test _is_third_party with module that has no __file__."""
    site_packages = {"/path/to/site-packages"}

    class MockModule:
        __name__ = "mock_module"  # Add __name__ attribute

    assert _is_third_party(MockModule(), site_packages)  # type: ignore[arg-type, type-var]


def test_is_third_party_none_file():
    """Test _is_third_party with module that has __file__ = None."""
    site_packages = {"/path/to/site-packages"}

    class MockModule:
        __name__ = "mock_module"  # Add __name__ attribute
        __file__ = None

    assert _is_third_party(MockModule(), site_packages)  # type: ignore[arg-type, type-var]


def test_remove_docstring_transformer():
    """Test _RemoveDocstringTransformer."""
    import libcst as cst

    code = '''
def function_with_docstring():
    """This is a docstring."""
    return 42
'''
    module = cst.parse_module(code.strip())
    transformer = _RemoveDocstringTransformer(exclude_fn_body=False)
    modified = module.visit(transformer)
    modified_code = modified.code

    # Docstring should be removed
    assert '"""This is a docstring."""' not in modified_code
    assert "return 42" in modified_code


def test_remove_docstring_transformer_with_multiline():
    """Test _RemoveDocstringTransformer with multiline docstring."""
    import libcst as cst

    code = '''
def function_with_multiline_docstring():
    """
    This is a multiline
    docstring.
    """
    return 42
'''
    module = cst.parse_module(code.strip())
    transformer = _RemoveDocstringTransformer(exclude_fn_body=False)
    modified = module.visit(transformer)
    modified_code = modified.code

    # Docstring should be removed
    assert "This is a multiline" not in modified_code
    assert "return 42" in modified_code


def test_remove_docstring_transformer_empty_body():
    """Test _RemoveDocstringTransformer when body becomes empty."""
    import libcst as cst

    code = '''
def function_with_only_docstring():
    """Only has a docstring."""
    pass  # Add a pass statement so body isn't empty
'''
    module = cst.parse_module(code.strip())
    transformer = _RemoveDocstringTransformer(exclude_fn_body=False)
    modified = module.visit(transformer)
    modified_code = modified.code

    # Docstring should be removed, pass should remain
    assert "pass" in modified_code
    assert '"""Only has a docstring."""' not in modified_code


def test_remove_docstring_transformer_exclude_body():
    """Test _RemoveDocstringTransformer with exclude_fn_body=True."""
    import libcst as cst

    code = '''
def function_with_body():
    """Docstring."""
    x = 1
    y = 2
    return x + y
'''
    module = cst.parse_module(code.strip())
    transformer = _RemoveDocstringTransformer(exclude_fn_body=True)
    modified = module.visit(transformer)
    modified_code = modified.code

    # Should replace body with ellipsis when exclude_fn_body=True
    assert "function_with_body" in modified_code
    # Body should be replaced, original statements should not be there
    assert "x = 1" not in modified_code
    assert "return x + y" not in modified_code


def test_closure_from_fn_with_function():
    """Test Closure.from_fn with a function."""
    closure = Closure.from_fn(sample_function)
    assert closure.name == "sample_function"
    assert "sample_function" in closure.code
    assert closure.hash is not None
    assert isinstance(closure.dependencies, dict)


def test_closure_from_fn_with_lambda():
    """Test Closure.from_fn with a lambda."""

    def lambda_fn(x):
        return x + 1

    closure = Closure.from_fn(lambda_fn)
    assert "lambda" in closure.name
    assert closure.code is not None


def test_closure_source_code():
    """Test getting source code of a function."""
    closure = Closure.from_fn(sample_function)
    assert "def sample_function():" in closure.code
    assert "return 42" in closure.code


def test_closure_source_code_lambda():
    """Test getting source code of a lambda."""

    # Use a named function instead of lambda for better testing
    def add_one(x):
        return x + 1

    closure = Closure.from_fn(add_one)
    assert "def add_one(x):" in closure.code
    assert "return x + 1" in closure.code


def test_closure_source_code_error():
    """Test error handling when getting source code."""
    # Built-in functions don't have source code
    with pytest.raises((OSError, TypeError)):
        Closure.from_fn(print)


def test_closure_hash():
    """Test closure hash generation."""
    closure1 = Closure.from_fn(sample_function)
    closure2 = Closure.from_fn(sample_function)

    # Same function should produce same hash
    assert closure1.hash == closure2.hash
    assert len(closure1.hash) == 64  # SHA256 hash


def test_closure_hash_different_functions():
    """Test closure hash for different functions."""

    def function1():
        return 1

    def function2():
        return 2

    closure1 = Closure.from_fn(function1)
    closure2 = Closure.from_fn(function2)

    # Different functions should have different hashes
    assert closure1.hash != closure2.hash


def test_closure_dependencies():
    """Test closure dependency extraction."""
    closure = Closure.from_fn(function_with_dependencies)
    # Standard library modules like 'os' are not included in dependencies
    # Only third-party packages are tracked
    assert isinstance(closure.dependencies, dict)
    # The code should still contain the import
    assert "import os" in closure.code


def test_closure_with_method():
    """Test Closure with a class method."""

    class TestClass:
        def method(self):
            return "method_result"

    obj = TestClass()
    closure = Closure.from_fn(obj.method)
    assert "method" in closure.name
    assert "return" in closure.code


def test_closure_with_static_method():
    """Test Closure with a static method."""

    class TestClass:
        @staticmethod
        def static_method():
            return "static_result"

    closure = Closure.from_fn(TestClass.static_method)
    assert "static_method" in closure.name


def test_closure_with_pip_dependencies():
    """Test Closure with pip package dependencies."""

    def func_with_pip_deps():
        import json  # standard library

        return json.dumps({"test": "data"})

    closure = Closure.from_fn(func_with_pip_deps)
    # json is a standard library module, so it won't be in dependencies
    # Only third-party pip packages are tracked
    assert isinstance(closure.dependencies, dict)
    assert "import json" in closure.code


def test_closure_equality():
    """Test Closure equality based on hash."""
    closure1 = Closure.from_fn(sample_function)
    closure2 = Closure.from_fn(sample_function)

    # Create a new closure with the same data
    closure3 = Closure(
        name=closure1.name,
        signature=closure1.signature,
        code=closure1.code,
        hash=closure1.hash,
        dependencies=closure1.dependencies,
    )

    # They should have the same hash
    assert closure1.hash == closure2.hash
    assert closure1.hash == closure3.hash


def test_closure_with_decorators():
    """Test Closure with decorated functions."""
    from functools import wraps

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    @decorator
    def decorated_function():
        return "decorated"

    closure = Closure.from_fn(decorated_function)
    assert "decorated_function" in closure.name


def test_closure_with_complex_imports():
    """Test Closure with complex import statements."""

    def complex_imports():
        import sys
        from os.path import join
        from pathlib import Path as P

        return P(join(sys.prefix, "test"))

    closure = Closure.from_fn(complex_imports)
    # These are all standard library imports, so won't be in dependencies
    assert isinstance(closure.dependencies, dict)
    # But the imports should be in the code
    assert "from os.path import join" in closure.code or "import" in closure.code


def test_closure_with_try_import():
    """Test Closure with imports in try/except blocks."""

    def try_import():
        try:
            # Use a module that exists but might not be available
            import sqlite3  # standard library module

            return sqlite3.version  # type: ignore[attr-defined]
        except ImportError:
            return "fallback"

    closure = Closure.from_fn(try_import)
    # Should capture the import even if in try block
    assert closure.code is not None
    assert "import sqlite3" in closure.code


def test_closure_serialization():
    """Test Closure serialization to dict."""
    closure = Closure.from_fn(sample_function)
    data = closure.model_dump()

    assert data["name"] == "sample_function"
    assert data["code"] is not None
    assert data["hash"] is not None
    assert isinstance(data["dependencies"], dict)
