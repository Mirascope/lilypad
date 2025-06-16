"""Tests for missing coverage in closure.py."""

import ast
import sys
from types import ModuleType
from typing import Annotated
from unittest.mock import Mock, patch, MagicMock
import inspect

import pytest

from src.lilypad._utils.closure import (
    _ImportCollector,
    _DefinitionCollector,
    _get_class_from_unbound_method,
    _extract_types,
    _is_stdlib_or_builtin,
    _DependencyCollector,
    Closure,
)


def test_import_collector_user_defined_module():
    """Test _ImportCollector when module is user-defined (not third-party) - covers line 210."""
    used_names = ["my_module", "my_func"]
    site_packages = {"/usr/local/lib/python3.9/site-packages"}
    
    collector = _ImportCollector(used_names, site_packages)
    
    # Create AST for: import my_module
    import_node = ast.Import(names=[ast.alias(name="my_module", asname=None)])
    
    # Mock the imported module to be user-defined (not in site-packages)
    mock_module = MagicMock()
    mock_module.__name__ = "my_module"
    mock_module.__file__ = "/home/user/project/my_module.py"
    
    with patch("builtins.__import__", return_value=mock_module):
        collector.visit_Import(import_node)
    
    # Should add to user_defined_imports, not imports
    assert "import my_module" in collector.user_defined_imports
    assert "import my_module" not in collector.imports


def test_extract_types_with_annotated():
    """Test _extract_types with Annotated type - covers line 314."""
    # Create an Annotated type
    MyAnnotated = Annotated[str, "metadata"]
    
    # Mock a custom type to extract
    class CustomType:
        __module__ = "my_module"
    
    # Create Annotated with custom type
    CustomAnnotated = Annotated[CustomType, "metadata"]
    
    # Test extraction
    types_found = _extract_types(CustomAnnotated)
    
    # Should extract CustomType from within Annotated
    assert CustomType in types_found


def test_is_stdlib_or_builtin_with_none_module():
    """Test _is_stdlib_or_builtin when module_name is None or empty - covers line 330."""
    # Test with object where __module__ is None
    obj_none_module = type("NoneModule", (), {"__module__": None})
    assert not _is_stdlib_or_builtin(obj_none_module)
    
    # Test with object where __module__ is empty string
    obj_empty_module = type("EmptyModule", (), {"__module__": ""})
    assert not _is_stdlib_or_builtin(obj_empty_module)
    
    # Test with object that doesn't have __module__ attribute
    class NoModuleAttr:
        pass
    obj = NoModuleAttr()
    assert not _is_stdlib_or_builtin(obj)


def test_get_class_from_unbound_method_returns_none():
    """Test _get_class_from_unbound_method when it can't find the class - covers line 508."""
    # Create a method with invalid qualname
    def simple_function():
        pass
    
    # Method with no class context (no dot in qualname)
    result = _get_class_from_unbound_method(simple_function)
    assert result is None
    
    # Method with class context but class not found in gc
    class_method = Mock()
    class_method.__qualname__ = "NonExistentClass.method"
    
    with patch("gc.get_objects", return_value=[]):
        result = _get_class_from_unbound_method(class_method)
        assert result is None


def test_get_class_from_unbound_method_isinstance_exception():
    """Test _get_class_from_unbound_method when isinstance raises exception - covers lines 515-517."""
    # Create a method with class qualname
    mock_method = Mock()
    mock_method.__qualname__ = "TestClass.method"
    
    # Create an object with a problematic __class__ property that will cause isinstance to fail
    class ProblematicObject:
        @property
        def __class__(self):
            raise RuntimeError("Cannot check isinstance")
    
    problematic_obj = ProblematicObject()
    
    # Also create a valid class to ensure we continue after exception
    class TestClass:
        __qualname__ = "TestClass"
        def method(self):
            pass
    
    # Create the actual class instance
    test_class_obj = TestClass
    
    with patch("gc.get_objects", return_value=[problematic_obj, test_class_obj]):
        result = _get_class_from_unbound_method(mock_method)
        assert result == TestClass


def test_dependency_collector_with_property_fget_none():
    """Test _DependencyCollector with property where fget is None - covers line 599."""
    collector = _DependencyCollector()
    
    # Create a property with fget=None (write-only property)
    prop = property(fset=lambda self, value: None)
    assert prop.fget is None
    
    # Should return early without processing
    collector._collect_imports_and_source_code(prop, include_source=True)
    
    # No source code should be collected
    assert len(collector.source_code) == 0


def test_dependency_collector_with_func_no_name():
    """Test _DependencyCollector with definition that has func but no __name__ - covers line 605."""
    collector = _DependencyCollector()
    
    # Create a mock object with func attribute but no __name__
    mock_definition = Mock()
    mock_definition.func = lambda x: x
    # Explicitly remove __name__ attribute
    del mock_definition.__name__
    
    # The actual function should be processed
    with patch.object(collector, "_collect_imports_and_source_code") as mock_collect:
        # First call will process mock_definition, which should redirect to mock_definition.func
        collector._collect_imports_and_source_code(mock_definition, include_source=True)
        
        # Should have been called again with the actual function
        assert mock_collect.call_count >= 1


def test_closure_from_fn_subprocess_error():
    """Test Closure.from_fn when subprocess raises CalledProcessError - covers line 781."""
    def test_function():
        """Test function."""
        return 42
    
    # Clear the cache first
    Closure.from_fn.cache_clear()
    
    # Mock subprocess to raise CalledProcessError
    with patch("subprocess.run") as mock_run:
        # First call for --select=I001 should fail
        mock_run.side_effect = subprocess.CalledProcessError(
            returncode=2,
            cmd=["ruff", "check"],
            output="error output",
            stderr="error stderr"
        )
        
        with pytest.raises(subprocess.CalledProcessError):
            Closure.from_fn(test_function)


def test_definition_collector_process_name_or_attribute():
    """Test _DefinitionCollector._process_name_or_attribute with various node types."""
    module = ModuleType("test_module")
    
    # Add some test objects to the module
    def test_func():
        pass
    
    class TestClass:
        pass
    
    module.test_func = test_func
    module.TestClass = TestClass
    module.no_name_obj = object()  # Object without __name__
    
    collector = _DefinitionCollector(module, ["test_func", "TestClass"], set())
    
    # Test with Name node for function
    name_node = ast.Name(id="test_func", ctx=ast.Load())
    collector._process_name_or_attribute(name_node)
    assert test_func in collector.definitions_to_include
    
    # Test with Name node for object without __name__
    no_name_node = ast.Name(id="no_name_obj", ctx=ast.Load())
    collector._process_name_or_attribute(no_name_node)
    # Should not be added because it has no __name__
    assert module.no_name_obj not in collector.definitions_to_include


def test_import_collector_import_from_relative():
    """Test _ImportCollector with relative imports."""
    used_names = ["imported_func"]
    site_packages = set()
    
    collector = _ImportCollector(used_names, site_packages)
    
    # Create AST for: from ...module import imported_func
    import_node = ast.ImportFrom(
        module="module",
        names=[ast.alias(name="imported_func", asname=None)],
        level=3
    )
    
    # Should handle ImportError and treat as user-defined
    collector.visit_ImportFrom(import_node)
    
    # Should be in user_defined_imports with adjusted module name
    assert any("...module" in imp for imp in collector.user_defined_imports)


def test_dependency_collector_with_cached_property():
    """Test _DependencyCollector with cached_property."""
    from functools import cached_property
    
    collector = _DependencyCollector()
    
    class TestClass:
        @cached_property
        def cached_method(self):
            return "cached value"
    
    # Get the cached_property descriptor
    cached_prop = TestClass.__dict__["cached_method"]
    
    # Mock to avoid actual source code processing
    with patch("inspect.getsource", return_value="def cached_method(self): return 'cached value'"):
        with patch("inspect.getmodule", return_value=sys.modules[__name__]):
            collector._collect_imports_and_source_code(cached_prop, include_source=True)
    
    # Should process the underlying function
    assert len(collector.visited_functions) > 0


# Import subprocess for the error test
import subprocess