"""The `run` command, which runs a prompt with lilypad opentelemetry tracing."""

import json
import os
import runpy
from pathlib import Path

from rich import print
from typer import Argument, Option

from lilypad.configure import configure

from ._utils import get_lily_directory, lily_directory_files, parse_prompt_file_name


def run_command(
    prompt_file_name: str = Argument(
        help="Prompt file to use",
        autocompletion=lily_directory_files,
        parser=parse_prompt_file_name,
    ),
    edit: bool | None = Option(
        default=False, help="Edit the prompt file in the default editor"
    ),
) -> None:
    """Run a prompt with lilypad opentelemetry tracing

    Args:
        prompt_file_name: The name of the prompt file to run.
        edit: Whether to open the prompt file in the default editor.
    """
    lily_file_path = get_lily_directory()
    if not prompt_file_name.endswith(".py"):
        prompt_file_name = f"{prompt_file_name}.py"

    configure()
    config_path = Path.cwd() / ".lilypad" / "config.json"
    if edit:
        os.environ["LILYPAD_EDITOR_OPEN"] = "True"
    runpy.run_path(str(lily_file_path / prompt_file_name), run_name="__main__")
    try:
        with open(config_path) as f:
            config = json.loads(f.read())
            if config_id := config.get("project_id", None):
                print(f"\nTraces url: http://localhost:8000/projects/{config_id}")
    except FileNotFoundError:
        return
