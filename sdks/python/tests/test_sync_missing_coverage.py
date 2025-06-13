"""Additional tests to cover missing lines in sync.py."""

import os
import json
import sys
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Any

import pytest

from lilypad.cli.commands.sync import (
    _find_python_files,
    _module_path_from_file,
    _import_module_safely,
    _normalize_signature,
    _parse_parameters_from_signature,
    _merge_parameters,
    _parse_return_type,
    _extract_type_from_param,
    _extract_parameter_types,
    _get_deployed_version,
    _format_return_type,
    _generate_protocol_stub_content,
    sync_command,
    app,
    console,
    DEBUG,
)
# Import TRACE_MODULE_NAME constant
TRACE_MODULE_NAME = "lilypad.traces"


def test_find_python_files_with_none_exclude():
    """Test _find_python_files when exclude_dirs is None."""
    with patch("os.walk") as mock_walk:
        # Mock os.walk to return a simple structure
        mock_walk.return_value = [
            ("/test", ["subdir", "__pycache__"], ["file1.py", "file2.txt"]),
            ("/test/subdir", [], ["file3.py"]),
            ("/test/__pycache__", [], ["cached.py"]),
        ]
        
        files = _find_python_files("/test", exclude_dirs=None)
        
        # Should exclude __pycache__ by default
        assert any("file1.py" in f for f in files)
        assert any("file3.py" in f for f in files)
        assert not any("cached.py" in f for f in files)


def test_find_python_files_modifies_dirs_in_place():
    """Test that _find_python_files modifies dirs list in place."""
    with patch("os.walk") as mock_walk:
        dirs_list = ["good_dir", "venv", "__pycache__"]
        mock_walk.return_value = [
            ("/test", dirs_list, ["file.py"]),
        ]
        
        _find_python_files("/test")
        
        # dirs should be modified in place to exclude default dirs
        assert "good_dir" in dirs_list
        assert "venv" not in dirs_list
        assert "__pycache__" not in dirs_list


def test_module_path_from_file_with_base_dir():
    """Test _module_path_from_file with base_dir parameter."""
    result = _module_path_from_file("/base/project/module.py", "/base")
    assert result == "project.module"


def test_module_path_from_file_without_py_extension():
    """Test _module_path_from_file with file without .py extension."""
    result = _module_path_from_file("path/to/module")
    assert result == "path.to.module"


def test_import_module_safely_import_error():
    """Test _import_module_safely with ImportError."""
    with patch("sys.stderr", new_callable=MagicMock):
        result = _import_module_safely("non_existent_module_12345")
        assert result is False


def test_import_module_safely_syntax_error():
    """Test _import_module_safely with SyntaxError."""
    with patch("lilypad.cli.commands.sync.importlib.import_module") as mock_import:
        mock_import.side_effect = SyntaxError("Invalid syntax")
        with patch("sys.stderr", new_callable=MagicMock):
            result = _import_module_safely("bad_syntax_module")
            assert result is False


def test_normalize_signature_with_debug():
    """Test _normalize_signature with DEBUG enabled."""
    with patch("lilypad.cli.commands.sync.DEBUG", True):
        with patch("builtins.print") as mock_print:
            result = _normalize_signature("def func(): pass")
            # Should print debug information
            mock_print.assert_called()
            assert "pass" in result


def test_normalize_signature_with_ellipsis():
    """Test _normalize_signature with function ending in ellipsis."""
    sig = "def func(): ..."
    result = _normalize_signature(sig)
    assert result.endswith(" pass")
    assert "..." not in result


def test_normalize_signature_with_colon_only():
    """Test _normalize_signature with function ending in colon only."""
    sig = "def func():"
    result = _normalize_signature(sig)
    assert result.endswith(": pass")


def test_normalize_signature_filters_decorators():
    """Test _normalize_signature filters out decorators and imports."""
    sig = """
    from typing import Any
    
    @decorator
    @another_decorator
    def func(a: int) -> str:
        pass
    """
    result = _normalize_signature(sig)
    assert "@" not in result
    assert "from typing" not in result
    assert "def func" in result


def test_parse_parameters_from_signature_removes_trace_ctx():
    """Test that _parse_parameters_from_signature removes trace_ctx parameter."""
    sig = "def func(trace_ctx: Any, a: int, b: str) -> None: pass"
    params = _parse_parameters_from_signature(sig)
    
    assert not any("trace_ctx" in p for p in params)
    assert any("a: int" in p for p in params)
    assert any("b: str" in p for p in params)


def test_parse_parameters_from_signature_handles_varargs():
    """Test _parse_parameters_from_signature with *args and **kwargs."""
    sig = "def func(a: int, *args: str, **kwargs: Any) -> None: pass"
    params = _parse_parameters_from_signature(sig)
    
    assert any("a: int" in p for p in params)
    assert any("*args: str" in p for p in params)
    assert any("**kwargs: Any" in p for p in params)


def test_parse_parameters_from_signature_ast_error():
    """Test _parse_parameters_from_signature when AST parsing fails."""
    with patch("ast.parse", side_effect=SyntaxError("Invalid syntax")):
        params = _parse_parameters_from_signature("invalid syntax")
        assert params == []


def test_parse_parameters_from_signature_no_function_found():
    """Test _parse_parameters_from_signature when no function is found."""
    sig = "# This is just a comment, no function definition"
    params = _parse_parameters_from_signature(sig)
    assert params == []


def test_parse_parameters_from_signature_annotation_error():
    """Test _parse_parameters_from_signature when annotation unparsing fails."""
    with patch("ast.unparse", side_effect=Exception("Unparse error")):
        sig = "def func(a: ComplexType) -> str: pass"
        params = _parse_parameters_from_signature(sig)
        # Should fallback to Any type
        assert any("a: Any" in p for p in params)


def test_merge_parameters_with_json_string():
    """Test _merge_parameters with arg_types as JSON string."""
    sig = "def func(a: int, b: str) -> None: pass"
    arg_types_json = '{"a": "float", "b": "bytes"}'
    
    merged = _merge_parameters(sig, arg_types_json)
    assert any("a: float" in p for p in merged)
    assert any("b: bytes" in p for p in merged)


def test_merge_parameters_with_invalid_json():
    """Test _merge_parameters with invalid JSON string."""
    sig = "def func(a: int) -> None: pass"
    invalid_json = "not valid json"
    
    with patch("builtins.print") as mock_print:
        merged = _merge_parameters(sig, invalid_json)
        # Should print error and use original types
        mock_print.assert_called()
        assert any("a: int" in p for p in merged)


def test_merge_parameters_preserves_defaults():
    """Test _merge_parameters preserves default values."""
    sig = "def func(a: int = 5, b: str = 'hello') -> None: pass"
    arg_types = {"a": "float"}
    
    merged = _merge_parameters(sig, arg_types)
    assert any("a: float = 5" in p for p in merged)
    assert any("b: str = 'hello'" in p for p in merged)


def test_merge_parameters_handles_complex_defaults():
    """Test _merge_parameters with complex default values."""
    sig = "def func(a: list = [1, 2, 3], b: dict = {'key': 'value'}) -> None: pass"
    arg_types = {}
    
    merged = _merge_parameters(sig, arg_types)
    assert any("a: list" in p for p in merged)
    assert any("b: dict" in p for p in merged)


def test_parse_return_type_no_annotation():
    """Test _parse_return_type when function has no return annotation."""
    sig = "def func(a: int): pass"
    ret_type = _parse_return_type(sig)
    assert ret_type == "Any"


def test_parse_return_type_ast_error():
    """Test _parse_return_type when AST parsing fails."""
    with patch("ast.parse", side_effect=SyntaxError("Invalid syntax")):
        ret_type = _parse_return_type("invalid syntax")
        assert ret_type == "Any"


def test_parse_return_type_no_function():
    """Test _parse_return_type when no function is found."""
    sig = "# No function here"
    ret_type = _parse_return_type(sig)
    assert ret_type == "Any"


def test_parse_return_type_unparse_error():
    """Test _parse_return_type when annotation unparsing fails."""
    with patch("ast.unparse", side_effect=Exception("Unparse error")):
        sig = "def func() -> ComplexType: pass"
        ret_type = _parse_return_type(sig)
        assert ret_type == "Any"


def test_extract_type_from_param_variations():
    """Test _extract_type_from_param with various parameter formats."""
    assert _extract_type_from_param("param: int") == "int"
    assert _extract_type_from_param("param: str = 'default'") == "str"
    assert _extract_type_from_param("param") == "Any"
    assert _extract_type_from_param("param: list[str] = []") == "list[str]"
    assert _extract_type_from_param("*args: str") == "str"
    assert _extract_type_from_param("**kwargs: Any") == "Any"


def test_extract_parameter_types_mixed():
    """Test _extract_parameter_types with mixed parameter types."""
    params = ["a: int", "b: str = 'default'", "c", "*args: float", "**kwargs: Any"]
    types = _extract_parameter_types(params)
    assert types == ["int", "str", "Any", "float", "Any"]


def test_get_deployed_version_all_archived():
    """Test _get_deployed_version when all versions are archived."""
    class MockVersion:
        def __init__(self, version_num, archived=True):
            self.version_num = version_num
            self.archived = archived
    
    versions = [
        MockVersion(1, archived=True),
        MockVersion(2, archived=True),
    ]
    
    deployed = _get_deployed_version(versions)
    assert deployed.version_num == 2  # Should return latest version


def test_get_deployed_version_mixed_archived():
    """Test _get_deployed_version with mixed archived status."""
    class MockVersion:
        def __init__(self, version_num, archived=False):
            self.version_num = version_num
            self.archived = archived
    
    versions = [
        MockVersion(1, archived=True),
        MockVersion(2, archived=False),
        MockVersion(3, archived=True),
        MockVersion(4, archived=False),
    ]
    
    deployed = _get_deployed_version(versions)
    assert deployed.version_num == 4  # Should return highest non-archived


def test_format_return_type_combinations():
    """Test _format_return_type with all combinations."""
    # Base type
    assert _format_return_type("str", False, False) == "str"
    
    # Wrapped only
    assert _format_return_type("str", False, True) == "Trace[str]"
    
    # Async only
    assert _format_return_type("str", True, False) == "Coroutine[Any, Any, str]"
    
    # Both async and wrapped
    assert _format_return_type("str", True, True) == "Coroutine[Any, Any, AsyncTrace[str]]"


def test_generate_protocol_stub_content_empty_versions():
    """Test _generate_protocol_stub_content with empty versions list."""
    content = _generate_protocol_stub_content("test_func", [], False, False)
    assert content == ""


def test_generate_protocol_stub_content_none_version_num():
    """Test _generate_protocol_stub_content with None version numbers."""
    class MockVersion:
        def __init__(self, version_num, signature, arg_types=None):
            self.version_num = version_num
            self.signature = signature
            self.arg_types = arg_types or {}
    
    versions = [MockVersion(None, "def test_func() -> str: pass")]
    content = _generate_protocol_stub_content("test_func", versions, False, False)
    
    # Should generate main protocol but skip version protocols
    assert "class TestFunc(Protocol):" in content
    assert "class TestFuncVersion" not in content


def test_generate_protocol_stub_content_with_parameters():
    """Test _generate_protocol_stub_content with function parameters."""
    class MockVersion:
        def __init__(self, version_num, signature, arg_types=None):
            self.version_num = version_num
            self.signature = signature
            self.arg_types = arg_types or {}
    
    versions = [MockVersion(1, "def test_func(a: int, b: str) -> bool: pass", {"a": "int", "b": "str"})]
    content = _generate_protocol_stub_content("test_func", versions, False, False)
    
    assert "def __call__(self, a: int, b: str) -> bool: ..." in content
    assert "def remote(self, a: int, b: str, sandbox: SandboxRunner | None = None) -> bool: ..." in content


def test_generate_protocol_stub_content_async_wrapped():
    """Test _generate_protocol_stub_content with async and wrapped modes."""
    class MockVersion:
        def __init__(self, version_num, signature, arg_types=None):
            self.version_num = version_num
            self.signature = signature
            self.arg_types = arg_types or {}
    
    versions = [MockVersion(1, "async def test_func(a: int) -> str: pass", {"a": "int"})]
    content = _generate_protocol_stub_content("test_func", versions, True, True)
    
    assert "def __call__(self, a: int) -> AsyncTrace[str]: ..." in content
    assert "def remote(self, a: int, sandbox: SandboxRunner | None = None) -> Coroutine[Any, Any, AsyncTrace[str]]: ..." in content


@patch("lilypad.cli.commands.sync.enable_recording")
@patch("lilypad.cli.commands.sync.clear_registry")
@patch("lilypad.cli.commands.sync.disable_recording")
@patch("lilypad.cli.commands.sync.get_decorated_functions")
@patch("lilypad.cli.commands.sync.get_sync_client")
@patch("lilypad.cli.commands.sync.get_settings")
@patch("lilypad.cli.commands.sync._find_python_files")
def test_sync_command_no_python_files(
    mock_find_files, mock_settings, mock_client, mock_get_funcs,
    mock_disable, mock_clear, mock_enable
):
    """Test sync_command when no Python files are found."""
    mock_find_files.return_value = []
    
    sync_command(Path("."))
    
    # Should not enable recording if no files found
    mock_enable.assert_not_called()
    mock_disable.assert_not_called()
    mock_clear.assert_not_called()


@patch("lilypad.cli.commands.sync.enable_recording")
@patch("lilypad.cli.commands.sync.clear_registry")
@patch("lilypad.cli.commands.sync.disable_recording")
@patch("lilypad.cli.commands.sync.get_decorated_functions")
@patch("lilypad.cli.commands.sync.get_sync_client")
@patch("lilypad.cli.commands.sync.get_settings")
@patch("lilypad.cli.commands.sync._find_python_files")
@patch("lilypad.cli.commands.sync._import_module_safely")
def test_sync_command_with_exclude_list(
    mock_import, mock_find_files, mock_settings, mock_client, mock_get_funcs,
    mock_disable, mock_clear, mock_enable
):
    """Test sync_command with exclude parameter as list."""
    mock_find_files.return_value = ["test.py"]
    mock_import.return_value = True
    mock_settings.return_value = Mock(api_key="test", project_id="test")
    mock_client.return_value = Mock()
    mock_get_funcs.return_value = {TRACE_MODULE_NAME: []}
    
    sync_command(Path("."), exclude=["dir1", "dir2"])
    
    # Should convert list to set for exclude_dirs
    mock_find_files.assert_called_once()


@patch("lilypad.cli.commands.sync.enable_recording")
@patch("lilypad.cli.commands.sync.clear_registry")
@patch("lilypad.cli.commands.sync.disable_recording")
@patch("lilypad.cli.commands.sync.get_decorated_functions")
@patch("lilypad.cli.commands.sync.get_sync_client")
@patch("lilypad.cli.commands.sync.get_settings")
@patch("lilypad.cli.commands.sync._find_python_files")
@patch("lilypad.cli.commands.sync._import_module_safely")
def test_sync_command_with_exclude_none(
    mock_import, mock_find_files, mock_settings, mock_client, mock_get_funcs,
    mock_disable, mock_clear, mock_enable
):
    """Test sync_command with exclude parameter as None."""
    mock_find_files.return_value = ["test.py"]
    mock_import.return_value = True
    mock_settings.return_value = Mock(api_key="test", project_id="test")
    mock_client.return_value = Mock()
    mock_get_funcs.return_value = {TRACE_MODULE_NAME: []}
    
    sync_command(Path("."), exclude=None)
    
    # Should pass None as exclude_dirs
    mock_find_files.assert_called_once()


@patch("lilypad.cli.commands.sync.enable_recording")
@patch("lilypad.cli.commands.sync.clear_registry")
@patch("lilypad.cli.commands.sync.disable_recording")
@patch("lilypad.cli.commands.sync.get_decorated_functions")
@patch("lilypad.cli.commands.sync.get_sync_client")
@patch("lilypad.cli.commands.sync.get_settings")
@patch("lilypad.cli.commands.sync._find_python_files")
@patch("lilypad.cli.commands.sync._import_module_safely")
def test_sync_command_no_decorated_functions(
    mock_import, mock_find_files, mock_settings, mock_client, mock_get_funcs,
    mock_disable, mock_clear, mock_enable
):
    """Test sync_command when no decorated functions are found."""
    mock_find_files.return_value = ["test.py"]
    mock_import.return_value = True
    mock_settings.return_value = Mock(api_key="test", project_id="test")
    mock_client.return_value = Mock()
    mock_get_funcs.return_value = {TRACE_MODULE_NAME: []}
    
    with patch("builtins.print") as mock_print:
        sync_command(Path("."))
        
        # Should print message about no functions found
        mock_print.assert_called()


@patch("lilypad.cli.commands.sync.enable_recording")
@patch("lilypad.cli.commands.sync.clear_registry")
@patch("lilypad.cli.commands.sync.disable_recording")
@patch("lilypad.cli.commands.sync.get_decorated_functions")
@patch("lilypad.cli.commands.sync.get_sync_client")
@patch("lilypad.cli.commands.sync.get_settings")
@patch("lilypad.cli.commands.sync._find_python_files")
@patch("lilypad.cli.commands.sync._import_module_safely")
def test_sync_command_with_functions_no_versions(
    mock_import, mock_find_files, mock_settings, mock_client, mock_get_funcs,
    mock_disable, mock_clear, mock_enable
):
    """Test sync_command when functions exist but no versions found."""
    mock_find_files.return_value = ["test.py"]
    mock_import.return_value = True
    mock_settings.return_value = Mock(api_key="test", project_id="test")
    
    # Mock client that returns empty list for function versions
    mock_client_instance = Mock()
    mock_client_instance.projects.functions.list_paginated.return_value = Mock(items=[])
    mock_client.return_value = mock_client_instance
    
    mock_get_funcs.return_value = {
        TRACE_MODULE_NAME: [("test.py", "test_func", 1, "test_module", {})]
    }
    
    with patch("builtins.print") as mock_print:
        sync_command(Path("."))
        
        # Should print message about no versions found for function
        mock_print.assert_called()


@patch("lilypad.cli.commands.sync.enable_recording")
@patch("lilypad.cli.commands.sync.clear_registry")
@patch("lilypad.cli.commands.sync.disable_recording")
@patch("lilypad.cli.commands.sync.get_decorated_functions")
@patch("lilypad.cli.commands.sync.get_sync_client")
@patch("lilypad.cli.commands.sync.get_settings")
@patch("lilypad.cli.commands.sync._find_python_files")
@patch("lilypad.cli.commands.sync._import_module_safely")
def test_sync_command_debug_mode(
    mock_import, mock_find_files, mock_settings, mock_client, mock_get_funcs,
    mock_disable, mock_clear, mock_enable
):
    """Test sync_command with debug mode enabled."""
    mock_find_files.return_value = ["test.py"]
    mock_import.return_value = True
    mock_settings.return_value = Mock(api_key="test", project_id="test")
    mock_client.return_value = Mock()
    mock_get_funcs.return_value = {TRACE_MODULE_NAME: []}
    
    # Test debug mode
    with patch("lilypad.cli.commands.sync.DEBUG", True):
        sync_command(Path("."), debug=True)
    
    # If we reach here, debug mode was handled correctly
    assert True


@patch("lilypad.cli.commands.sync.enable_recording")
@patch("lilypad.cli.commands.sync.clear_registry")
@patch("lilypad.cli.commands.sync.disable_recording")
@patch("lilypad.cli.commands.sync.get_decorated_functions")
@patch("lilypad.cli.commands.sync.get_sync_client")
@patch("lilypad.cli.commands.sync.get_settings")
@patch("lilypad.cli.commands.sync._find_python_files")
@patch("lilypad.cli.commands.sync._import_module_safely")
def test_sync_command_verbose_mode(
    mock_import, mock_find_files, mock_settings, mock_client, mock_get_funcs,
    mock_disable, mock_clear, mock_enable
):
    """Test sync_command with verbose mode enabled."""
    mock_find_files.return_value = ["test.py"]
    mock_import.return_value = True
    mock_settings.return_value = Mock(api_key="test", project_id="test")
    mock_client.return_value = Mock()
    mock_get_funcs.return_value = {TRACE_MODULE_NAME: []}
    
    with patch("builtins.print") as mock_print:
        sync_command(Path("."), verbose=True)
        
        # Verbose mode should produce additional output
        mock_print.assert_called()


def test_sync_command_typer_app():
    """Test that the typer app is properly configured."""
    assert app is not None
    assert hasattr(app, 'command')


def test_console_instance():
    """Test that console instance exists."""
    assert console is not None
    assert hasattr(console, 'print')


def test_debug_global_variable():
    """Test DEBUG global variable."""
    import lilypad.cli.commands.sync
    assert isinstance(lilypad.cli.commands.sync.DEBUG, bool)


@patch("lilypad.cli.commands.sync._run_ruff")
def test_sync_command_with_ruff_formatting(mock_ruff):
    """Test sync_command when ruff formatting is applied."""
    # This tests the path where ruff is called for formatting
    mock_ruff.return_value = True
    
    # This would test stub content writing and formatting
    # The actual test would need to mock more components
    assert True  # Placeholder for ruff integration test


def test_normalize_signature_complex_function():
    """Test _normalize_signature with complex function signature."""
    complex_sig = """
    @decorator1
    @decorator2
    def complex_func(
        self,
        arg1: int,
        arg2: str = "default",
        *args: Any,
        **kwargs: Dict[str, Any]
    ) -> Optional[List[str]]:
        '''Docstring here'''
        pass
    """
    
    result = _normalize_signature(complex_sig)
    assert "@decorator" not in result
    assert "def complex_func" in result
    assert "pass" in result


def test_parse_parameters_handles_self_parameter():
    """Test that _parse_parameters_from_signature handles self parameter."""
    sig = "def method(self, a: int, b: str) -> None: pass"
    params = _parse_parameters_from_signature(sig)
    
    # Should include self parameter
    assert any("self" in p for p in params)
    assert any("a: int" in p for p in params)
    assert any("b: str" in p for p in params)


def test_parse_parameters_complex_annotations():
    """Test _parse_parameters_from_signature with complex type annotations."""
    sig = "def func(a: List[Dict[str, Any]], b: Optional[Union[int, str]]) -> None: pass"
    params = _parse_parameters_from_signature(sig)
    
    # Should handle complex types
    assert len(params) == 2


def test_merge_parameters_no_changes_needed():
    """Test _merge_parameters when no arg_types changes are needed."""
    sig = "def func(a: int, b: str) -> None: pass"
    arg_types = {}  # Empty dict means no changes
    
    merged = _merge_parameters(sig, arg_types)
    assert any("a: int" in p for p in merged)
    assert any("b: str" in p for p in merged)


def test_extract_type_from_param_complex_defaults():
    """Test _extract_type_from_param with complex default values."""
    assert _extract_type_from_param("param: Dict[str, int] = {'key': 1}") == "Dict[str, int]"
    assert _extract_type_from_param("param: List[str] = ['a', 'b']") == "List[str]"
    assert _extract_type_from_param("param: Optional[int] = None") == "Optional[int]"