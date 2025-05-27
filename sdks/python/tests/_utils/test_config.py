"""Tests for lilypad._utils.config module."""

import json
from pathlib import Path

import pytest

from lilypad.lib._utils.config import load_config


@pytest.fixture
def config_dir(tmp_path: Path) -> Path:
    """Create a temporary .lilypad directory."""
    config_dir = tmp_path / ".lilypad"
    config_dir.mkdir()
    return config_dir


def test_load_config_no_file():
    """Test loading config when no file exists."""
    assert load_config() == {}


def test_load_config_with_file(config_dir: Path, monkeypatch):
    """Test loading config with existing file."""
    test_config = {"project_id": 123, "port": 8000}
    config_file = config_dir / "config.json"

    with config_file.open("w") as f:
        json.dump(test_config, f)

    monkeypatch.setenv("LILYPAD_PROJECT_DIR", str(config_dir.parent))
    assert load_config() == test_config


def test_load_config_with_empty_file(config_dir: Path, monkeypatch):
    """Test loading config with empty file."""
    config_file = config_dir / "config.json"
    config_file.write_text("")

    monkeypatch.setenv("LILYPAD_PROJECT_DIR", str(config_dir.parent))
    assert load_config() == {}
