"""Test cases for the SandboxRunner abstract base class."""

import pytest
import orjson
from unittest.mock import Mock

from lilypad.sandbox.runner import SandboxRunner, Result, DependencyError
from lilypad._utils import Closure


class MockSandboxRunner(SandboxRunner):
    """Concrete implementation of SandboxRunner for testing."""

    def execute_function(
        self,
        closure: Closure,
        *args,
        custom_result=None,
        pre_actions=None,
        after_actions=None,
        extra_imports=None,
        **kwargs,
    ) -> Result:
        """Mock implementation of execute_function."""
        return {"result": "test_result"}


def test_dependency_error():
    """Test DependencyError exception."""
    # Test basic instantiation
    error = DependencyError("Missing package")
    assert str(error) == "Dependency error: Missing package"
    assert error.message == "Missing package"
    assert error.module_name is None
    assert error.error_class is None

    # Test with all parameters
    error = DependencyError("Package not found", module_name="numpy", error_class="ImportError")
    assert error.message == "Package not found"
    assert error.module_name == "numpy"
    assert error.error_class == "ImportError"


def test_sandbox_runner_initialization():
    """Test SandboxRunner initialization."""
    # Test without environment
    runner = MockSandboxRunner()
    assert runner.environment == {}

    # Test with environment
    env = {"PATH": "/usr/bin", "PYTHONPATH": "/usr/lib"}
    runner = MockSandboxRunner(environment=env)
    assert runner.environment == env


def test_is_async_func():
    """Test _is_async_func method."""
    # Create mock closures
    async_closure = Mock(spec=Closure)
    async_closure.signature = "async def my_func():\n    pass"

    sync_closure = Mock(spec=Closure)
    sync_closure.signature = "def my_func():\n    pass"

    # Test async function
    assert SandboxRunner._is_async_func(async_closure) is True

    # Test sync function
    assert SandboxRunner._is_async_func(sync_closure) is False

    # Test multiline signature
    multiline_async = Mock(spec=Closure)
    multiline_async.signature = """
    async def complex_func(
        param1,
        param2
    ):
        pass
    """
    assert SandboxRunner._is_async_func(multiline_async) is True


def test_parse_execution_result_success():
    """Test parse_execution_result with successful execution."""
    # Test successful execution
    result_data = {"result": "success", "data": 42}
    stdout = orjson.dumps(result_data)
    stderr = b""
    returncode = 0

    result = SandboxRunner.parse_execution_result(stdout, stderr, returncode)
    assert result == result_data


def test_parse_execution_result_dependency_error():
    """Test parse_execution_result with dependency errors."""
    # Test ImportError
    error_data = {
        "error_type": "ImportError",
        "error_message": "No module named 'numpy'",
        "is_dependency_error": True,
        "module_name": "numpy",
    }
    stdout = orjson.dumps(error_data)
    stderr = b""
    returncode = 1

    with pytest.raises(DependencyError) as exc_info:
        SandboxRunner.parse_execution_result(stdout, stderr, returncode)

    assert exc_info.value.message == "No module named 'numpy'"
    assert exc_info.value.module_name == "numpy"
    assert exc_info.value.error_class == "ImportError"

    # Test ModuleNotFoundError
    error_data["error_type"] = "ModuleNotFoundError"
    stdout = orjson.dumps(error_data)

    with pytest.raises(DependencyError):
        SandboxRunner.parse_execution_result(stdout, stderr, returncode)


def test_parse_execution_result_runtime_error():
    """Test parse_execution_result with runtime errors."""
    # Test non-JSON output with error
    stdout = b"Invalid JSON output"
    stderr = b"Error occurred"
    returncode = 1

    with pytest.raises(RuntimeError) as exc_info:
        SandboxRunner.parse_execution_result(stdout, stderr, returncode)

    assert "Process exited with non-zero status" in str(exc_info.value)
    assert "Invalid JSON output" in str(exc_info.value)
    assert "Error occurred" in str(exc_info.value)


def test_parse_execution_result_json_decode_error_then_success():
    """Test parse_execution_result when first JSON parse fails but returncode is 0 - covers line 90."""
    import orjson

    # Create result that will succeed on second parse
    result_data = {"status": "success", "value": 100}
    stdout = orjson.dumps(result_data)
    stderr = b""
    returncode = 0

    # Mock orjson.loads to fail first time, succeed second time
    original_loads = orjson.loads
    call_count = 0

    def mock_loads(data):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # First call fails - create proper JSONDecodeError
            # orjson.JSONDecodeError needs msg, doc, and pos arguments
            raise orjson.JSONDecodeError("Mock error", data.decode(), 0)
        else:
            # Second call succeeds
            return original_loads(data)

    # Patch orjson.loads
    import lilypad.sandbox.runner

    original_runner_loads = lilypad.sandbox.runner.orjson.loads
    lilypad.sandbox.runner.orjson.loads = mock_loads

    try:
        # Call parse_execution_result
        result = SandboxRunner.parse_execution_result(stdout, stderr, returncode)

        # Should return the parsed JSON from line 90
        assert result == result_data
        assert result["status"] == "success"
        assert result["value"] == 100
        assert call_count == 2  # Verify it was called twice
    finally:
        # Restore original
        lilypad.sandbox.runner.orjson.loads = original_runner_loads


def test_generate_script_sync_function():
    """Test generate_script for synchronous functions."""
    # Create a mock closure
    closure = Mock(spec=Closure)
    closure.name = "test_func"
    closure.signature = "def test_func(x, y):\n    return x + y"
    closure.code = """
def test_func(x, y):
    return x + y
"""
    closure.dependencies = {
        "numpy": {"version": "1.21.0", "extras": []},
        "pandas": {"version": "1.3.0", "extras": ["excel", "sql"]},
    }

    script = SandboxRunner.generate_script(closure, 1, 2)

    # Verify script contains expected elements
    assert "test_func(*(1, 2), **{})" in script
    assert '"numpy==1.21.0"' in script
    assert '"pandas[excel,sql]==1.3.0"' in script
    assert "def main():" in script
    assert "result = main()" in script
    assert "print(json.dumps(result))" in script


def test_generate_script_async_function():
    """Test generate_script for asynchronous functions."""
    # Create a mock async closure
    closure = Mock(spec=Closure)
    closure.name = "async_test_func"
    closure.signature = "async def async_test_func(x):\n    return x * 2"
    closure.code = """
async def async_test_func(x):
    return x * 2
"""
    closure.dependencies = {}

    script = SandboxRunner.generate_script(closure, 5)

    # Verify async-specific elements
    assert "import asyncio" in script
    assert "async def main():" in script
    assert "await async_test_func(*(5,), **{})" in script
    assert "result = asyncio.run(main())" in script


def test_generate_script_with_custom_result():
    """Test generate_script with custom result format."""
    closure = Mock(spec=Closure)
    closure.name = "func"
    closure.signature = "def func(): pass"
    closure.code = "def func(): return 42"
    closure.dependencies = {}

    custom_result = {"output": "result", "status": "'success'"}
    script = SandboxRunner.generate_script(closure, custom_result=custom_result)

    assert '"output": (result)' in script
    assert "\"status\": ('success')" in script


def test_generate_script_with_actions():
    """Test generate_script with pre and after actions."""
    closure = Mock(spec=Closure)
    closure.name = "func"
    closure.signature = "def func(): pass"
    closure.code = "def func(): return 42"
    closure.dependencies = {}

    pre_actions = ["import os", "os.environ['TEST'] = '1'"]
    after_actions = ["print('Done')", "cleanup()"]
    extra_imports = ["import sys", "import time"]

    script = SandboxRunner.generate_script(
        closure, pre_actions=pre_actions, after_actions=after_actions, extra_imports=extra_imports
    )

    # Verify all actions are included
    assert "import os" in script
    assert "os.environ['TEST'] = '1'" in script
    assert "print('Done')" in script
    assert "cleanup()" in script
    assert "import sys" in script
    assert "import time" in script


def test_generate_script_error_handling():
    """Test that generated script includes error handling."""
    closure = Mock(spec=Closure)
    closure.name = "func"
    closure.signature = "def func(): pass"
    closure.code = "def func(): return 42"
    closure.dependencies = {}

    script = SandboxRunner.generate_script(closure)

    # Verify error handling is present
    assert "except ImportError as e:" in script
    assert "except ModuleNotFoundError as e:" in script
    assert "except Exception as e:" in script
    assert "error_type" in script
    assert "error_message" in script
    assert "traceback" in script
    assert "sys.exit(1)" in script
