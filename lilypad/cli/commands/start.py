"""The `start` command to initialize Lilypad."""

import contextlib
import os
import signal
import subprocess
import sys
import time
from importlib.resources import files
from pathlib import Path
from types import FrameType

import typer
from rich import print
from typer import Option

from lilypad._utils import load_config
from lilypad.server import client

from ...server.db.setup import create_tables


def check_if_pad_exists() -> bool:
    """Check if the SQLite database exists."""
    return os.path.exists("pad.db")


def check_if_lilypad_exists() -> bool:
    """Check if the project name exists."""
    return os.path.exists(".lilypad")


def check_if_lily_exists() -> bool:
    """Check if the project name exists."""
    return os.path.exists("lily")


def start_lilypad(project_dir: Path, port: str) -> subprocess.Popen:
    """Starts the FastAPI server using subprocess.Popen.

    Args:
        project_dir (Path): The path to the project directory.
        port (str): The port to run the FastAPI server on.

    Returns:
        subprocess.Popen: The subprocess running the FastAPI server.
    """
    env = os.environ.copy()

    # Sets the LILYPAD_PROJECT_DIR so Lilypad knows where to look for the database
    env["LILYPAD_PROJECT_DIR"] = str(project_dir)
    files_dir = files("lilypad").joinpath("server")
    process = subprocess.Popen(
        ["fastapi", "dev", "--port", port],
        cwd=str(files_dir),
        env=env,
    )
    return process


def wait_for_server(lilypad_client: client.LilypadClient) -> bool:
    """Waits until the server is up and running.

    Args:
        lilypad_client (LilypadClient): The Lilypad client.

    Returns:
        bool: True if the server is up within the timeout period, False otherwise.
    """
    start_time: float = time.time()
    while True:
        try:
            if lilypad_client.get_health():
                return True
        except Exception:
            pass  # Server not yet available
        if time.time() - start_time > lilypad_client.timeout:
            print(f"Server did not start within {lilypad_client.timeout} seconds.")
            return False
        time.sleep(1)  # Wait before retrying


def terminate_process(process: subprocess.Popen) -> None:
    """Terminates the subprocess gracefully.

    Args:
        process (subprocess.Popen): The subprocess to terminate.
    """
    if process.poll() is None:
        print("Terminating the FastAPI server...")
        process.terminate()
        try:
            process.wait(timeout=5)
            print("Server terminated gracefully.")
        except subprocess.TimeoutExpired:
            print("Server did not terminate gracefully. Killing it.")
            process.kill()
            process.wait()
    else:
        print("Server process already terminated.")


def start_command(
    port: str = Option(default="8000", help="Port to run the FastAPI server on."),
) -> None:
    """Initialize Lilypad.

    - Create prompts directory if it doesn't exist
    - Create the SQLite database if it doesn't exist
    - Start the FastAPI server
    """
    is_new_project = False
    project_name = "DEFAULT"
    if not check_if_lilypad_exists():
        is_new_project = True
        project_name = typer.prompt("What's your project name?")
    destination_dir = Path.cwd()

    if not check_if_pad_exists():
        create_tables()

    if not check_if_lily_exists():
        os.mkdir("lily")
        lily_init = destination_dir / "lily" / "__init__.py"
        lily_init.touch()

    config = load_config()
    port = config.get("port", port)
    lilypad_client = client.LilypadClient(
        base_url=f"http://localhost:{port}/api", timeout=10
    )
    process = start_lilypad(destination_dir, port)

    def signal_handler(sig: int, frame: FrameType | None) -> None:
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    if is_new_project:
        try:
            if wait_for_server(lilypad_client):
                project = lilypad_client.post_project(project_name)
                os.mkdir(".lilypad")
                with open(".lilypad/config.json", "w") as f:
                    f.write(
                        f'{{"project_name": "{project_name}", "project_id": "{project.id}", "port": {port}}}'
                    )
        except KeyboardInterrupt:
            print("Shutting down...")
            terminate_process(process)

    with contextlib.suppress(KeyboardInterrupt):
        process.wait()
