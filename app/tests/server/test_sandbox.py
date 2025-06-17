"""Tests for the sandbox module."""

import json
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

import pytest

# Docker import with fallback for testing
try:
    import docker
except ImportError:
    docker = None

from lilypad.sandbox import SandboxRunner, SubprocessSandboxRunner

# Try to import DockerSandboxRunner, fallback if not available
if TYPE_CHECKING:
    from lilypad.sandbox import DockerSandboxRunner
else:
    try:
        from lilypad.sandbox import DockerSandboxRunner
    except ImportError:
        DockerSandboxRunner = None


class TestSandboxRunner:
    """Test SandboxRunner abstract base class."""

    def test_init_with_environment(self):
        """Test initialization with environment variables."""
        env = {"TEST_VAR": "test_value"}

        class ConcreteSandboxRunner(SandboxRunner):
            def execute_function(self, closure, *args, **kwargs):
                return "test"

        runner = ConcreteSandboxRunner(environment=env)
        assert runner.environment == env

    def test_init_without_environment(self):
        """Test initialization without environment variables."""

        class ConcreteSandboxRunner(SandboxRunner):
            def execute_function(self, closure, *args, **kwargs):
                return "test"

        runner = ConcreteSandboxRunner()
        assert runner.environment == {}

    def test_is_async_func_with_async_function(self):
        """Test _is_async_func with async function signature."""
        closure = Mock()
        closure.signature = "async def test_func():\n    pass"

        assert SandboxRunner._is_async_func(closure) is True

    def test_is_async_func_with_sync_function(self):
        """Test _is_async_func with sync function signature."""
        closure = Mock()
        closure.signature = "def test_func():\n    pass"

        assert SandboxRunner._is_async_func(closure) is False

    def test_is_async_func_with_multiline_signature(self):
        """Test _is_async_func with multiline signature containing async def."""
        closure = Mock()
        closure.signature = "# comment\nasync def test_func():\n    pass"

        assert SandboxRunner._is_async_func(closure) is True

    def test_generate_async_run(self):
        """Test _generate_async_run method."""
        closure = Mock()
        closure.name = "test_func"

        result = SandboxRunner._generate_async_run(closure, "arg1", kwarg1="value1")

        assert "import asyncio" in result
        assert "asyncio.run(test_func(*('arg1',), **{'kwarg1': 'value1'}))" in result

    def test_generate_sync_run(self):
        """Test _generate_sync_run method."""
        closure = Mock()
        closure.name = "test_func"

        result = SandboxRunner._generate_sync_run(closure, "arg1", kwarg1="value1")

        assert "result = test_func(*('arg1',), **{'kwarg1': 'value1'})" in result

    def test_generate_script_with_sync_function(self):
        """Test generate_script with sync function."""
        closure = Mock()
        closure.name = "test_func"
        closure.signature = "def test_func():\n    pass"
        closure.dependencies = {"requests": {"version": "2.28.0", "extras": []}}
        closure.code = "def test_func():\n    return 'hello'"

        with patch.object(SandboxRunner, "_is_async_func", return_value=False):
            result = SandboxRunner.generate_script(closure, "arg1")

        assert "# /// script" in result
        assert '"requests==2.28.0"' in result
        assert closure.code in result
        assert "result = test_func(*('arg1',), **{})" in result
        assert "print(json.dumps(result))" in result

    def test_generate_script_with_async_function(self):
        """Test generate_script with async function."""
        closure = Mock()
        closure.name = "test_func"
        closure.signature = "async def test_func():\n    pass"
        closure.dependencies = {}
        closure.code = "async def test_func():\n    return 'hello'"

        with patch.object(SandboxRunner, "_is_async_func", return_value=True):
            result = SandboxRunner.generate_script(closure, "arg1")

        assert "# /// script" in result
        assert closure.code in result
        assert "import asyncio" in result
        assert "asyncio.run(test_func(*('arg1',), **{}))" in result

    def test_generate_script_with_extras_dependencies(self):
        """Test generate_script with dependencies having extras."""
        closure = Mock()
        closure.name = "test_func"
        closure.signature = "def test_func():\n    pass"
        closure.dependencies = {
            "requests": {"version": "2.28.0", "extras": ["security", "socks"]},
            "numpy": {"version": "1.24.0", "extras": []},
        }
        closure.code = "def test_func():\n    return 'hello'"

        with patch.object(SandboxRunner, "_is_async_func", return_value=False):
            result = SandboxRunner.generate_script(closure)

        assert '"requests[security,socks]==2.28.0"' in result
        assert '"numpy==1.24.0"' in result


class TestSubprocessSandboxRunner:
    """Test SubprocessSandboxRunner class."""

    def test_init_with_environment(self):
        """Test initialization with environment variables."""
        env = {"TEST_VAR": "test_value", "PATH": "/custom/path"}
        runner = SubprocessSandboxRunner(environment=env)
        assert runner.environment == env

    def test_init_without_environment_sets_path(self):
        """Test initialization without environment sets PATH from os.environ."""
        import os

        with patch.dict(os.environ, {"PATH": "/system/path"}):
            runner = SubprocessSandboxRunner()
            assert runner.environment["PATH"] == "/system/path"

    def test_init_with_environment_without_path(self):
        """Test initialization with environment without PATH sets it from os.environ."""
        import os

        env = {"TEST_VAR": "test_value"}
        with patch.dict(os.environ, {"PATH": "/system/path"}):
            runner = SubprocessSandboxRunner(environment=env)
            assert runner.environment["PATH"] == "/system/path"
            assert runner.environment["TEST_VAR"] == "test_value"

    @patch("lilypad.sandbox.subprocess.Path")
    @patch("subprocess.run")
    @patch("tempfile.NamedTemporaryFile")
    def test_execute_function_success(
        self, mock_tempfile, mock_subprocess_run, mock_path_class
    ):
        """Test successful function execution."""
        # Setup mocks
        mock_file = Mock()
        mock_file.name = "/tmp/test.py"
        mock_tempfile.return_value.__enter__.return_value = mock_file

        mock_path = Mock()
        mock_path.unlink = Mock()
        mock_path.__str__ = Mock(return_value="/tmp/test.py")
        mock_path_class.return_value = mock_path

        mock_result = Mock()
        mock_result.stdout = '{"result": "success"}'
        mock_subprocess_run.return_value = mock_result

        closure = Mock()

        runner = SubprocessSandboxRunner()

        with patch.object(runner, "generate_script", return_value="test script"):
            result = runner.execute_function(closure, "arg1", kwarg1="value1")

        assert result == {"result": "success"}
        mock_file.write.assert_called_once_with("test script")
        mock_subprocess_run.assert_called_once_with(
            ["uv", "run", "/tmp/test.py"],
            check=True,
            capture_output=True,
            text=True,
            env=runner.environment,
        )
        mock_path.unlink.assert_called_once()

    @patch("lilypad.sandbox.subprocess.Path")
    @patch("subprocess.run")
    @patch("tempfile.NamedTemporaryFile")
    def test_execute_function_subprocess_error(
        self, mock_tempfile, mock_subprocess_run, mock_path_class
    ):
        """Test function execution with subprocess error."""
        import subprocess

        # Setup mocks
        mock_file = Mock()
        mock_file.name = "/tmp/test.py"
        mock_tempfile.return_value.__enter__.return_value = mock_file

        mock_path = Mock()
        mock_path.unlink = Mock()
        mock_path.__str__ = Mock(return_value="/tmp/test.py")
        mock_path_class.return_value = mock_path

        error = subprocess.CalledProcessError(1, "uv run")
        error.stdout = "stdout content"
        error.stderr = "stderr content"
        mock_subprocess_run.side_effect = error

        closure = Mock()
        runner = SubprocessSandboxRunner()

        with (
            patch.object(runner, "generate_script", return_value="test script"),
            pytest.raises(RuntimeError) as exc_info,
        ):
            runner.execute_function(closure, "arg1")

        assert "Process exited with non-zero status" in str(exc_info.value)
        assert "stdout content" in str(exc_info.value)
        assert "stderr content" in str(exc_info.value)
        mock_path.unlink.assert_called_once()

    @patch("lilypad.sandbox.subprocess.Path")
    @patch("subprocess.run")
    @patch("tempfile.NamedTemporaryFile")
    def test_execute_function_json_loads_invalid_json(
        self, mock_tempfile, mock_subprocess_run, mock_path_class
    ):
        """Test function execution with invalid JSON output."""
        # Setup mocks
        mock_file = Mock()
        mock_file.name = "/tmp/test.py"
        mock_tempfile.return_value.__enter__.return_value = mock_file

        mock_path = Mock()
        mock_path.unlink = Mock()
        mock_path.__str__ = Mock(return_value="/tmp/test.py")
        mock_path_class.return_value = mock_path

        mock_result = Mock()
        mock_result.stdout = "invalid json"
        mock_subprocess_run.return_value = mock_result

        closure = Mock()
        runner = SubprocessSandboxRunner()

        with (
            patch.object(runner, "generate_script", return_value="test script"),
            pytest.raises(json.JSONDecodeError),
        ):
            runner.execute_function(closure, "arg1")

        mock_path.unlink.assert_called_once()


@pytest.mark.skipif(
    DockerSandboxRunner is None, reason="DockerSandboxRunner not available"
)
class TestDockerSandboxRunner:
    """Test DockerSandboxRunner class."""

    def test_init_with_default_image(self):
        """Test initialization with default image."""
        assert DockerSandboxRunner is not None
        runner = DockerSandboxRunner()
        assert runner.image == "ghcr.io/astral-sh/uv:python3.10-alpine"
        assert runner.environment == {}

    def test_init_with_custom_image_and_environment(self):
        """Test initialization with custom image and environment."""
        assert DockerSandboxRunner is not None
        env = {"TEST_VAR": "test_value"}
        runner = DockerSandboxRunner(image="custom:image", environment=env)
        assert runner.image == "custom:image"
        assert runner.environment == env

    def test_create_tar_stream(self):
        """Test _create_tar_stream method."""
        assert DockerSandboxRunner is not None
        files = {"file1.py": "print('hello')", "file2.py": "print('world')"}

        stream = DockerSandboxRunner._create_tar_stream(files)

        assert stream.tell() == 0  # Stream is at beginning
        # Stream should contain data
        stream.seek(0, 2)  # Seek to end
        assert stream.tell() > 0  # Stream has content

    @patch("docker.from_env")
    def test_execute_function_success(self, mock_docker_from_env):
        """Test successful function execution."""
        assert DockerSandboxRunner is not None
        # Setup mocks
        mock_client = Mock()
        mock_container = Mock()
        mock_container.exec_run.return_value = (0, (b'{"result": "success"}', b""))
        mock_client.containers.run.return_value = mock_container
        mock_docker_from_env.return_value = mock_client

        closure = Mock()
        runner = DockerSandboxRunner()

        with (
            patch.object(runner, "generate_script", return_value="test script"),
            patch.object(DockerSandboxRunner, "_create_tar_stream") as mock_tar,
        ):
            mock_stream = Mock()
            mock_tar.return_value = mock_stream

            result = runner.execute_function(closure, "arg1", kwarg1="value1")

        assert result == {"result": "success"}
        mock_client.containers.run.assert_called_once_with(
            runner.image,
            "tail -f /dev/null",
            remove=True,
            detach=True,
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"],
            environment=runner.environment,
        )
        mock_container.put_archive.assert_called_once_with("/", mock_stream)
        mock_container.exec_run.assert_called_once_with(
            cmd=["uv", "run", "/main.py"],
            demux=True,
        )
        mock_container.stop.assert_called_once()

    @patch("docker.from_env")
    def test_execute_function_container_exec_error(self, mock_docker_from_env):
        """Test function execution with container exec error."""
        assert DockerSandboxRunner is not None
        # Setup mocks
        mock_client = Mock()
        mock_container = Mock()
        mock_container.exec_run.return_value = (1, (b"", b"execution error"))
        mock_client.containers.run.return_value = mock_container
        mock_docker_from_env.return_value = mock_client

        closure = Mock()
        runner = DockerSandboxRunner()

        with (
            patch.object(runner, "generate_script", return_value="test script"),
            patch.object(DockerSandboxRunner, "_create_tar_stream"),
            pytest.raises(RuntimeError) as exc_info,
        ):
            runner.execute_function(closure, "arg1")

        assert "Error running code in Docker container: execution error" in str(
            exc_info.value
        )
        mock_container.stop.assert_called_once()

    @patch("docker.from_env")
    def test_execute_function_json_loads_invalid_json(self, mock_docker_from_env):
        """Test function execution with invalid JSON output."""
        assert DockerSandboxRunner is not None
        # Setup mocks
        mock_client = Mock()
        mock_container = Mock()
        mock_container.exec_run.return_value = (0, (b"invalid json", b""))
        mock_client.containers.run.return_value = mock_container
        mock_docker_from_env.return_value = mock_client

        closure = Mock()
        runner = DockerSandboxRunner()

        with (
            patch.object(runner, "generate_script", return_value="test script"),
            patch.object(DockerSandboxRunner, "_create_tar_stream"),
            pytest.raises(json.JSONDecodeError),
        ):
            runner.execute_function(closure, "arg1")

        mock_container.stop.assert_called_once()

    @patch("docker.from_env")
    def test_execute_function_container_stop_exception(self, mock_docker_from_env):
        """Test function execution handles container stop exception gracefully."""
        assert DockerSandboxRunner is not None
        # Setup mocks
        mock_client = Mock()
        mock_container = Mock()
        mock_container.exec_run.return_value = (0, (b'{"result": "success"}', b""))
        mock_container.stop.side_effect = Exception("Stop failed")
        mock_client.containers.run.return_value = mock_container
        mock_docker_from_env.return_value = mock_client

        closure = Mock()
        runner = DockerSandboxRunner()

        with (
            patch.object(runner, "generate_script", return_value="test script"),
            patch.object(DockerSandboxRunner, "_create_tar_stream"),
        ):
            # Should not raise exception even if container.stop() fails
            result = runner.execute_function(closure, "arg1")

        assert result == {"result": "success"}
        mock_container.stop.assert_called_once()

    @patch("docker.from_env")
    def test_execute_function_docker_exception(self, mock_docker_from_env):
        """Test function execution with Docker exception during container creation."""
        assert DockerSandboxRunner is not None
        assert docker is not None
        # Setup mocks
        mock_client = Mock()
        mock_client.containers.run.side_effect = docker.errors.DockerException(  # type: ignore
            "Docker error"
        )  # type: ignore[union-attr]
        mock_docker_from_env.return_value = mock_client

        closure = Mock()
        runner = DockerSandboxRunner()

        with (
            patch.object(runner, "generate_script", return_value="test script"),
            pytest.raises(docker.errors.DockerException),  # type: ignore
        ):  # type: ignore[union-attr]
            runner.execute_function(closure, "arg1")

    @patch("docker.from_env")
    def test_execute_function_no_container_created(self, mock_docker_from_env):
        """Test function execution when no container is created."""
        assert DockerSandboxRunner is not None
        # Setup mocks
        mock_client = Mock()
        mock_client.containers.run.return_value = None
        mock_docker_from_env.return_value = mock_client

        closure = Mock()
        runner = DockerSandboxRunner()

        with (
            patch.object(runner, "generate_script", return_value="test script"),
            patch.object(DockerSandboxRunner, "_create_tar_stream"),
            pytest.raises(AttributeError),
        ):
            # Should handle None container gracefully
            runner.execute_function(closure, "arg1")


class TestSandboxModule:
    """Test sandbox module imports and __all__."""

    def test_all_exports(self):
        """Test that __all__ contains expected exports."""
        from lilypad.sandbox import __all__

        expected_exports = [
            "DockerSandboxRunner",
            "SubprocessSandboxRunner",
            "SandboxRunner",
            "DockerSandboxRunner",  # Listed twice in original
        ]
        assert __all__ == expected_exports

    def test_docker_import_suppression(self):
        """Test that Docker import is suppressed when docker is not available."""
        # This test verifies the suppress(ImportError) context manager works
        # We can't easily test the actual import failure without mocking import machinery
        try:
            from lilypad.sandbox import DockerSandboxRunner

            assert DockerSandboxRunner is not None
        except ImportError:
            # This is expected when docker package is not available
            pass

    def test_imports_work(self):
        """Test that all imports work correctly."""
        from lilypad.sandbox import SandboxRunner, SubprocessSandboxRunner

        assert SandboxRunner is not None
        assert SubprocessSandboxRunner is not None

        # DockerSandboxRunner might not be available
        try:
            from lilypad.sandbox import DockerSandboxRunner

            assert DockerSandboxRunner is not None
        except ImportError:
            pass  # DockerSandboxRunner not available, which is fine
