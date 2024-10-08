"""The `start` command to initialize Lilypad."""

import os
import subprocess
from importlib.resources import files
from pathlib import Path

import typer
from rich import print

from ...server.db.setup import create_tables

prompt_dir_name = "prompts"


def check_if_prompts_exists() -> bool:
    """Check if the prompts directory exists."""
    return os.path.exists(prompt_dir_name)


def check_if_pad_exists() -> bool:
    """Check if the SQLite database exists."""
    return os.path.exists("pad.db")


def start_command() -> None:
    """Initialize Lilypad.

    - Create prompts directory if it doesn't exist
    - Create the SQLite database if it doesn't exist
    - Start the FastAPI server
    """
    print("Starting Lilypad...")
    destination_dir = Path.cwd()
    if not check_if_prompts_exists():
        os.makedirs(prompt_dir_name, exist_ok=True)
        print(destination_dir)

    if not check_if_pad_exists():
        create_tables()
    files_dir = files("lilypad").joinpath("server")
    env = os.environ.copy()

    # Sets the LILYPAD_PROJECT_DIR so Lilypad knows where to look for the database
    env["LILYPAD_PROJECT_DIR"] = str(destination_dir)
    try:
        subprocess.run(
            ["fastapi", "dev"],
            cwd=str(files_dir),
            env=env,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        typer.echo(f"Error running FastAPI dev: {e}", err=True)
