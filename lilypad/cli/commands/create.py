"""The `create` command, which is used to create a new prompt stub."""

from rich import print
from typer import Argument

from ._utils import get_prompts_directory


def get_stub(function_name: str) -> str:
    """The stub for the prompt function."""
    return f"""import lilypad

    
@lilypad.synced.prompt()
def {function_name}() -> str: ...


if __name__ == "__main__":
    output = {function_name}()
    print(output)
"""


def create_command(
    prompt_file_name: str = Argument(
        help="Prompt file to add",
    ),
) -> None:
    """Create a Lilypad function stub.

    Args:
        prompt_file_name: The name of the prompt file to create
    """
    prompts_file_path = get_prompts_directory()
    if not prompt_file_name.endswith(".py"):
        prompt_file_name = f"{prompt_file_name}.py"
    prompt_file_path = prompts_file_path / prompt_file_name
    if not prompt_file_path.exists():
        prompt_file_path.touch()
        print(f"Created prompt file {prompt_file_path}")
        with open(prompt_file_path, "w") as f:
            f.write(get_stub(prompt_file_name[:-3]))
    else:
        print(f"Prompt file {prompt_file_name} already exists")
