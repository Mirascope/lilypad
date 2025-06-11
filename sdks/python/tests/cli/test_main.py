"""Tests for the main CLI module."""

import pytest
from unittest.mock import patch
from typer.testing import CliRunner

from lilypad.cli.main import app


@pytest.fixture
def runner():
    """Create a CLI runner for testing."""
    return CliRunner()


def test_version_command(runner):
    """Test the version command displays the package version."""
    with patch("importlib.metadata.version") as mock_version:
        mock_version.return_value = "1.2.3"

        result = runner.invoke(app, ["version"])

        assert result.exit_code == 0
        assert "1.2.3" in result.stdout
        mock_version.assert_called_once_with("python-lilypad")


def test_local_command_exists(runner):
    """Test that the local command is registered."""
    with patch("lilypad.cli.commands.local_command") as mock_local:
        mock_local.return_value = None

        result = runner.invoke(app, ["local", "--help"])

        assert result.exit_code == 0
        assert "Run Lilypad Locally" in result.stdout


def test_sync_command_exists(runner):
    """Test that the sync command is registered."""
    with patch("lilypad.cli.commands.sync.sync_command") as mock_sync:
        mock_sync.return_value = None

        result = runner.invoke(app, ["sync", "--help"])

        assert result.exit_code == 0
        assert "Scan the specified module directory" in result.stdout


def test_help_command(runner):
    """Test the main help command shows all subcommands."""
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "version" in result.stdout
    assert "local" in result.stdout
    assert "sync" in result.stdout
    assert "Show the Lilypad version" in result.stdout


def test_invalid_command(runner):
    """Test that invalid commands return an error."""
    result = runner.invoke(app, ["invalid-command"])

    assert result.exit_code != 0
    assert "No such command" in result.stdout or "Error" in result.stdout
