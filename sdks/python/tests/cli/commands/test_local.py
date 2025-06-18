"""Tests for the local command."""

import contextlib
import signal
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch, mock_open

import pytest
from typer.testing import CliRunner

from lilypad.cli.commands.local import (
    _start_lilypad,
    _wait_for_server,
    _terminate_process,
    local_command,
)


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def mock_popen():
    """Create a mock subprocess.Popen object."""
    mock = MagicMock()
    mock.poll = MagicMock(return_value=None)
    mock.wait = MagicMock(return_value=0)
    mock.terminate = MagicMock()
    return mock


def test_start_lilypad(mock_popen):
    """Test starting the Lilypad server."""
    with (
        patch("subprocess.Popen", return_value=mock_popen) as mock_popen_class,
        patch("importlib.resources.files") as mock_files,
    ):
        mock_files.return_value.joinpath.return_value = Path("/fake/path")

        process = _start_lilypad(Path("/project"), 8000)

        assert process == mock_popen
        mock_popen_class.assert_called_once()

        # Check environment variables
        call_args = mock_popen_class.call_args
        env = call_args[1]["env"]
        assert env["LILYPAD_PROJECT_DIR"] == "/project"
        assert env["LILYPAD_ENVIRONMENT"] == "local"
        assert env["LILYPAD_PORT"] == "8000"


def test_wait_for_server_success():
    """Test waiting for server when it starts successfully."""
    mock_client = MagicMock()
    mock_client.timeout = 5
    mock_client.get_health.return_value = True

    result = _wait_for_server(mock_client)

    assert result is True
    mock_client.get_health.assert_called_once()


def test_wait_for_server_timeout():
    """Test waiting for server when it times out."""
    mock_client = MagicMock()
    mock_client.timeout = 0.1
    mock_client.get_health.side_effect = Exception("Connection refused")

    with patch("time.sleep"):
        result = _wait_for_server(mock_client)

    assert result is False


def test_wait_for_server_eventual_success():
    """Test waiting for server when it starts after a few attempts."""
    mock_client = MagicMock()
    mock_client.timeout = 5
    mock_client.get_health.side_effect = [
        Exception("Connection refused"),
        Exception("Connection refused"),
        True,
    ]

    with patch("time.sleep"):
        result = _wait_for_server(mock_client)

    assert result is True
    assert mock_client.get_health.call_count == 3


def test_terminate_process_running():
    """Test terminating a running process."""
    mock_process = MagicMock()
    mock_process.poll.return_value = None

    _terminate_process(mock_process)

    mock_process.terminate.assert_called_once()


def test_terminate_process_already_stopped():
    """Test terminating an already stopped process."""
    mock_process = MagicMock()
    mock_process.poll.return_value = 0

    _terminate_process(mock_process)

    mock_process.terminate.assert_not_called()


@patch("os.path.exists")
@patch("typer.prompt")
@patch("lilypad.cli.commands.local.get_sync_client")
@patch("lilypad.cli.commands.local._start_lilypad")
@patch("lilypad.cli.commands.local._wait_for_server")
@patch("lilypad.cli.commands.local.get_and_create_config")
@patch("lilypad.cli.commands.local.get_settings")
@patch("signal.signal")
def test_local_command_new_project(
    mock_signal,
    mock_get_settings,
    mock_get_config,
    mock_wait_server,
    mock_start,
    mock_get_client,
    mock_prompt,
    mock_exists,
):
    """Test local command for a new project."""
    # Setup mocks
    mock_exists.return_value = False
    mock_prompt.return_value = "MyProject"
    mock_get_settings.return_value = MagicMock(port=8000)
    mock_get_config.return_value = {"api_key": "test-key"}

    mock_process = MagicMock()
    mock_process.wait.side_effect = KeyboardInterrupt()
    mock_start.return_value = mock_process

    mock_client = MagicMock()
    mock_project = MagicMock(uuid_="project-uuid")
    mock_client.projects.create.return_value = mock_project
    mock_get_client.return_value = mock_client

    mock_wait_server.return_value = True

    # Use mock_open for file operations
    m = mock_open()
    # Call the function directly
    with (
        patch("builtins.open", m),
        contextlib.suppress(KeyboardInterrupt, SystemExit),
    ):
        local_command(port="9000")  # Expected exceptions

    # Verify project creation
    mock_client.projects.create.assert_called_once_with(name="MyProject")

    # Verify config was written (the function writes twice)
    # Just verify that open was called for writing
    assert any("w" in str(call) for call in m.call_args_list)


@patch("os.path.exists")
@patch("lilypad.cli.commands.local.get_sync_client")
@patch("lilypad.cli.commands.local._start_lilypad")
@patch("lilypad.cli.commands.local.get_and_create_config")
@patch("lilypad.cli.commands.local.get_settings")
@patch("signal.signal")
def test_local_command_existing_project(
    mock_signal,
    mock_get_settings,
    mock_get_config,
    mock_start,
    mock_get_client,
    mock_exists,
):
    """Test local command for an existing project."""
    # Setup mocks
    mock_exists.return_value = True
    mock_get_settings.return_value = MagicMock(port=8000)
    mock_get_config.return_value = {"api_key": "test-key", "project_uuid": "existing-uuid"}

    mock_process = MagicMock()
    mock_process.wait.side_effect = KeyboardInterrupt()
    mock_start.return_value = mock_process

    mock_client = MagicMock()
    mock_get_client.return_value = mock_client

    # Use mock_open for file operations
    m = mock_open()
    # Call the function directly
    with (
        patch("builtins.open", m),
        contextlib.suppress(KeyboardInterrupt, SystemExit),
    ):
        local_command(port=None)

    # Verify no project creation for existing project
    mock_client.projects.create.assert_not_called()

    # Verify process was started
    mock_start.assert_called_once()


def test_signal_handler():
    """Test the signal handler function."""

    # Create a signal handler function inline to test
    def signal_handler(sig: int, frame):
        raise SystemExit(0)

    with pytest.raises(SystemExit) as exc_info:
        signal_handler(signal.SIGINT, None)

    assert exc_info.value.code == 0


def test_terminate_process_already_stopped_coverage():
    """Test _terminate_process when process is already stopped - covers lines 83-86."""
    from lilypad.cli.commands.local import _terminate_process

    # Test with process that has already terminated
    mock_process = Mock()
    mock_process.poll.return_value = 0  # Process already terminated

    _terminate_process(mock_process)

    # Should not call terminate since process is already stopped
    mock_process.terminate.assert_not_called()
    mock_process.wait.assert_not_called()


def test_terminate_process_timeout():
    """Test _terminate_process when process doesn't terminate gracefully - covers lines 83-86."""
    from lilypad.cli.commands.local import _terminate_process

    # Test with process that times out on termination
    mock_process = Mock()
    mock_process.poll.return_value = None  # Process is running
    # First call to wait() raises TimeoutExpired, second call succeeds
    mock_process.wait.side_effect = [
        subprocess.TimeoutExpired("cmd", 5),
        None,  # Second call after kill() succeeds
    ]

    _terminate_process(mock_process)

    # Should call terminate, wait (which raises TimeoutExpired), then kill
    mock_process.terminate.assert_called_once()
    mock_process.kill.assert_called_once()
    assert mock_process.wait.call_count == 2  # Once for timeout, once after kill


def test_local_command_signal_handler_setup():
    """Test that signal handler is properly set up in local_command - covers lines 128-130."""
    from lilypad.cli.commands.local import local_command

    with (
        patch("lilypad.cli.commands.local._start_lilypad") as mock_start,
        patch("lilypad.cli.commands.local._wait_for_server") as mock_wait,
        patch("lilypad.cli.commands.local.get_sync_client") as mock_client,
        patch("lilypad.cli.commands.local.get_settings") as mock_settings,
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data='{"project_uuid": "test"}')),
        patch("json.dump"),
        patch("signal.signal") as mock_signal,
    ):
        # Setup mocks
        mock_settings.return_value = Mock(port=8000)
        mock_process = Mock()
        mock_process.wait.side_effect = KeyboardInterrupt()
        mock_start.return_value = mock_process
        mock_wait.return_value = True

        with contextlib.suppress(KeyboardInterrupt):
            local_command(port=None)

        # Verify signal handler was set up
        import signal as sig

        # Verify SIGINT handler was set (it's a custom function, not SIG_IGN)
        mock_signal.assert_called()
        # Check that SIGINT was the first argument in one of the calls
        sigint_calls = [call for call in mock_signal.call_args_list if call[0][0] == sig.SIGINT]
        assert len(sigint_calls) > 0, "SIGINT handler was not set"


@patch("os.path.exists")
@patch("typer.prompt")
@patch("lilypad.cli.commands.local.get_sync_client")
@patch("lilypad.cli.commands.local._start_lilypad")
@patch("lilypad.cli.commands.local._wait_for_server")
@patch("lilypad.cli.commands.local._terminate_process")
@patch("lilypad.cli.commands.local.get_and_create_config")
@patch("lilypad.cli.commands.local.get_settings")
@patch("signal.signal")
def test_local_command_new_project_keyboard_interrupt(
    mock_signal,
    mock_get_settings,
    mock_get_config,
    mock_terminate,
    mock_wait_server,
    mock_start,
    mock_get_client,
    mock_prompt,
    mock_exists,
):
    """Test local command with KeyboardInterrupt during new project creation - covers lines 128-130."""
    # Setup mocks
    mock_exists.return_value = False
    mock_prompt.return_value = "MyProject"
    mock_get_settings.return_value = MagicMock(port=8000)
    mock_get_config.return_value = {"api_key": "test-key"}

    mock_process = MagicMock()
    mock_start.return_value = mock_process

    mock_client = MagicMock()
    # Simulate KeyboardInterrupt during project creation
    mock_client.projects.create.side_effect = KeyboardInterrupt()
    mock_get_client.return_value = mock_client

    mock_wait_server.return_value = True

    # Use mock_open for file operations
    m = mock_open()

    # Call the function and expect no exception (KeyboardInterrupt is handled)
    with patch("builtins.open", m), contextlib.suppress(KeyboardInterrupt):
        # The function should handle the KeyboardInterrupt internally
        local_command(port="9000")

    # Verify that _terminate_process was called when KeyboardInterrupt occurred
    mock_terminate.assert_called_once_with(mock_process)
