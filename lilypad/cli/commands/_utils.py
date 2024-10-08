"""Utility functions for the CLI commands."""

from pathlib import Path


def get_prompts_directory() -> Path:
    """Get the prompts directory."""
    return Path.cwd() / "prompts"
