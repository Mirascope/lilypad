"""The `create` command, which is used to create a new prompt stub."""

from rich import print
from typer import Argument

from ._utils import (
    generate_lily_init,
    generate_llm_fn_stub,
    get_lily_directory,
    lily_directory_files,
)


def create_command(
    prompt_file_name: str = Argument(
        help="Prompt file to add",
    ),
) -> None:
    """Create a Lilypad function stub.

    Args:
        prompt_file_name: The name of the prompt file to create
    """
    lily_file_path = get_lily_directory()
    if not prompt_file_name.endswith(".py"):
        prompt_file_name = f"{prompt_file_name}.py"
    prompt_file_path = lily_file_path / prompt_file_name
    if not prompt_file_path.exists():
        prompt_file_path.touch()
        print(f"Created lilypad file {prompt_file_path}")
        with open(prompt_file_path, "w") as f:
            f.write(generate_llm_fn_stub(prompt_file_name[:-3]))
        lily_files = lily_directory_files()

        init_file = lily_file_path / "__init__.py"
        with open(init_file, "w") as f:
            f.write(generate_lily_init(lily_files))
    else:
        print(f"Lilypad file {prompt_file_name} already exists")
