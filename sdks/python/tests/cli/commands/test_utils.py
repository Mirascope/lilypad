"""Tests for CLI command utilities."""

import json
from unittest.mock import patch, mock_open


from lilypad.cli.commands._utils import get_and_create_config


def test_get_and_create_config_existing_dir_and_file():
    """Test getting config when both directory and file exist."""
    config_data = {"api_key": "test-key", "project_uuid": "test-uuid"}

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(config_data))),
    ):
        result = get_and_create_config(".lilypad/config.json")

    assert result == config_data


def test_get_and_create_config_no_dir():
    """Test creating directory and config file when they don't exist."""
    with patch("os.path.exists", return_value=False), patch("os.mkdir") as mock_mkdir:
        m = mock_open()
        with patch("builtins.open", m):
            result = get_and_create_config(".lilypad/config.json")

    # Verify directory was created
    mock_mkdir.assert_called_once_with(".lilypad")

    # Verify empty config was written
    handle = m()
    written_calls = [call for call in handle.write.call_args_list if call[0][0].strip()]
    assert len(written_calls) > 0
    written_data = "".join(call[0][0] for call in written_calls)
    assert json.loads(written_data) == {}

    # Result should be empty dict
    assert result == {}


def test_get_and_create_config_dir_exists_no_file():
    """Test creating config file when directory exists but file doesn't."""

    def exists_side_effect(path):
        return path == ".lilypad"

    with patch("os.path.exists", side_effect=exists_side_effect), patch("os.mkdir") as mock_mkdir:
        # First open call raises FileNotFoundError (file doesn't exist)
        # Second open call is for writing
        m = mock_open()
        m.side_effect = [FileNotFoundError(), m.return_value]

        with patch("builtins.open", m):
            result = get_and_create_config(".lilypad/config.json")

    # Directory should not be created (already exists)
    mock_mkdir.assert_not_called()

    # Result should be empty dict
    assert result == {}


def test_get_and_create_config_invalid_json():
    """Test handling invalid JSON in existing config file."""
    invalid_json = "{ invalid json"

    with patch("os.path.exists", return_value=True):
        # First open succeeds but contains invalid JSON
        # Second open is for writing
        m = mock_open(read_data=invalid_json)
        m.return_value.read.side_effect = [invalid_json, ""]

        with patch("builtins.open", m), patch("json.load", side_effect=json.JSONDecodeError("test", "doc", 0)):
            result = get_and_create_config(".lilypad/config.json")

    # Result should be empty dict after handling the error
    assert result == {}

    # Verify file was written
    assert any("w" in str(call) for call in m.call_args_list)


def test_get_and_create_config_with_subdirectory():
    """Test with a config path that includes subdirectories."""
    config_data = {"setting": "value"}
    config_path = ".lilypad/subdir/config.json"

    with (
        patch("os.path.exists", return_value=True),
        patch("builtins.open", mock_open(read_data=json.dumps(config_data))),
    ):
        result = get_and_create_config(config_path)

    assert result == config_data
