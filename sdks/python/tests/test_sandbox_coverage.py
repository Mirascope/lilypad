"""Tests to cover missing lines in sandbox runner."""

import pytest
import orjson
from lilypad.sandbox.subprocess import SubprocessSandboxRunner
from lilypad.sandbox.runner import DependencyError


def test_parse_execution_result_success():
    """Test successful execution of parse_execution_result method to cover line 90."""
    runner = SubprocessSandboxRunner()

    # Create a simple result that will be JSON serialized
    expected_result = {"result": "success", "output": "test"}
    stdout_data = orjson.dumps(expected_result)

    # Test successful parse (should hit line 90 when returncode is 0 and parse succeeds)
    result = runner.parse_execution_result(stdout_data, b"", 0)

    # Verify the result matches what was "returned"
    assert result == expected_result


def test_parse_execution_result_with_dependency_error():
    """Test parse_execution_result with dependency error detection."""
    runner = SubprocessSandboxRunner()

    # Create stdout that contains dependency error info
    dependency_error = {
        "error_type": "ImportError",
        "error_message": "Module not found",
        "module_name": "missing_module",
    }
    stdout_data = orjson.dumps(dependency_error)

    # Test with dependency error (non-zero exit)
    with pytest.raises(DependencyError):
        runner.parse_execution_result(stdout_data, b"", 1)


def test_parse_execution_result_non_zero_exit():
    """Test parse_execution_result with non-zero exit code but no dependency error."""
    runner = SubprocessSandboxRunner()

    stdout_data = b"Some output"
    stderr_data = b"Some error"

    # Test non-zero exit without dependency error
    with pytest.raises(RuntimeError, match="Process exited with non-zero status"):
        runner.parse_execution_result(stdout_data, stderr_data, 1)


def test_parse_execution_result_json_decode_error_success():
    """Test parse_execution_result when first JSON parse fails but second succeeds (covers line 90)."""
    runner = SubprocessSandboxRunner()

    # Create stdout that's not valid JSON initially but will work when stripped
    # This tests the case where the first orjson.loads fails but the final one succeeds
    stdout_data = b"  \n" + orjson.dumps({"result": "test"}) + b"  \n"

    # Test successful parse after initial JSONDecodeError (should hit line 90)
    result = runner.parse_execution_result(stdout_data, b"", 0)

    assert result == {"result": "test"}


def test_parse_execution_result_json_decode_error_failure():
    """Test parse_execution_result when JSON parsing completely fails."""
    runner = SubprocessSandboxRunner()

    # Return invalid JSON in stdout
    stdout_data = b"completely invalid json output"

    # Test complete JSON decode failure (should raise error on line 90)
    with pytest.raises(orjson.JSONDecodeError):
        runner.parse_execution_result(stdout_data, b"", 0)
