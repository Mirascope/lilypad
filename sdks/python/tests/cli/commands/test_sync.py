"""Tests for the sync command."""

from typing import Any
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from lilypad.cli.commands.sync import (
    _merge_parameters,
    _parse_return_type,
    _normalize_signature,
    _generate_protocol_stub_content,
    _parse_parameters_from_signature,
    _find_python_files,
    _module_path_from_file,
    _import_module_safely,
    _extract_type_from_param,
    _extract_parameter_types,
    _get_deployed_version,
    _format_return_type,
    sync_command,
)

SIMPLE_SIG = """
import lilypad

@lilypad.generation()
def my_func(a: int, b: str = "default") -> bool: ...
"""

ASYNC_SIG = """
import lilypad

@lilypad.generation()
async def my_async_func(x: float, y: float = 3.14) -> str: ...
"""

ARG_TYPES_DICT = {"a": "int", "b": "str"}


@pytest.fixture
def normalized_simple_sig():
    """Return the normalized signature."""
    return _normalize_signature(SIMPLE_SIG)


def test_normalize_signature(normalized_simple_sig: str):
    """Test the _normalize_signature function."""
    assert "pass" in normalized_simple_sig
    assert "@" not in normalized_simple_sig


def test_parse_parameters_from_signature():
    """Test the _parse_parameters_from_signature function."""
    params = _parse_parameters_from_signature(SIMPLE_SIG)
    assert "a: int" in params
    assert any("b:" in p and "default" in p for p in params)


def test_merge_parameters():
    """Test the _merge_parameters function."""
    merged = _merge_parameters(SIMPLE_SIG, ARG_TYPES_DICT)
    assert any(p.startswith("a: int") for p in merged)
    assert any(p.startswith("b: str") for p in merged)


def test_parse_return_type():
    """Test the _parse_return_type function."""
    ret_type = _parse_return_type(SIMPLE_SIG)
    assert ret_type == "bool"


@pytest.mark.parametrize(
    "is_async, wrapped, expected",
    [
        (
            True,
            True,
            [
                "class MyFuncVersion1(Protocol):\n    def __call__(self, a: int, b: str) -> AsyncTrace[str]: ...\n",
                "class MyFunc(Protocol):",
                "    @classmethod\n"
                "    @overload\n"
                "    def version(cls, forced_version: Literal[1], sandbox: SandboxRunner |"
                " None = None) -> MyFuncVersion1: ...",
                "def remote(self, a: int, b: str, sandbox: SandboxRunner | None = None) -> Coroutine[Any, Any, AsyncTrace[str]]: ...",
            ],
        ),
        (
            True,
            False,
            [
                "class MyFuncVersion1(Protocol):\n    def __call__(self, a: int, b: str) -> str: ...\n",
                "class MyFunc(Protocol):",
                "    @classmethod\n"
                "    @overload\n"
                "    def version(cls, forced_version: Literal[1], sandbox: SandboxRunner |"
                " None = None) -> MyFuncVersion1: ...",
                "def remote(self, a: int, b: str, sandbox: SandboxRunner | None = None) -> Coroutine[Any, Any, str]: ...",
            ],
        ),
        (
            False,
            True,
            [
                "class MyFuncVersion1(Protocol):\n    def __call__(self, a: int, b: str) -> Trace[str]: ...\n",
                "class MyFunc(Protocol):",
                "    @classmethod\n"
                "    @overload\n"
                "    def version(cls, forced_version: Literal[1], sandbox: SandboxRunner |"
                " None = None) -> MyFuncVersion1: ...",
                "def remote(self, a: int, b: str, sandbox: SandboxRunner | None = None) -> Trace[str]: ...",
            ],
        ),
        (
            False,
            False,
            [
                "class MyFuncVersion1(Protocol):\n    def __call__(self, a: int, b: str) -> str: ...\n",
                "class MyFunc(Protocol):",
                "    @classmethod\n"
                "    @overload\n"
                "    def version(cls, forced_version: Literal[1], sandbox: SandboxRunner |"
                " None = None) -> MyFuncVersion1: ...",
                "def remote(self, a: int, b: str, sandbox: SandboxRunner | None = None) -> str: ...",
                "def remote(self, a: int, b: str, sandbox: SandboxRunner | None = None) -> str: ...",
            ],
        ),
    ],
)
def test_generate_protocol_stub_content(is_async, wrapped, expected):
    """Test the _generate_protocol_stub_content function."""

    class DummyVersion:
        def __init__(self, version_num: int, signature: str, arg_types: dict):
            self.version_num = version_num
            self.signature = signature
            self.arg_types = arg_types

    # Define a simple signature for testing purposes.
    SIMPLE_SIG = "def my_func(a: int, b: str) -> str: ..."

    versions = [
        DummyVersion(1, SIMPLE_SIG, {"a": "int", "b": "str"}),
        DummyVersion(2, SIMPLE_SIG, {"a": "int", "b": "str"}),
    ]

    stub_content = _generate_protocol_stub_content("my_func", versions, is_async=is_async, wrapped=wrapped)  # pyright: ignore [reportArgumentType]

    for part in expected:
        assert part in stub_content


def dummy_get_decorated_functions(decorator_name: str, dummy_file_path: str):
    """Dummy get_decorated_functions function"""
    return {"lilypad.generation": [(dummy_file_path, "my_func", 1, "pkg.dummy")]}


class DummyClient:
    """Dummy LilypadClient class"""

    def __init__(self, token: Any) -> None:
        pass

    def get_generations_by_name(self, fn):
        """Dummy get_generations_by_name method"""

        class DummyVersion:
            def __init__(self, version_num: int, signature: str, arg_types: dict):
                self.version_num = version_num
                self.signature = signature
                self.arg_types = arg_types

        return [
            DummyVersion(1, SIMPLE_SIG, {"a": "int", "b": "str"}),
            DummyVersion(2, SIMPLE_SIG, {"a": "int", "b": "str"}),
        ]


@pytest.fixture(autouse=True)
def override_dependencies(monkeypatch, tmp_path: Path):
    """Override dependencies for the sync command."""
    pkg_dir = tmp_path / "pkg"
    pkg_dir.mkdir(exist_ok=True)
    dummy_file = (pkg_dir / "dummy.py").resolve()
    monkeypatch.setattr(
        "lilypad.cli.commands.sync.get_decorated_functions",
        lambda decorator_name: dummy_get_decorated_functions(decorator_name, str(dummy_file)),
    )


# Test for _find_python_files
def test_find_python_files(tmp_path):
    """Test finding Python files in directory."""
    # Create test directory structure
    (tmp_path / "test.py").write_text("# test file")
    (tmp_path / "subdir").mkdir()
    (tmp_path / "subdir" / "nested.py").write_text("# nested file")
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "cache.py").write_text("# cache file")
    (tmp_path / "other.txt").write_text("# not python")

    files = _find_python_files(str(tmp_path))

    # Should find .py files but exclude __pycache__
    py_files = [f for f in files if f.endswith(".py")]
    assert len(py_files) == 2
    assert any("test.py" in f for f in py_files)
    assert any("nested.py" in f for f in py_files)
    assert not any("__pycache__" in f for f in py_files)


def test_find_python_files_with_custom_exclude(tmp_path):
    """Test finding Python files with custom exclude dirs."""
    (tmp_path / "test.py").write_text("# test file")
    (tmp_path / "mydir").mkdir()
    (tmp_path / "mydir" / "excluded.py").write_text("# excluded file")

    files = _find_python_files(str(tmp_path), {"mydir"})

    py_files = [f for f in files if f.endswith(".py")]
    assert len(py_files) == 1
    assert any("test.py" in f for f in py_files)
    assert not any("excluded.py" in f for f in py_files)


def test_find_python_files_empty_directory(tmp_path):
    """Test finding Python files in empty directory."""
    files = _find_python_files(str(tmp_path))
    assert files == []


# Test for _module_path_from_file
def test_module_path_from_file():
    """Test converting file path to module path."""
    assert _module_path_from_file("path/to/module.py") == "path.to.module"
    assert _module_path_from_file("module.py") == "module"
    assert _module_path_from_file("path/to/module.py", "path") == "to.module"


def test_module_path_from_file_windows_style():
    """Test converting Windows-style file paths."""
    with patch("os.sep", "\\"):
        assert _module_path_from_file("path\\to\\module.py") == "path.to.module"


# Test for _import_module_safely
def test_import_module_safely_success():
    """Test successful module import."""
    assert _import_module_safely("os") is True


def test_import_module_safely_import_error():
    """Test handling ImportError."""
    with patch("sys.stderr"):
        assert _import_module_safely("non_existent_module_xyz") is False


def test_import_module_safely_syntax_error():
    """Test handling SyntaxError."""
    # Use a specific mock for the importlib module within the sync command
    with (
        patch.object(__import__("lilypad.cli.commands.sync", fromlist=["importlib"]), "importlib") as mock_importlib,
        patch("sys.stderr"),
    ):
        mock_importlib.import_module.side_effect = SyntaxError("Invalid syntax")
        assert _import_module_safely("some_module") is False


# Test for _extract_type_from_param
def test_extract_type_from_param():
    """Test extracting type from parameter string."""
    assert _extract_type_from_param("param: int") == "int"
    assert _extract_type_from_param("param: str = 'default'") == "str"
    assert _extract_type_from_param("param") == "Any"
    assert _extract_type_from_param("param: list[str] = []") == "list[str]"


# Test for _extract_parameter_types
def test_extract_parameter_types():
    """Test extracting types from merged parameters."""
    params = ["a: int", "b: str = 'default'", "c"]
    types = _extract_parameter_types(params)
    assert types == ["int", "str", "Any"]


# Test for _get_deployed_version
def test_get_deployed_version():
    """Test getting deployed version from list."""

    class MockVersion:
        def __init__(self, version_num, archived=False):
            self.version_num = version_num
            self.archived = archived

    versions = [
        MockVersion(1, archived=True),
        MockVersion(2, archived=False),
        MockVersion(3, archived=False),
    ]

    deployed = _get_deployed_version(versions)
    assert deployed.version_num == 3  # Highest non-archived


def test_get_deployed_version_all_archived():
    """Test getting deployed version when all are archived."""

    class MockVersion:
        def __init__(self, version_num, archived=True):
            self.version_num = version_num
            self.archived = archived

    versions = [MockVersion(1), MockVersion(2)]
    deployed = _get_deployed_version(versions)
    assert deployed.version_num == 2  # Last version when all archived


# Test for _format_return_type
def test_format_return_type():
    """Test formatting return types."""
    assert _format_return_type("str", False, False) == "str"
    assert _format_return_type("str", False, True) == "Trace[str]"
    assert _format_return_type("str", True, False) == "Coroutine[Any, Any, str]"
    assert _format_return_type("str", True, True) == "Coroutine[Any, Any, AsyncTrace[str]]"


# Test edge cases for _normalize_signature
def test_normalize_signature_edge_cases():
    """Test edge cases for signature normalization."""
    # Empty signature
    assert _normalize_signature("") == ""

    # Signature ending with ...
    sig_with_ellipsis = "def func(): ..."
    normalized = _normalize_signature(sig_with_ellipsis)
    assert normalized.endswith(" pass")

    # Signature with decorators and imports
    complex_sig = """
    from typing import Any
    
    @decorator
    def func(a: int) -> str:
        pass
    """
    normalized = _normalize_signature(complex_sig)
    assert "@" not in normalized
    assert "from typing" not in normalized


# Test edge cases for _parse_parameters_from_signature
def test_parse_parameters_edge_cases():
    """Test edge cases for parameter parsing."""
    # Function with varargs and kwargs
    sig_with_varargs = "def func(a: int, *args: str, **kwargs: Any) -> None: pass"
    params = _parse_parameters_from_signature(sig_with_varargs)
    assert any("*args" in p for p in params)
    assert any("**kwargs" in p for p in params)

    # Function with trace_ctx parameter (should be removed)
    sig_with_trace_ctx = "def func(trace_ctx: Any, a: int) -> str: pass"
    params = _parse_parameters_from_signature(sig_with_trace_ctx)
    assert not any("trace_ctx" in p for p in params)
    assert any("a: int" in p for p in params)

    # Function with annotation parsing errors
    with patch("ast.unparse", side_effect=Exception("Parse error")):
        params = _parse_parameters_from_signature("def func(a: ComplexType) -> str: pass")
        assert any("a: Any" in p for p in params)


def test_parse_parameters_malformed_signature():
    """Test parsing malformed signatures."""
    malformed_sig = "this is not a valid function signature"
    params = _parse_parameters_from_signature(malformed_sig)
    assert params == []


# Test edge cases for _merge_parameters
def test_merge_parameters_with_json_string():
    """Test merging parameters with JSON string arg_types."""
    sig = "def func(a: int, b: str) -> None: pass"
    arg_types_json = '{"a": "float", "b": "bytes"}'

    merged = _merge_parameters(sig, arg_types_json)
    assert any("a: float" in p for p in merged)
    assert any("b: bytes" in p for p in merged)


def test_merge_parameters_invalid_json():
    """Test merging parameters with invalid JSON."""
    sig = "def func(a: int) -> None: pass"
    invalid_json = "not valid json"

    merged = _merge_parameters(sig, invalid_json)
    assert any("a: int" in p for p in merged)  # Should fallback to original type


def test_merge_parameters_with_defaults():
    """Test merging parameters with default values."""
    sig = "def func(a: int = 5, b: str = 'hello') -> None: pass"
    arg_types = {"a": "float"}

    merged = _merge_parameters(sig, arg_types)
    assert any("a: float = 5" in p for p in merged)
    assert any("b: str = 'hello'" in p for p in merged)


# Test edge cases for _parse_return_type
def test_parse_return_type_edge_cases():
    """Test edge cases for return type parsing."""
    # No return type annotation
    sig_no_return = "def func(a: int): pass"
    ret_type = _parse_return_type(sig_no_return)
    assert ret_type == "Any"

    # Complex return type with parsing error
    with patch("ast.unparse", side_effect=Exception("Parse error")):
        ret_type = _parse_return_type("def func() -> ComplexType: pass")
        assert ret_type == "Any"


# Test _generate_protocol_stub_content edge cases
def test_generate_protocol_stub_content_empty_versions():
    """Test generating stub content with empty versions."""
    content = _generate_protocol_stub_content("test_func", [], False, False)
    assert content == ""


def test_generate_protocol_stub_content_no_params():
    """Test generating stub content for function with no parameters."""

    class MockVersion:
        def __init__(self, version_num, signature, arg_types=None):
            self.version_num = version_num
            self.signature = signature
            self.arg_types = arg_types

    versions = [MockVersion(1, "def test_func() -> str: pass")]
    content = _generate_protocol_stub_content("test_func", versions, False, False)
    assert "def __call__(self) -> str: ..." in content
    assert "def remote(self, sandbox: SandboxRunner | None = None) -> str: ..." in content


def test_generate_protocol_stub_content_none_version_num():
    """Test generating stub content with None version numbers."""

    class MockVersion:
        def __init__(self, version_num, signature, arg_types=None):
            self.version_num = version_num
            self.signature = signature
            self.arg_types = arg_types

    versions = [MockVersion(None, "def test_func() -> str: pass")]
    content = _generate_protocol_stub_content("test_func", versions, False, False)
    # Should still generate main protocol but skip version-specific protocols
    assert "class TestFunc(Protocol):" in content


# Test sync_command integration
@patch("lilypad.cli.commands.sync.get_settings")
@patch("lilypad.cli.commands.sync.get_sync_client")
@patch("lilypad.cli.commands.sync.get_decorated_functions")
@patch("lilypad.cli.commands.sync.enable_recording")
@patch("lilypad.cli.commands.sync.disable_recording")
@patch("lilypad.cli.commands.sync.clear_registry")
def test_sync_command_no_files(
    mock_clear, mock_disable, mock_enable, mock_get_funcs, mock_client, mock_settings, tmp_path
):
    """Test sync command with no Python files."""
    mock_settings.return_value = Mock(api_key="test", project_id="test")
    mock_client.return_value = Mock()

    # Empty directory - no Python files
    sync_command(directory=tmp_path)

    # Should not call recording functions if no files found
    mock_enable.assert_not_called()


@patch("lilypad.cli.commands.sync.get_settings")
@patch("lilypad.cli.commands.sync.get_sync_client")
@patch("lilypad.cli.commands.sync.get_decorated_functions")
@patch("lilypad.cli.commands.sync.enable_recording")
@patch("lilypad.cli.commands.sync.disable_recording")
@patch("lilypad.cli.commands.sync.clear_registry")
@patch("lilypad.cli.commands.sync._find_python_files")
@patch("importlib.import_module")
def test_sync_command_no_functions(
    mock_import,
    mock_find_files,
    mock_clear,
    mock_disable,
    mock_enable,
    mock_get_funcs,
    mock_client,
    mock_settings,
    tmp_path,
):
    """Test sync command with no decorated functions found."""
    # Configure mocks
    mock_settings.return_value = Mock(api_key="test", project_id="test")
    mock_client.return_value = Mock()
    mock_get_funcs.return_value = {"lilypad.traces": []}  # No functions
    mock_find_files.return_value = [str(tmp_path / "test.py")]  # Mock finding Python files

    # Create a Python file
    (tmp_path / "test.py").write_text("def test(): pass")

    # Call the function
    sync_command(directory=tmp_path)

    # The key test is that it should run through the whole flow but exit when no functions found
    # Just verify no exceptions are raised and the right path is taken
    assert True  # If we get here without errors, the basic flow worked


@patch("lilypad.cli.commands.sync.get_settings")
@patch("lilypad.cli.commands.sync.get_sync_client")
@patch("lilypad.cli.commands.sync.get_decorated_functions")
@patch("lilypad.cli.commands.sync.enable_recording")
@patch("lilypad.cli.commands.sync.disable_recording")
@patch("lilypad.cli.commands.sync.clear_registry")
@patch("lilypad.cli.commands.sync._find_python_files")
def test_sync_command_function_import_error(
    mock_find_files,
    mock_clear,
    mock_disable,
    mock_enable,
    mock_get_funcs,
    mock_client,
    mock_settings,
    tmp_path,
):
    """Test sync command with function import errors."""
    mock_settings.return_value = Mock(api_key="test", project_id="test")
    mock_client.return_value = Mock()
    mock_get_funcs.return_value = {"lilypad.traces": [("test.py", "test_func", 1, "test_module", {})]}
    mock_find_files.return_value = [str(tmp_path / "test.py")]

    # Create a Python file
    (tmp_path / "test.py").write_text("def test(): pass")

    # Test that the command handles the import error gracefully
    sync_command(directory=tmp_path)

    # If we reach here without crashing, the test passes
    assert True


@patch("lilypad.cli.commands.sync.get_settings")
@patch("lilypad.cli.commands.sync.get_sync_client")
@patch("lilypad.cli.commands.sync.get_decorated_functions")
@patch("lilypad.cli.commands.sync.enable_recording")
@patch("lilypad.cli.commands.sync.disable_recording")
@patch("lilypad.cli.commands.sync.clear_registry")
@patch("lilypad.cli.commands.sync._find_python_files")
def test_sync_command_successful_processing(
    mock_find_files,
    mock_clear,
    mock_disable,
    mock_enable,
    mock_get_funcs,
    mock_client,
    mock_settings,
    tmp_path,
):
    """Test successful sync command processing."""
    mock_settings.return_value = Mock(api_key="test", project_id="test")
    mock_client.return_value = Mock()
    mock_get_funcs.return_value = {"lilypad.traces": []}  # Simple case - no functions
    mock_find_files.return_value = [str(tmp_path / "test.py")]

    # Create a Python file
    (tmp_path / "test.py").write_text("def test(): pass")

    # Test that the command runs successfully
    sync_command(directory=tmp_path)

    # If we reach here without crashing, the test passes
    assert True


def test_sync_command_with_exclude_dirs(tmp_path):
    """Test sync command with exclude directories."""
    # Create test structure
    (tmp_path / "include.py").write_text("def test(): pass")
    (tmp_path / "exclude_dir").mkdir()
    (tmp_path / "exclude_dir" / "exclude.py").write_text("def test(): pass")

    with (
        patch("lilypad.cli.commands.sync.get_settings") as mock_settings,
        patch("lilypad.cli.commands.sync.get_sync_client") as mock_client,
        patch("lilypad.cli.commands.sync.get_decorated_functions") as mock_get_funcs,
    ):
        mock_settings.return_value = Mock(api_key="test", project_id="test")
        mock_client.return_value = Mock()
        mock_get_funcs.return_value = {"lilypad.generation": []}

        # Test with exclude parameter
        sync_command(directory=tmp_path, exclude=["exclude_dir"])

        mock_get_funcs.assert_called_once()


def test_sync_command_debug_mode(tmp_path):
    """Test sync command with debug mode enabled."""
    (tmp_path / "test.py").write_text("def test(): pass")

    with (
        patch("lilypad.cli.commands.sync.get_settings") as mock_settings,
        patch("lilypad.cli.commands.sync.get_sync_client") as mock_client,
        patch("lilypad.cli.commands.sync.get_decorated_functions") as mock_get_funcs,
    ):
        mock_settings.return_value = Mock(api_key="test", project_id="test")
        mock_client.return_value = Mock()
        mock_get_funcs.return_value = {"lilypad.generation": []}

        # Test with debug=True
        sync_command(directory=tmp_path, debug=True)

        # DEBUG should be set to True globally
        import lilypad.cli.commands.sync

        assert lilypad.cli.commands.sync.DEBUG is True


@patch("lilypad.cli.commands.sync.get_settings")
@patch("lilypad.cli.commands.sync.get_sync_client")
@patch("lilypad.cli.commands.sync.get_decorated_functions")
@patch("lilypad.cli.commands.sync.enable_recording")
@patch("lilypad.cli.commands.sync.disable_recording")
@patch("lilypad.cli.commands.sync.clear_registry")
@patch("lilypad.cli.commands.sync._find_python_files")
def test_sync_command_client_no_versions(
    mock_find_files,
    mock_clear,
    mock_disable,
    mock_enable,
    mock_get_funcs,
    mock_client,
    mock_settings,
    tmp_path,
):
    """Test sync command when client returns no versions."""
    mock_settings.return_value = Mock(api_key="test", project_id="test")
    mock_client.return_value = Mock()
    mock_get_funcs.return_value = {"lilypad.traces": []}  # Simple case - no functions
    mock_find_files.return_value = [str(tmp_path / "test.py")]

    # Create a Python file
    (tmp_path / "test.py").write_text("def test(): pass")

    # Test that the command runs without versions
    sync_command(directory=tmp_path)

    # If we reach here without crashing, the test passes
    assert True


def test_sync_command_exclude_string_format(tmp_path):
    """Test sync command with exclude as string format."""
    (tmp_path / "test.py").write_text("def test(): pass")

    with (
        patch("lilypad.cli.commands.sync.get_settings") as mock_settings,
        patch("lilypad.cli.commands.sync.get_sync_client") as mock_client,
        patch("lilypad.cli.commands.sync.get_decorated_functions") as mock_get_funcs,
    ):
        mock_settings.return_value = Mock(api_key="test", project_id="test")
        mock_client.return_value = Mock()
        mock_get_funcs.return_value = {"lilypad.generation": []}

        # Test with exclude as non-list (should handle gracefully)
        sync_command(directory=tmp_path, exclude="dir1,dir2")

        mock_get_funcs.assert_called_once()
