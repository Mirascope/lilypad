"""The `run` command, which runs a prompt with lilypad opentelemetry tracing."""

import glob
import os
import runpy
from pathlib import Path

from typer import Argument, Option

from lilypad.configure import init

from ._utils import get_prompts_directory


def find_file_names(directory: Path, prefix: str = "") -> list[str]:
    """Finds all files in a directory.

    Args:
        directory: The directory to search for the prompt.
        prefix: The prefix of the prompt to search for.

    Returns:
        A list of file names found.
    """
    pattern = os.path.join(directory, f"[!_]{prefix}*.py")  # ignores private files
    matching_files_with_dir = glob.glob(pattern)

    # Removing the directory part from each path
    return [os.path.basename(file) for file in matching_files_with_dir]


def prompts_directory_files(prefix: str = "") -> list[str]:
    """Finds all prompt files in the prompts directory.

    Args:
        prefix: The prefix of the prompt to search for.

    Returns:
        A list of prompt file names found.
    """
    prompts_directory = Path.cwd() / "prompts"
    prompt_file_names = find_file_names(prompts_directory, prefix)
    return [f"{name[:-3]}" for name in prompt_file_names]  # remove .py extension


def parse_prompt_file_name(prompt_file_name: str) -> str:
    """Returns the file name without the .py extension."""
    if prompt_file_name.endswith(".py"):
        return prompt_file_name[:-3]
    return prompt_file_name


def run_command(
    prompt_file_name: str = Argument(
        help="Prompt file to use",
        autocompletion=prompts_directory_files,
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
    prompts_file_path = get_prompts_directory()
    if not prompt_file_name.endswith(".py"):
        prompt_file_name = f"{prompt_file_name}.py"

    init()

    if edit:
        os.environ["LILYPAD_EDITOR_OPEN"] = "True"
    runpy.run_path(str(prompts_file_path / prompt_file_name), run_name="__main__")
