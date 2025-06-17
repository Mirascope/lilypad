"""Unit tests for Docker sandbox runner."""

import io
import json
import tarfile
from unittest.mock import Mock, patch

import pytest

from lilypad._utils import Closure

try:
    from lilypad.sandbox.docker import DockerSandboxRunner
except ImportError:
    pytest.skip("Docker not available, skipping docker tests", allow_module_level=True)


@pytest.fixture
def docker_runner():
    """Create a DockerSandboxRunner instance for testing."""
    return DockerSandboxRunner()


@pytest.fixture
def docker_runner_with_env():
    """Create a DockerSandboxRunner instance with custom environment."""
    return DockerSandboxRunner(
        image="custom-image:latest",
        environment={"TEST_VAR": "test_value", "DEBUG": "true"},
    )


@pytest.fixture
def mock_closure():
    """Create a mock Closure for testing."""
    closure = Mock(spec=Closure)
    closure.code = "print('Hello World')"
    closure.dependencies = {}
    return closure


def test_docker_runner_init_default():
    """Test DockerSandboxRunner initialization with defaults."""
    runner = DockerSandboxRunner()
    assert runner.image == "ghcr.io/astral-sh/uv:python3.10-alpine"
    assert runner.environment == {}


def test_docker_runner_init_custom():
    """Test DockerSandboxRunner initialization with custom parameters."""
    environment = {"API_KEY": "test123", "DEBUG": "false"}
    runner = DockerSandboxRunner(image="custom:latest", environment=environment)
    assert runner.image == "custom:latest"
    assert runner.environment == environment


def test_create_tar_stream_single_file():
    """Test creating tar stream with single file."""
    files = {"test.py": "print('hello')"}
    stream = DockerSandboxRunner._create_tar_stream(files)

    assert isinstance(stream, io.BytesIO)
    stream.seek(0)

    # Verify tar content
    with tarfile.open(fileobj=stream, mode="r") as tar:
        members = tar.getnames()
        assert "test.py" in members

        # Extract and verify content
        test_file = tar.extractfile("test.py")
        assert test_file is not None
        content = test_file.read().decode("utf-8")
        assert content == "print('hello')"


def test_create_tar_stream_multiple_files():
    """Test creating tar stream with multiple files."""
    files = {
        "main.py": "import helper\nhelper.run()",
        "helper.py": "def run():\n    print('Running')",
        "requirements.txt": "requests==2.28.0",
    }
    stream = DockerSandboxRunner._create_tar_stream(files)

    stream.seek(0)
    with tarfile.open(fileobj=stream, mode="r") as tar:
        members = tar.getnames()
        assert len(members) == 3
        assert "main.py" in members
        assert "helper.py" in members
        assert "requirements.txt" in members


def test_create_tar_stream_empty_files():
    """Test creating tar stream with empty files dict."""
    files = {}
    stream = DockerSandboxRunner._create_tar_stream(files)

    stream.seek(0)
    with tarfile.open(fileobj=stream, mode="r") as tar:
        members = tar.getnames()
        assert len(members) == 0


def test_create_tar_stream_unicode_content():
    """Test creating tar stream with unicode content."""
    files = {"unicode.py": "print('Hello 世界! 🌍')"}
    stream = DockerSandboxRunner._create_tar_stream(files)

    stream.seek(0)
    with tarfile.open(fileobj=stream, mode="r") as tar:
        test_file = tar.extractfile("unicode.py")
        assert test_file is not None
        content = test_file.read().decode("utf-8")
        assert content == "print('Hello 世界! 🌍')"


@patch("lilypad.sandbox.docker.docker")
def test_execute_function_success(mock_docker, docker_runner, mock_closure):
    """Test successful function execution."""
    # Mock Docker client and container
    mock_client = Mock()
    mock_container = Mock()
    mock_docker.from_env.return_value = mock_client
    mock_client.containers.run.return_value = mock_container

    # Mock container execution result
    expected_result = {"status": "success", "result": 42}
    stdout = json.dumps(expected_result).encode("utf-8")
    stderr = b""
    mock_container.exec_run.return_value = (0, (stdout, stderr))

    # Mock generate_script
    with patch.object(docker_runner, "generate_script", return_value="mock_script"):
        result = docker_runner.execute_function(mock_closure, "arg1", key="value")

    # Verify result
    assert result == expected_result

    # Verify Docker client calls
    mock_docker.from_env.assert_called_once()
    mock_client.containers.run.assert_called_once_with(
        "ghcr.io/astral-sh/uv:python3.10-alpine",
        "tail -f /dev/null",
        remove=True,
        detach=True,
        security_opt=["no-new-privileges"],
        cap_drop=["ALL"],
        environment={},
    )

    # Verify container operations
    mock_container.put_archive.assert_called_once()
    mock_container.exec_run.assert_called_once_with(
        cmd=["uv", "run", "/main.py"], demux=True
    )
    mock_container.stop.assert_called_once()


@patch("lilypad.sandbox.docker.docker")
def test_execute_function_with_environment(
    mock_docker, docker_runner_with_env, mock_closure
):
    """Test function execution with custom environment."""
    # Mock Docker client and container
    mock_client = Mock()
    mock_container = Mock()
    mock_docker.from_env.return_value = mock_client
    mock_client.containers.run.return_value = mock_container

    # Mock successful execution
    stdout = json.dumps({"result": "ok"}).encode("utf-8")
    stderr = b""
    mock_container.exec_run.return_value = (0, (stdout, stderr))

    with patch.object(
        docker_runner_with_env, "generate_script", return_value="mock_script"
    ):
        docker_runner_with_env.execute_function(mock_closure)

    # Verify custom environment was passed
    mock_client.containers.run.assert_called_once_with(
        "custom-image:latest",
        "tail -f /dev/null",
        remove=True,
        detach=True,
        security_opt=["no-new-privileges"],
        cap_drop=["ALL"],
        environment={"TEST_VAR": "test_value", "DEBUG": "true"},
    )


@patch("lilypad.sandbox.docker.docker")
def test_execute_function_container_execution_error(
    mock_docker, docker_runner, mock_closure
):
    """Test handling of container execution errors."""
    # Mock Docker client and container
    mock_client = Mock()
    mock_container = Mock()
    mock_docker.from_env.return_value = mock_client
    mock_client.containers.run.return_value = mock_container

    # Mock execution error
    stdout = b""
    stderr = b"ModuleNotFoundError: No module named 'requests'"
    mock_container.exec_run.return_value = (1, (stdout, stderr))

    with (
        patch.object(docker_runner, "generate_script", return_value="mock_script"),
        pytest.raises(RuntimeError, match="Error running code in Docker container"),
    ):
        docker_runner.execute_function(mock_closure)

    # Verify container was stopped even on error
    mock_container.stop.assert_called_once()


@patch("lilypad.sandbox.docker.docker")
def test_execute_function_json_parse_error(mock_docker, docker_runner, mock_closure):
    """Test handling of JSON parsing errors from container output."""
    # Mock Docker client and container
    mock_client = Mock()
    mock_container = Mock()
    mock_docker.from_env.return_value = mock_client
    mock_client.containers.run.return_value = mock_container

    # Mock execution with invalid JSON output
    stdout = b"This is not valid JSON"
    stderr = b""
    mock_container.exec_run.return_value = (0, (stdout, stderr))

    with (
        patch.object(docker_runner, "generate_script", return_value="mock_script"),
        pytest.raises(json.JSONDecodeError),
    ):
        docker_runner.execute_function(mock_closure)


@patch("lilypad.sandbox.docker.docker")
def test_execute_function_container_creation_error(
    mock_docker, docker_runner, mock_closure
):
    """Test handling of container creation errors."""
    # Mock Docker client that raises error
    mock_client = Mock()
    mock_docker.from_env.return_value = mock_client
    mock_client.containers.run.side_effect = Exception("Failed to create container")

    with (
        patch.object(docker_runner, "generate_script", return_value="mock_script"),
        pytest.raises(Exception, match="Failed to create container"),
    ):
        docker_runner.execute_function(mock_closure)


@patch("lilypad.sandbox.docker.docker")
def test_execute_function_container_stop_error(
    mock_docker, docker_runner, mock_closure
):
    """Test that container stop errors are suppressed."""
    # Mock Docker client and container
    mock_client = Mock()
    mock_container = Mock()
    mock_docker.from_env.return_value = mock_client
    mock_client.containers.run.return_value = mock_container

    # Mock successful execution
    stdout = json.dumps({"result": "success"}).encode("utf-8")
    stderr = b""
    mock_container.exec_run.return_value = (0, (stdout, stderr))

    # Mock container.stop to raise an error
    mock_container.stop.side_effect = Exception("Stop failed")

    with patch.object(docker_runner, "generate_script", return_value="mock_script"):
        # Should not raise despite stop error
        result = docker_runner.execute_function(mock_closure)
        assert result == {"result": "success"}


@patch("lilypad.sandbox.docker.docker")
def test_execute_function_no_container_cleanup(
    mock_docker, docker_runner, mock_closure
):
    """Test cleanup when container is None."""
    # Mock Docker client
    mock_client = Mock()
    mock_docker.from_env.return_value = mock_client
    mock_client.containers.run.return_value = None  # Simulate no container created

    with (
        patch.object(docker_runner, "generate_script", return_value="mock_script"),
        pytest.raises(AttributeError),  # Will fail when trying to call methods on None
    ):
        docker_runner.execute_function(mock_closure)


@patch("lilypad.sandbox.docker.docker")
def test_execute_function_put_archive_error(mock_docker, docker_runner, mock_closure):
    """Test handling of put_archive errors."""
    # Mock Docker client and container
    mock_client = Mock()
    mock_container = Mock()
    mock_docker.from_env.return_value = mock_client
    mock_client.containers.run.return_value = mock_container

    # Mock put_archive to raise error
    mock_container.put_archive.side_effect = Exception("Failed to copy files")

    with (
        patch.object(docker_runner, "generate_script", return_value="mock_script"),
        pytest.raises(Exception, match="Failed to copy files"),
    ):
        docker_runner.execute_function(mock_closure)

    # Verify container was still stopped
    mock_container.stop.assert_called_once()


def test_execute_function_args_kwargs_passed():
    """Test that args and kwargs are passed to generate_script."""
    docker_runner = DockerSandboxRunner()
    mock_closure = Mock(spec=Closure)

    with patch("lilypad.sandbox.docker.docker") as mock_docker:
        # Mock Docker components
        mock_client = Mock()
        mock_container = Mock()
        mock_docker.from_env.return_value = mock_client
        mock_client.containers.run.return_value = mock_container

        # Mock successful execution
        stdout = json.dumps({"result": "test"}).encode("utf-8")
        mock_container.exec_run.return_value = (0, (stdout, b""))

        with patch.object(
            docker_runner, "generate_script", return_value="mock_script"
        ) as mock_generate:
            docker_runner.execute_function(
                mock_closure, "arg1", "arg2", key1="value1", key2="value2"
            )

            # Verify generate_script was called with correct arguments
            mock_generate.assert_called_once_with(
                mock_closure, "arg1", "arg2", key1="value1", key2="value2"
            )
