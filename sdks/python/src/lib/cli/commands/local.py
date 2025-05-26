"""The `local` command to run `lilypad` locally."""

import os
import sys
import json
import time
import signal
import contextlib
import subprocess
from types import FrameType
from pathlib import Path
from importlib.resources import files

import typer
from rich import print

from .... import Lilypad
from ._utils import get_and_create_config
from ..._utils.settings import get_settings


def _start_lilypad(project_dir: Path, port: int) -> subprocess.Popen:
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
    env["LILYPAD_ENVIRONMENT"] = "local"
    env["LILYPAD_PORT"] = str(port)
    files_dir = files("lilypad").joinpath("server")

    process = subprocess.Popen(
        ["fastapi", "dev", "--port", str(port)],
        cwd=str(files_dir),
        env=env,
    )
    return process


def _wait_for_server(lilypad_client: Lilypad) -> bool:
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


def _terminate_process(process: subprocess.Popen) -> None:
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


def local_command(
    port: str | None = typer.Option(default=None, help="Port to run the FastAPI server on."),
) -> None:
    """Run `lilypad` locally.

    - Create the SQLite database if it doesn't exist
    - Start the FastAPI server
    """
    settings = get_settings()
    existing_project = True
    project_name = "DEFAULT"
    new_port: int = int(port) if port else settings.port
    if not os.path.exists(".lilypad"):
        existing_project = False
        project_name = typer.prompt("What's your project name?")
    config_path = os.path.join(".lilypad", "config.json")
    data = get_and_create_config(config_path)
    data["base_url"] = f"http://localhost:{new_port}"
    if existing_project:
        data["port"] = new_port
    with open(config_path, "w") as f:
        json.dump(data, f, indent=4)
    lilypad_client = Lilypad()
    process = _start_lilypad(Path.cwd(), new_port)

    def signal_handler(sig: int, frame: FrameType | None) -> None:
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)

    if not existing_project:
        try:
            if _wait_for_server(lilypad_client):
                project = lilypad_client.post_project(project_name)
                with open(config_path, "w") as f:
                    data["project_uuid"] = str(project.uuid)
                    json.dump(data, f, indent=4)
        except KeyboardInterrupt:
            print("Shutting down...")
            _terminate_process(process)

    with contextlib.suppress(KeyboardInterrupt):
        process.wait()
