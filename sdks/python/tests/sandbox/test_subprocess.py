"""Test cases for the SubprocessSandboxRunner."""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock

from lilypad.sandbox.subprocess import SubprocessSandboxRunner
from lilypad._utils import Closure


def test_subprocess_runner_initialization():
    """Test SubprocessSandboxRunner initialization."""
    # Test without environment - should include PATH
    runner = SubprocessSandboxRunner()
    assert "PATH" in runner.environment
    assert runner.environment["PATH"] == os.environ["PATH"]

    # Test with custom environment
    custom_env = {"CUSTOM_VAR": "value"}
    runner = SubprocessSandboxRunner(environment=custom_env)
    assert "PATH" in runner.environment
    assert "CUSTOM_VAR" in runner.environment
    assert runner.environment["CUSTOM_VAR"] == "value"

    # Test with PATH already in environment
    env_with_path = {"PATH": "/custom/path"}
    runner = SubprocessSandboxRunner(environment=env_with_path)
    assert runner.environment["PATH"] == "/custom/path"


@patch("pathlib.Path.unlink")
@patch("subprocess.run")
@patch("tempfile.NamedTemporaryFile")
def test_execute_function_success(mock_tempfile, mock_run, mock_unlink):
    """Test successful function execution."""
    # Setup mocks
    mock_file = MagicMock()
    mock_file.name = "/tmp/test_script.py"
    mock_tempfile.return_value.__enter__.return_value = mock_file

    mock_result = MagicMock()
    mock_result.stdout = b'{"result": 42}'
    mock_result.stderr = b""
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    # Create closure
    closure = Mock(spec=Closure)
    closure.name = "test_func"
    closure.signature = "def test_func(x): return x * 2"
    closure.code = "def test_func(x): return x * 2"
    closure.dependencies = {}

    # Execute
    runner = SubprocessSandboxRunner()
    result = runner.execute_function(closure, 21)

    # Verify
    assert result == {"result": 42}
    mock_tempfile.assert_called_once_with(mode="w", suffix=".py", delete=False)
    mock_run.assert_called_once()
    mock_unlink.assert_called_once()

    # Check subprocess call
    call_args = mock_run.call_args
    assert call_args[0][0] == ["uv", "run", "--no-project", "/tmp/test_script.py"]
    assert call_args[1]["capture_output"] is True
    assert call_args[1]["text"] is False
    assert "env" in call_args[1]


@patch("pathlib.Path.unlink")
@patch("subprocess.run")
@patch("tempfile.NamedTemporaryFile")
def test_execute_function_with_custom_params(mock_tempfile, mock_run, mock_unlink):
    """Test execute_function with custom parameters."""
    # Setup mocks
    mock_file = MagicMock()
    mock_file.name = "/tmp/test_script.py"
    mock_tempfile.return_value.__enter__.return_value = mock_file

    mock_result = MagicMock()
    mock_result.stdout = b'{"output": "test", "status": "success"}'
    mock_result.stderr = b""
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    # Create closure
    closure = Mock(spec=Closure)
    closure.name = "process"
    closure.signature = "def process(): pass"
    closure.code = "def process(): return 'test'"
    closure.dependencies = {}

    # Execute with custom parameters
    runner = SubprocessSandboxRunner()
    result = runner.execute_function(
        closure,
        custom_result={"output": "result", "status": "'success'"},
        pre_actions=["import sys"],
        after_actions=["print('done')"],
        extra_imports=["import os"],
    )

    # Verify custom result format
    assert result == {"output": "test", "status": "success"}

    # Verify script was written with custom content
    written_script = mock_file.write.call_args[0][0]
    assert "import sys" in written_script
    assert "import os" in written_script
    assert "print('done')" in written_script


@patch("pathlib.Path.unlink")
@patch("subprocess.run")
@patch("tempfile.NamedTemporaryFile")
def test_execute_function_error_handling(mock_tempfile, mock_run, mock_unlink):
    """Test error handling in execute_function."""
    # Setup mocks for dependency error
    mock_file = MagicMock()
    mock_file.name = "/tmp/test_script.py"
    mock_tempfile.return_value.__enter__.return_value = mock_file

    error_output = {
        "error_type": "ImportError",
        "error_message": "No module named 'pandas'",
        "is_dependency_error": True,
        "module_name": "pandas",
    }

    import json

    mock_result = MagicMock()
    mock_result.stdout = json.dumps(error_output).encode()
    mock_result.stderr = b"Import error"
    mock_result.returncode = 1
    mock_run.return_value = mock_result

    # Create closure
    closure = Mock(spec=Closure)
    closure.name = "analyze"
    closure.signature = "def analyze(): pass"
    closure.code = "import pandas\ndef analyze(): return pandas.DataFrame()"
    closure.dependencies = {"pandas": {"version": "1.3.0", "extras": []}}

    # Execute and expect DependencyError
    runner = SubprocessSandboxRunner()
    from lilypad.sandbox.runner import DependencyError

    with pytest.raises(DependencyError) as exc_info:
        runner.execute_function(closure)

    assert exc_info.value.module_name == "pandas"


@patch("pathlib.Path.unlink")
@patch("subprocess.run")
@patch("tempfile.NamedTemporaryFile")
def test_execute_function_cleanup(mock_tempfile, mock_run, mock_unlink):
    """Test that temporary files are cleaned up."""
    # Setup mocks
    mock_file = MagicMock()
    mock_file.name = "/tmp/test_cleanup.py"
    mock_tempfile.return_value.__enter__.return_value = mock_file

    mock_result = MagicMock()
    mock_result.stdout = b'{"result": "ok"}'
    mock_result.stderr = b""
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    # Create closure
    closure = Mock(spec=Closure)
    closure.name = "func"
    closure.signature = "def func(): pass"
    closure.code = "def func(): return 'ok'"
    closure.dependencies = {}

    # Execute
    runner = SubprocessSandboxRunner()
    runner.execute_function(closure)

    # Verify cleanup was called
    mock_unlink.assert_called_once()


@patch("pathlib.Path.unlink")
@patch("subprocess.run")
@patch("tempfile.NamedTemporaryFile")
def test_execute_function_with_args_kwargs(mock_tempfile, mock_run, mock_unlink):
    """Test execute_function with args and kwargs."""
    # Setup mocks
    mock_file = MagicMock()
    mock_file.name = "/tmp/test_script.py"
    mock_tempfile.return_value.__enter__.return_value = mock_file

    mock_result = MagicMock()
    mock_result.stdout = b'{"result": 30}'
    mock_result.stderr = b""
    mock_result.returncode = 0
    mock_run.return_value = mock_result

    # Create closure
    closure = Mock(spec=Closure)
    closure.name = "calculate"
    closure.signature = "def calculate(a, b, operation='add'): pass"
    closure.code = "def calculate(a, b, operation='add'): return a + b if operation == 'add' else a * b"
    closure.dependencies = {}

    # Execute with args and kwargs
    runner = SubprocessSandboxRunner()
    result = runner.execute_function(closure, 10, 20, operation="add")

    # Verify
    assert result == {"result": 30}

    # Check that the script contains the correct function call
    written_script = mock_file.write.call_args[0][0]
    assert "calculate(*(10, 20), **{'operation': 'add'})" in written_script
