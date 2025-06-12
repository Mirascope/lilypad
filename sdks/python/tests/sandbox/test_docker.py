"""Tests for Docker sandbox runner."""

import io
import tarfile
from unittest.mock import Mock, patch
import pytest

from lilypad.sandbox.docker import DockerSandboxRunner, _DEFAULT_IMAGE
from lilypad._utils import Closure


@pytest.fixture
def mock_closure():
    """Create a mock closure for testing."""
    closure = Mock(spec=Closure)
    closure.source_code = "def test_func(): return 'hello'"
    closure.function_name = "test_func"
    closure.dependencies = []
    return closure


class TestDockerSandboxRunner:
    """Test DockerSandboxRunner class."""

    def test_init_default_values(self):
        """Test DockerSandboxRunner initialization with default values."""
        runner = DockerSandboxRunner()

        assert runner.image == _DEFAULT_IMAGE
        # Check inherited environment attribute from SandboxRunner
        assert hasattr(runner, "environment")

    def test_init_custom_values(self):
        """Test DockerSandboxRunner initialization with custom values."""
        custom_image = "python:3.10"
        custom_env = {"CUSTOM_VAR": "value"}

        runner = DockerSandboxRunner(image=custom_image, environment=custom_env)

        assert runner.image == custom_image
        assert runner.environment == custom_env

    def test_create_tar_stream_single_file(self):
        """Test _create_tar_stream with a single file."""
        files = {"test.py": "print('hello')"}

        stream = DockerSandboxRunner._create_tar_stream(files)

        assert isinstance(stream, io.BytesIO)
        assert stream.tell() == 0  # Stream should be at start

        # Verify tar content
        with tarfile.open(fileobj=stream, mode="r") as tar:
            members = tar.getnames()
            assert "test.py" in members

            file_info = tar.extractfile("test.py")
            content = file_info.read().decode("utf-8")
            assert content == "print('hello')"

    def test_create_tar_stream_multiple_files(self):
        """Test _create_tar_stream with multiple files."""
        files = {"main.py": "import helper\nprint(helper.func())", "helper.py": "def func(): return 'world'"}

        stream = DockerSandboxRunner._create_tar_stream(files)

        with tarfile.open(fileobj=stream, mode="r") as tar:
            members = tar.getnames()
            assert "main.py" in members
            assert "helper.py" in members

            main_content = tar.extractfile("main.py").read().decode("utf-8")
            helper_content = tar.extractfile("helper.py").read().decode("utf-8")

            assert main_content == "import helper\nprint(helper.func())"
            assert helper_content == "def func(): return 'world'"

    def test_create_tar_stream_unicode_content(self):
        """Test _create_tar_stream with unicode content."""
        files = {"unicode.py": "print('Hello 世界 🌍')"}

        stream = DockerSandboxRunner._create_tar_stream(files)

        with tarfile.open(fileobj=stream, mode="r") as tar:
            file_info = tar.extractfile("unicode.py")
            content = file_info.read().decode("utf-8")
            assert content == "print('Hello 世界 🌍')"

    @patch("lilypad.sandbox.docker.docker")
    def test_execute_function_success(self, mock_docker, mock_closure):
        """Test successful function execution."""
        # Setup mocks
        mock_client = Mock()
        mock_container = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.run.return_value = mock_container
        mock_container.exec_run.return_value = (0, (b'{"result": "success"}', b""))

        runner = DockerSandboxRunner()
        runner.generate_script = Mock(return_value="test script")
        from lilypad.sandbox.runner import Result

        expected_result: Result = {"result": "success"}
        runner.parse_execution_result = Mock(return_value=expected_result)

        result = runner.execute_function(mock_closure, arg1="value1")

        # Verify Docker operations
        mock_docker.from_env.assert_called_once()
        mock_client.containers.run.assert_called_once_with(
            _DEFAULT_IMAGE,
            "tail -f /dev/null",
            remove=True,
            detach=True,
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"],
            environment=runner.environment,
        )

        # Verify script generation
        runner.generate_script.assert_called_once_with(
            mock_closure,
            arg1="value1",
            custom_result=None,
            pre_actions=None,
            after_actions=None,
            extra_imports=None,
        )

        # Verify container operations
        mock_container.put_archive.assert_called_once()
        mock_container.exec_run.assert_called_once_with(
            cmd=["uv", "run", "/main.py"],
            demux=True,
        )
        mock_container.stop.assert_called_once()

        assert result == expected_result

    @patch("lilypad.sandbox.docker.docker")
    def test_execute_function_with_custom_environment(self, mock_docker, mock_closure):
        """Test function execution with custom environment."""
        custom_env = {"MY_VAR": "my_value"}
        mock_client = Mock()
        mock_container = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.run.return_value = mock_container
        mock_container.exec_run.return_value = (0, (b'{"result": "success"}', b""))

        runner = DockerSandboxRunner(environment=custom_env)
        runner.generate_script = Mock(return_value="test script")
        runner.parse_execution_result = Mock(return_value={"result": "success"})

        result = runner.execute_function(mock_closure)

        # Verify environment was passed
        mock_client.containers.run.assert_called_once_with(
            _DEFAULT_IMAGE,
            "tail -f /dev/null",
            remove=True,
            detach=True,
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"],
            environment=custom_env,
        )

    @patch("lilypad.sandbox.docker.docker")
    def test_execute_function_with_custom_image(self, mock_docker, mock_closure):
        """Test function execution with custom Docker image."""
        custom_image = "python:3.11-alpine"
        mock_client = Mock()
        mock_container = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.run.return_value = mock_container
        mock_container.exec_run.return_value = (0, (b'{"result": "success"}', b""))

        runner = DockerSandboxRunner(image=custom_image)
        runner.generate_script = Mock(return_value="test script")
        runner.parse_execution_result = Mock(return_value={"result": "success"})

        result = runner.execute_function(mock_closure)

        # Verify custom image was used
        mock_client.containers.run.assert_called_once_with(
            custom_image,
            "tail -f /dev/null",
            remove=True,
            detach=True,
            security_opt=["no-new-privileges"],
            cap_drop=["ALL"],
            environment=runner.environment,
        )

    @patch("lilypad.sandbox.docker.docker")
    def test_execute_function_with_all_options(self, mock_docker, mock_closure):
        """Test function execution with all optional parameters."""
        mock_client = Mock()
        mock_container = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.run.return_value = mock_container
        mock_container.exec_run.return_value = (0, (b'{"result": "success"}', b""))

        runner = DockerSandboxRunner()
        runner.generate_script = Mock(return_value="test script")
        runner.parse_execution_result = Mock(return_value={"result": "success"})

        custom_result = {"status": "done"}
        pre_actions = ["pip install requests"]
        after_actions = ["rm temp.txt"]
        extra_imports = ["import requests"]

        result = runner.execute_function(
            mock_closure,
            custom_result=custom_result,
            pre_actions=pre_actions,
            after_actions=after_actions,
            extra_imports=extra_imports,
            arg1="value1",
        )

        # Verify all parameters were passed to generate_script
        runner.generate_script.assert_called_once_with(
            mock_closure,
            arg1="value1",
            custom_result=custom_result,
            pre_actions=pre_actions,
            after_actions=after_actions,
            extra_imports=extra_imports,
        )

    @patch("lilypad.sandbox.docker.docker")
    def test_execute_function_container_cleanup_on_success(self, mock_docker, mock_closure):
        """Test container cleanup happens even on successful execution."""
        mock_client = Mock()
        mock_container = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.run.return_value = mock_container
        mock_container.exec_run.return_value = (0, (b'{"result": "success"}', b""))

        runner = DockerSandboxRunner()
        runner.generate_script = Mock(return_value="test script")
        runner.parse_execution_result = Mock(return_value={"result": "success"})

        result = runner.execute_function(mock_closure)

        # Verify container was stopped
        mock_container.stop.assert_called_once()

    @patch("lilypad.sandbox.docker.docker")
    def test_execute_function_container_cleanup_on_exception(self, mock_docker, mock_closure):
        """Test container cleanup happens even when exception occurs."""
        mock_client = Mock()
        mock_container = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.run.return_value = mock_container
        mock_container.exec_run.side_effect = Exception("Container error")

        runner = DockerSandboxRunner()
        runner.generate_script = Mock(return_value="test script")

        with pytest.raises(Exception, match="Container error"):
            runner.execute_function(mock_closure)

        # Verify container was still stopped despite exception
        mock_container.stop.assert_called_once()

    @patch("lilypad.sandbox.docker.docker")
    def test_execute_function_no_container_cleanup_if_no_container(self, mock_docker, mock_closure):
        """Test no container cleanup if container creation fails."""
        mock_client = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.run.side_effect = Exception("Failed to create container")

        runner = DockerSandboxRunner()
        runner.generate_script = Mock(return_value="test script")

        with pytest.raises(Exception, match="Failed to create container"):
            runner.execute_function(mock_closure)

        # No container.stop() should be called since container is None

    @patch("lilypad.sandbox.docker.docker")
    def test_execute_function_suppresses_stop_exception(self, mock_docker, mock_closure):
        """Test that exceptions during container.stop() are suppressed."""
        mock_client = Mock()
        mock_container = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.run.return_value = mock_container
        mock_container.exec_run.return_value = (0, (b'{"result": "success"}', b""))
        mock_container.stop.side_effect = Exception("Stop failed")

        runner = DockerSandboxRunner()
        runner.generate_script = Mock(return_value="test script")
        runner.parse_execution_result = Mock(return_value={"result": "success"})

        # Should not raise exception despite stop() failing
        result = runner.execute_function(mock_closure)

        assert result == {"result": "success"}
        mock_container.stop.assert_called_once()

    @patch("lilypad.sandbox.docker.docker")
    def test_execute_function_none_stdout_stderr(self, mock_docker, mock_closure):
        """Test function execution when stdout/stderr are None."""
        mock_client = Mock()
        mock_container = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.run.return_value = mock_container
        mock_container.exec_run.return_value = (0, (None, None))

        runner = DockerSandboxRunner()
        runner.generate_script = Mock(return_value="test script")
        runner.parse_execution_result = Mock(return_value={"result": "success"})

        result = runner.execute_function(mock_closure)

        # Verify parse_execution_result was called with empty bytes
        runner.parse_execution_result.assert_called_once_with(b"", b"", 0)
        assert result == {"result": "success"}

    def test_tar_stream_file_info_properties(self):
        """Test that tar file info has correct properties."""
        files = {"test.py": "print('test')"}

        stream = DockerSandboxRunner._create_tar_stream(files)

        with tarfile.open(fileobj=stream, mode="r") as tar:
            info = tar.getmember("test.py")
            assert info.name == "test.py"
            assert info.size == len(b"print('test')")
            assert info.isfile()
