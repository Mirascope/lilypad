"""Utilities for handling configuration."""

import json
import os
from pathlib import Path
from typing import Any


def load_config() -> dict[str, Any]:
    try:
        project_dir = os.getenv("LILYPAD_PROJECT_DIR", Path.cwd())
        with open(f"{project_dir}/.lilypad/config.json") as f:
            config = json.loads(f.read())
        return config
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
