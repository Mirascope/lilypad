"""Utilities for handling configuration."""

import os
from typing import Any
from pathlib import Path

import orjson


def load_config() -> dict[str, Any]:
    try:
        project_dir = os.getenv("LILYPAD_PROJECT_DIR", Path.cwd())
        with open(f"{project_dir}/.lilypad/config.json") as f:
            config = orjson.loads(f.read())
        return config
    except (FileNotFoundError, orjson.JSONDecodeError):
        return {}
