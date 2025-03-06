"""The `stubs` command to generate type stubs for functions decorated with lilypad.generation."""

import importlib
import os
import re
import sys
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeAlias

import typer
from rich import print
from rich.console import Console
from rich.table import Table

from ...generations import (
    clear_registry,
    disable_recording,
    enable_recording,
    get_decorated_functions,
)
from ...server.client import LilypadClient
from ...server.schemas import GenerationPublic

console = Console()

# Type aliases
FilePath: TypeAlias = str
ModulePath: TypeAlias = str
FunctionInfo: TypeAlias = tuple[
    str, str, int, str
]  # (file_path, function_name, line_number, module_name)

# Regular expression to extract a function signature from a stored signature text
SIGNATURE_REGEX = re.compile(r"def\s+\w+\((.*?)\)\s*->\s*(.*?):")


def _find_python_files(
    directory: str, exclude_dirs: set[str] | None = None
) -> list[FilePath]:
    """Find all Python files in a directory recursively."""
    if exclude_dirs is None:
        exclude_dirs = {
            "venv",
            ".venv",
            "env",
            ".git",
            ".github",
            "__pycache__",
            "build",
            "dist",
        }

    python_files: list[FilePath] = []

    for root, dirs, files in os.walk(directory):
        # Remove excluded directories from dirs to prevent them from being walked
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        for file in files:
            if file.endswith(".py"):
                file_path = os.path.join(root, file)
                python_files.append(file_path)

    return python_files


def _module_path_from_file(
    file_path: FilePath, base_dir: str | None = None
) -> ModulePath:
    """Convert a file path to a module path that can be imported."""
    if base_dir:
        # Make the file path relative to the base directory
        rel_path = os.path.relpath(file_path, base_dir)
    else:
        rel_path = file_path

    # Remove .py extension
    if rel_path.endswith(".py"):
        rel_path = rel_path[:-3]

    # Convert path separators to dots
    module_path = rel_path.replace(os.sep, ".")

    return module_path


def _import_module_safely(module_path: ModulePath) -> bool:
    """Import a module safely, returning success status."""
    try:
        importlib.import_module(module_path)
        return True
    except (ImportError, SyntaxError) as e:
        print(f"Warning: Failed to import {module_path}: {e}", file=sys.stderr)
        return False


def _make_dummy_function(func_name: str) -> Callable[..., Any]:
    """Create a dummy function with the given name for use with get_generations_by_name."""
    def dummy_func(*args, **kwargs) -> None:
        return None
    dummy_func.__name__ = func_name
    dummy_func.__qualname__ = func_name
    return dummy_func


def _extract_signature_parts(signature_text: str) -> tuple[list[str], str]:
    """Extract argument types and return type from a function signature.

    Args:
        signature_text: Full function signature text

    Returns:
        Tuple of (parameter_types_list, return_type)
    """
    # Remove decorator lines and find the function definition
    lines = [
        line for line in signature_text.splitlines() if not line.strip().startswith("@")
    ]
    def_line = ""
    for line in lines:
        if line.strip().startswith("def "):
            def_line = line.strip()
            break

    if not def_line:
        return [], "Any"

    match = SIGNATURE_REGEX.search(def_line)
    if not match:
        return [], "Any"

    params_str, return_type = match.groups()
    param_types = []
    param_names = []

    if params_str.strip():
        for param in params_str.split(","):
            param = param.strip()
            if not param:
                continue

            if ":" in param:
                name, type_hint = param.split(":", 1)
                param_names.append(name.strip())
                param_types.append(type_hint.strip())
            else:
                param_names.append(param.strip())
                param_types.append("Any")

    return param_types, return_type.strip()


def _parse_signature_for_protocol(
    signature_text: str,
) -> tuple[list[tuple[str, str]], str]:
    """Parse a function signature to extract parameter names, types and return type.

    Example:
        Input: "def answer_question(question: str, language: str) -> str: ..."
        Output: [(question, str), (language, str)], str
    """
    # Remove decorator lines and find the function definition
    lines = [
        line for line in signature_text.splitlines() if not line.strip().startswith("@")
    ]
    def_line = ""
    for line in lines:
        if line.strip().startswith("def "):
            def_line = line.strip()
            break

    if not def_line:
        return [], "Any"

    match = SIGNATURE_REGEX.search(def_line)
    if not match:
        return [], "Any"

    params_str, return_type = match.groups()
    params = []

    if params_str.strip():
        for param in params_str.split(","):
            param = param.strip()
            if not param:
                continue

            if ":" in param:
                name, type_hint = param.split(":", 1)
                params.append((name.strip(), type_hint.strip()))
            else:
                params.append((param.strip(), "Any"))

    return params, return_type.strip()


def _generate_protocol_stub_content(
    func_name: str, versions: list[GenerationPublic]
) -> str:
    """Generate stub content using Protocol for the decorated function.

    The generated stub will define a Protocol class with:
    - __call__ method matching the latest function signature
    - version method with overloads for each version number
    """
    if not versions:
        return ""

    lines = []
    lines.append("# This file was auto-generated by lilypad stubs command\n")
    lines.append("from typing import overload, Literal, Callable, Any, Protocol\n\n\n")

    # Sort versions by version number for consistency
    sorted_versions = sorted(versions, key=lambda v: v.version_num or 0)
    latest_version = sorted_versions[-1]

    # Get the latest version's signature for the __call__ method
    params, return_type = _parse_signature_for_protocol(latest_version.signature)

    # Generate the Protocol class
    pascal_case_name = "".join(word.title() for word in func_name.split("_"))
    lines.append(f"class {pascal_case_name}(Protocol):\n")
    lines.append(f"    # Create a protocol for the {func_name} function\n\n")

    # Add __call__ method with the latest signature
    param_str = ", ".join([f"{name}: {type_hint}" for name, type_hint in params])
    lines.append(f"    def __call__(self, {param_str}) -> {return_type}: ...\n")
    lines.append("    # Keep the original function signature as __call__ method\n\n")
    lines.append("    # start typing the function signature\n")
    lines.append(
        "    # The decorated function has `version` method. the decorator set the version of the function automatically\n\n"
    )

    # Add overloads for the version method - now with @classmethod
    for version in sorted_versions:
        version_num = version.version_num
        if version_num is None:
            continue

        param_types, ret_type = _extract_signature_parts(version.signature)
        callable_type = f"Callable[[{', '.join(param_types)}], {ret_type}]"

        lines.append("    @classmethod\n")
        lines.append("    @overload\n")
        lines.append(
            f"    def version(cls, forced_version: Literal[{version_num}]) -> {callable_type}: ...\n"
        )

    # Add base version method
    lines.append("    @classmethod # type: ignore[misc]\n")
    lines.append(
        "    def version(cls, forced_version: int) -> Callable[..., Any]: ...\n\n"
    )

    # Add type assignment for the decorated function (not TypeAlias)
    lines.append("# Set Type hint for the decorated function\n")
    lines.append(f"{func_name} = {pascal_case_name}\n\n\n")

    # Add the dummy greet function
    lines.append("def greet(name: int) -> str: ...\n")

    return "".join(lines)


def _write_stub_file(file_path: str, function_name: str, stub_content: str) -> Path:
    """Write a stub file for the given function in the same directory as the source."""
    # Get the directory of the original file
    directory = os.path.dirname(file_path)

    # Create the stub file path: functionname.pyi in the same directory
    stub_file_path = Path(directory) / f"{function_name}.pyi"

    # Write the stub content
    stub_file_path.write_text(stub_content, encoding="utf-8")

    return stub_file_path


def stubs_command(
    directory: Path = typer.Argument(
        Path("."), help="Directory to scan for decorated functions."
    ),
    exclude: list[str] | None = typer.Option(
        None,
        "--exclude",
        "-e",
        help="Directories to exclude from scanning (comma-separated).",
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show verbose output including stub content."
    ),
) -> None:
    """Generate type stubs for functions decorated with lilypad.generation.

    Scans the specified directory for Python files, finds functions decorated
    with @lilypad.generation, and generates .pyi stub files with proper type
    hints for each version of the function.

    This enables type checking for code like:
        result = answer_question.version(1)("What is the capital of France?")
        result2 = answer_question.version(2)("What is the capital of France?", "French")

    Examples:
        lilypad stubs .
        lilypad stubs ./my_project
        lilypad stubs ./src --exclude tests,examples --verbose
    """
    # Process exclude directories
    exclude_dirs: set[str] = {
        "venv",
        ".venv",
        "env",
        ".git",
        ".github",
        "__pycache__",
        "build",
        "dist",
    }
    if exclude:
        for item in exclude:
            for dir_name in item.split(","):
                exclude_dirs.add(dir_name.strip())

    # Convert Path to string
    dir_str: str = str(directory.absolute())

    with console.status(
        "Scanning for functions decorated with [bold]lilypad.generation[/bold]..."
    ):
        # Find all Python files in the directory
        python_files: list[FilePath] = _find_python_files(dir_str, exclude_dirs)

        if not python_files:
            print(f"No Python files found in {dir_str}")
            return

        # Use an absolute path for the directory
        directory_abs: str = os.path.abspath(dir_str)

        # Add parent directory to Python path temporarily to enable imports
        parent_dir: str = os.path.dirname(directory_abs)
        sys.path.insert(0, parent_dir)

        # Enable recording before importing modules
        enable_recording()

        try:
            # Import each Python file
            for file_path in python_files:
                module_path: ModulePath = _module_path_from_file(file_path, parent_dir)
                _import_module_safely(module_path)

            # Get decorated functions information
            results = get_decorated_functions("lilypad.generation")
        finally:
            # Clean up
            disable_recording()
            clear_registry()
            sys.path.pop(0)  # Remove the directory from Python path

    # Get client for DB operations
    client = LilypadClient()

    # Process decorated functions
    decorator_name = "lilypad.generation"
    functions = results.get(decorator_name, [])

    if not functions:
        print(f"No functions found with decorator [bold]{decorator_name}[/bold]")
        return

    print(
        f"\nFound [bold green]{len(functions)}[/bold green] function(s) with decorator [bold]{decorator_name}[/bold]"
    )

    # Create a table for the results
    table = Table(show_header=True)
    table.add_column("File", style="cyan")
    table.add_column("Function", style="green")
    table.add_column("Versions", style="yellow")
    table.add_column("Stub File", style="magenta")

    # Sort by file path for consistent output
    sorted_functions = sorted(functions, key=lambda x: x[0])

    # Count generated stubs
    stubs_count = 0

    for file_path, function_name, _lineno, _module_name in sorted_functions:
        # Create a dummy function for the client
        dummy_func = _make_dummy_function(function_name)

        try:
            # Get all versions of this function
            with console.status(
                f"Fetching versions for [bold]{function_name}[/bold]..."
            ):
                versions = client.get_generations_by_name(dummy_func)

            if not versions:
                print(f"[yellow]No versions found for {function_name}[/yellow]")
                continue

            # Generate stub content using the Protocol approach
            stub_content = _generate_protocol_stub_content(function_name, versions)

            if verbose:
                print(f"\n[blue]Stub content for {function_name}:[/blue]")
                print(f"[dim]{stub_content}[/dim]")

            # Write stub file
            stub_file = _write_stub_file(file_path, function_name, stub_content)
            stubs_count += 1

            # Make file path relative for display
            try:
                rel_path = os.path.relpath(file_path)
                display_path = rel_path
            except ValueError:
                display_path = file_path

            # Add to result table
            table.add_row(
                display_path, function_name, str(len(versions)), str(stub_file)
            )

        except Exception as e:
            print(f"[red]Error processing {function_name}: {e}[/red]")

    if stubs_count > 0:
        print(f"\nGenerated [bold green]{stubs_count}[/bold green] stub files:")
        console.print(table)
    else:
        print("[yellow]No stub files were generated[/yellow]")
