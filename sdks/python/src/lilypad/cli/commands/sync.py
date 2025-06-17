"""Sync command for generating type stubs for functions decorated with lilypad.traces."""

import os
import ast
import sys
import json
import inspect
import importlib
from typing import Any, TypeAlias
from pathlib import Path
from textwrap import dedent
from ...generated.types.function_public import FunctionPublic

import typer
from rich import print
from rich.table import Table
from rich.console import Console

from ...traces import (
    TRACE_MODULE_NAME,
    clear_registry,
    enable_recording,
    disable_recording,
    get_decorated_functions,
)
from ..._utils.client import get_sync_client
from ..._utils.closure import Closure, _run_ruff
from ..._utils.settings import get_settings

app = typer.Typer()
console = Console()
DEBUG: bool = False

FilePath: TypeAlias = str
ModulePath: TypeAlias = str
FunctionInfo: TypeAlias = tuple[str, str, int, str]

DEFAULT_DIRECTORY: Path = typer.Argument(Path("."), help="Directory to scan for decorated functions.")
DEFAULT_EXCLUDE: list[str] | None = typer.Option(
    None, "--exclude", "-e", help="Comma-separated list of directories to exclude."
)
DEFAULT_VERBOSE: bool = typer.Option(False, "--verbose", "-v", help="Show verbose output.")


def _find_python_files(directory: str, exclude_dirs: set[str] | None = None) -> list[FilePath]:
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
            "node_modules",
        }
    python_files: list[FilePath] = []
    for root, dirs, files in os.walk(directory):
        # Filter out excluded directories to prevent walking into them
        dirs[:] = [d for d in dirs if d not in exclude_dirs]

        # Only include files if the current directory is not in an excluded path
        current_dir = os.path.basename(root)
        if current_dir not in exclude_dirs:
            for file in files:
                if file.endswith(".py"):
                    python_files.append(os.path.join(root, file))
    return python_files


def _module_path_from_file(file_path: FilePath, base_dir: str | None = None) -> ModulePath:
    if base_dir:
        # Handle Windows and Unix paths properly
        file_path = file_path.replace("\\", "/")
        base_dir = base_dir.replace("\\", "/")

        if file_path.startswith(base_dir):
            rel_path = file_path[len(base_dir) :].lstrip("/")
        else:  # pragma: no cover
            # Fallback to relpath for complex cases
            rel_path = os.path.relpath(file_path, base_dir)
    else:
        rel_path = file_path

    if rel_path.endswith(".py"):
        rel_path = rel_path[:-3]

    # Normalize path separators - handle both Windows and Unix
    return rel_path.replace("\\", ".").replace("/", ".")


def _import_module_safely(module_path: ModulePath) -> bool:
    try:
        importlib.import_module(module_path)
        return True
    except (ImportError, SyntaxError) as e:
        print(f"Warning: Failed to import {module_path}: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error: Unexpected error importing {module_path}: {e}", file=sys.stderr)
        return False


def _normalize_signature(signature_text: str) -> str:
    # Return only the function definition line (ignoring import lines and decorators)
    lines = signature_text.splitlines()

    # Find lines that are part of function definition
    func_lines = []
    in_function = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("def ") or stripped.startswith("async def "):
            in_function = True
            func_lines.append(stripped)
        elif in_function and (
            stripped.startswith(")")
            or stripped.endswith("):")
            or (stripped and not stripped.startswith("@") and not stripped.startswith("#"))
        ):
            func_lines.append(stripped)
            if stripped.endswith(":"):
                break
        elif in_function and stripped:  # pragma: no cover
            func_lines.append(stripped)

    if not func_lines:
        # Fallback: just clean all non-decorator lines
        func_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith("@")]

    # Join with single spaces, clean up extra whitespace
    normalized = " ".join(func_lines)
    # Normalize whitespace but preserve structure
    import re

    normalized = re.sub(r"\s+", " ", normalized).strip()

    # Only modify signatures that explicitly have ... as placeholder
    if normalized.endswith("..."):
        normalized = normalized[:-3] + " pass"
    # Don't add pass to normal function signatures ending with :

    if DEBUG:
        print(f"[DEBUG] Normalized signature: {normalized}")
    return normalized


def _parse_parameters_from_signature(signature_text: str) -> list[str]:
    try:
        normalized = _normalize_signature(signature_text)

        # For AST parsing, we need a valid function body
        if normalized.endswith(":"):  # pragma: no cover
            normalized += " pass"

        module = ast.parse(normalized)
        func_def = module.body[0]
        params: list[str] = []
        total_args = func_def.args.args  # pyright: ignore [reportAttributeAccessIssue]
        defaults = func_def.args.defaults  # pyright: ignore [reportAttributeAccessIssue]
        num_defaults = len(defaults)
        start_default = len(total_args) - num_defaults
        for i, arg in enumerate(total_args):
            param_str = arg.arg
            if arg.annotation is not None:
                try:
                    annotation = ast.unparse(arg.annotation)
                except Exception:  # pragma: no cover
                    annotation = "Any"
                param_str += f": {annotation}"
            if i >= start_default:
                default_node = defaults[i - start_default]
                try:
                    default_val = ast.unparse(default_node)
                except Exception:  # pragma: no cover
                    default_val = "..."
                param_str += f" = {default_val}"
            params.append(param_str)

        # Handle *args
        if func_def.args.vararg:  # pyright: ignore [reportAttributeAccessIssue]
            vararg = func_def.args.vararg  # pyright: ignore [reportAttributeAccessIssue]
            vararg_str = f"*{vararg.arg}"
            if vararg.annotation:
                try:
                    annotation = ast.unparse(vararg.annotation)
                except Exception:  # pragma: no cover
                    annotation = "Any"
                vararg_str += f": {annotation}"
            params.append(vararg_str)

        # Handle keyword-only arguments
        kwonlyargs = func_def.args.kwonlyargs  # pyright: ignore [reportAttributeAccessIssue]
        kw_defaults = func_def.args.kw_defaults  # pyright: ignore [reportAttributeAccessIssue]
        for i, arg in enumerate(kwonlyargs):  # pragma: no cover
            param_str = arg.arg
            if arg.annotation is not None:
                try:
                    annotation = ast.unparse(arg.annotation)
                except Exception:  # pragma: no cover
                    annotation = "Any"
                param_str += f": {annotation}"
            # Check if this keyword-only arg has a default
            if i < len(kw_defaults) and kw_defaults[i] is not None:
                try:
                    default_val = ast.unparse(kw_defaults[i])
                except Exception:  # pragma: no cover
                    default_val = "..."
                param_str += f" = {default_val}"
            params.append(param_str)

        # Handle **kwargs
        if func_def.args.kwarg:  # pyright: ignore [reportAttributeAccessIssue]
            kwarg = func_def.args.kwarg  # pyright: ignore [reportAttributeAccessIssue]
            kwarg_str = f"**{kwarg.arg}"
            if kwarg.annotation:
                try:
                    annotation = ast.unparse(kwarg.annotation)
                except Exception:  # pragma: no cover
                    annotation = "Any"
                kwarg_str += f": {annotation}"
            params.append(kwarg_str)
        # Remove the first parameter if it is 'trace_ctx'
        if params and params[0].split(":")[0].strip() == "trace_ctx":
            params = params[1:]
        if DEBUG:
            print(f"[DEBUG] Parsed parameters from normalized signature:\n{normalized}\n=> {params}")
        return params
    except Exception as e:
        if DEBUG:
            print(f"[DEBUG] Error parsing parameters: {e}")
        return []


def _extract_type_from_param(param: str) -> str:
    parts = param.split(":", 1)
    if len(parts) < 2:
        return "Any"
    rest = parts[1].strip()
    type_part = rest.split("=")[0].strip() if "=" in rest else rest
    return type_part


def _merge_parameters(signature_text: str, arg_types_val: Any) -> list[str]:
    params_list = _parse_parameters_from_signature(signature_text)
    if isinstance(arg_types_val, dict):
        arg_types_dict = arg_types_val
    else:
        try:
            arg_types_dict = json.loads(arg_types_val)
        except Exception as e:
            if DEBUG:
                print(f"[DEBUG] Error loading arg_types: {e}")
            arg_types_dict = {}
    merged: list[str] = []
    for param in params_list:
        parts = param.split(":", 1)
        name = parts[0].strip()
        default_part = None
        if len(parts) > 1:
            type_and_default = parts[1].strip()
            if "=" in type_and_default:
                type_part, default_part = type_and_default.split("=", 1)
                type_part = type_part.strip()
                default_part = default_part.strip()
            else:
                type_part = type_and_default
        else:  # pragma: no cover
            type_part = "Any"
        new_type = arg_types_dict.get(name, type_part)
        if default_part:
            merged.append(f"{name}: {new_type} = {default_part}")
        else:
            merged.append(f"{name}: {new_type}")
    if DEBUG:
        print(f"[DEBUG] Merged parameters for signature:\n{signature_text}\narg_types: {arg_types_val}\n=> {merged}")
    return merged


def _parse_return_type(signature_text: str) -> str:
    try:
        normalized = _normalize_signature(signature_text)

        # For AST parsing, we need a valid function body
        if normalized.endswith(":"):  # pragma: no cover
            normalized += " pass"

        module = ast.parse(normalized)
        func_def = module.body[0]
        ret = ast.unparse(func_def.returns).strip() if func_def.returns is not None else "Any"  # pyright: ignore [reportAttributeAccessIssue]
        if DEBUG:  # pragma: no cover
            print(f"[DEBUG] Parsed return type from normalized signature: {normalized} => {ret}")
        return ret
    except Exception as e:
        if DEBUG:  # pragma: no cover
            print(f"[DEBUG] Error parsing return type: {e}")
        return "Any"


def _extract_parameter_types(merged_params: list[str]) -> list[str]:
    types = [_extract_type_from_param(param) for param in merged_params]
    if DEBUG:
        print(f"[DEBUG] Extracted parameter types from merged params: {merged_params} => {types}")
    return types


def _get_deployed_version(versions: list[FunctionPublic]) -> FunctionPublic:
    """Return the deployed version from the list, choosing the highest version
    that is not archived; if none is found, return the last version."""
    for v in sorted(versions, key=lambda v: v.version_num or 0, reverse=True):
        if not getattr(v, "archived", None):
            return v
    return versions[-1]


def _format_return_type(ret_type: str | None, is_async: bool, wrapped: bool) -> str:
    """Format the return type based on whether it's async and if it's wrapped."""
    # Default to Any if ret_type is None or empty
    if ret_type is None or ret_type == "":
        ret_type = "Any"

    if is_async:
        if wrapped:
            return f"Coroutine[Any, Any, AsyncTrace[{ret_type}]]"
        else:
            return f"Coroutine[Any, Any, {ret_type}]"
    else:
        if wrapped:
            return f"Trace[{ret_type}]"
        else:
            return ret_type


def _generate_protocol_stub_content(
    func_name: str, versions: list[FunctionPublic], is_async: bool, wrapped: bool
) -> str:
    if not versions:
        return ""
    sorted_versions = sorted(versions, key=lambda v: v.version_num or 0)
    latest_version = sorted_versions[-1]
    ret_type_latest = _parse_return_type(latest_version.signature)
    class_name = "".join(word.title() for word in func_name.split("_"))
    version_protocols = []
    version_overloads = []
    for version in sorted_versions:
        if version.version_num is None:
            continue
        merged_params = (
            _merge_parameters(version.signature, version.arg_types)
            if version.arg_types
            else _parse_parameters_from_signature(version.signature)
        )
        params_str = ", ".join(merged_params)

        ret_type = _parse_return_type(version.signature)
        ret_type_formatted = _format_return_type(ret_type, False, wrapped)
        if is_async and wrapped:
            ret_type_formatted = f"Async{ret_type_formatted}"

        version_class_name = f"{class_name}Version{version.version_num}"
        # Normal protocol for this version
        ver_proto = (
            f"class {version_class_name}(Protocol):\n"
            f"    def __call__(self, {params_str}) -> {ret_type_formatted}: ...\n\n"
        )
        version_protocols.append(ver_proto)

        version_overload = (
            f"    @classmethod\n"
            f"    @overload\n"
            f"    def version(cls, forced_version: Literal[{version.version_num}], sandbox: SandboxRunner | None = None) -> {version_class_name}: ..."
        )
        version_overloads.append(version_overload)
    # Overloads for main __call__
    latest_params = (
        _merge_parameters(latest_version.signature, latest_version.arg_types)
        if latest_version.arg_types
        else _parse_parameters_from_signature(latest_version.signature)
    )
    params_str_latest = ", ".join(latest_params)

    deployed_version = _get_deployed_version(versions)
    deployed_params = (
        _merge_parameters(deployed_version.signature, deployed_version.arg_types)
        if deployed_version.arg_types
        else _parse_parameters_from_signature(deployed_version.signature)
    )
    deployed_params_str = ", ".join(deployed_params)
    deployed_return_type = _parse_return_type(deployed_version.signature)
    # Implementation methods with union return types
    formatted_ret_type_latest = _format_return_type(ret_type_latest, is_async, wrapped)
    if params_str_latest:
        main_call_impl = f"    def __call__(self, {params_str_latest}) -> {formatted_ret_type_latest}: ..."

    else:
        main_call_impl = f"    def __call__(self) -> {formatted_ret_type_latest}: ..."
    formatted_ret_type_deployed = _format_return_type(deployed_return_type, is_async, wrapped)
    if deployed_params_str:
        main_remote_impl = f"    def remote(self, {deployed_params_str}, sandbox: SandboxRunner | None = None) -> {formatted_ret_type_deployed}: ..."
    else:
        main_remote_impl = (
            f"    def remote(self, sandbox: SandboxRunner | None = None) -> {formatted_ret_type_deployed}: ..."
        )

    # Version overloads (normal and wrapped)
    version_overload_block = "\n\n".join(version_overloads)  # + wrapped_overloads)
    formatted_ret_type_impl = _format_return_type("Any", is_async, wrapped)
    base_version = (
        f"    @classmethod  # type: ignore[misc]\n"
        f"    def version(cls, forced_version: int, sandbox: SandboxRunner | None = None) -> Callable[..., {formatted_ret_type_impl}]: ..."
    )
    header_types = (
        "overload, Literal, Callable, Any, Protocol, Coroutine"
        if is_async
        else "overload, Literal, Callable, Any, Protocol"
    )
    joined_protocols = "\n\n".join(version_protocols)

    content = f"""# This file was auto-generated by lilypad sync command
from typing import {header_types}


{joined_protocols}

class {class_name}(Protocol):


{main_call_impl}

{main_remote_impl}

{version_overload_block}

{base_version}

{func_name}: {class_name}
"""
    if DEBUG:
        print(f"[DEBUG] Generated stub content for function '{func_name}':\n{content}")
    return dedent(content)


def sync_command(
    directory: Path = DEFAULT_DIRECTORY,
    exclude: list[str] | None = DEFAULT_EXCLUDE,
    verbose: bool = DEFAULT_VERBOSE,
    debug: bool = False,
) -> None:
    """Generate type stubs for functions decorated with lilypad.generation."""
    global DEBUG
    DEBUG = debug
    if not isinstance(exclude, list):
        exclude = []
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
    for item in exclude:
        for dir_name in item.split(","):
            exclude_dirs.add(dir_name.strip())
    dir_str: str = str(directory.absolute())
    with console.status(f"Scanning for functions decorated with [bold]{TRACE_MODULE_NAME}[/bold]..."):
        python_files: list[FilePath] = _find_python_files(dir_str, exclude_dirs)
        if not python_files:
            print(f"No Python files found in {dir_str}")
            return
        directory_abs: str = os.path.abspath(dir_str)
        parent_dir: str = os.path.dirname(directory_abs)
        sys.path.insert(0, parent_dir)
        enable_recording()
        try:
            for file_path in python_files:
                module_path: ModulePath = _module_path_from_file(file_path, parent_dir)
                _import_module_safely(module_path)
            results = get_decorated_functions(TRACE_MODULE_NAME)
        finally:
            disable_recording()
            clear_registry()
            sys.path.pop(0)
    settings = get_settings()
    client = get_sync_client(api_key=settings.api_key)
    decorator_name = TRACE_MODULE_NAME
    functions = results.get(decorator_name, [])
    if not functions:
        print(f"No functions found with decorator [bold]{decorator_name}[/bold]")
        return
    print(f"\nFound [bold green]{len(functions)}[/bold green] function(s) with decorator [bold]{decorator_name}[/bold]")
    table = Table(show_header=True)
    table.add_column("Source File", style="cyan")
    table.add_column("Functions", style="green")
    table.add_column("Versions", style="yellow")
    file_stub_map: dict[str, list[str]] = {}
    file_func_map: dict[str, list[str]] = {}
    has_async_trace = False
    has_sync_trace = False
    for file_path, function_name, _lineno, module_name, context in sorted(functions, key=lambda x: x[0]):
        try:
            mod = importlib.import_module(module_name)
            fn = getattr(mod, function_name)
            is_async = inspect.iscoroutinefunction(fn)
        except Exception as e:
            print(f"[red]Error retrieving function {function_name} from {module_name}: {e}[/red]")
            continue
        closure = Closure.from_fn(fn)
        try:
            with console.status(f"Fetching versions for [bold]{function_name}[/bold]..."):
                versions = client.projects.functions.get_by_name(
                    function_name=closure.name, project_uuid=settings.project_id
                )
            if not versions:  # pragma: no cover
                print(f"[yellow]No versions found for {function_name}[/yellow]")
                continue
            if context is None:  # pragma: no cover
                context = {}
            wrapped = context.get("mode") == "wrap"
            stub_content = _run_ruff(
                dedent(_generate_protocol_stub_content(function_name, versions, is_async, wrapped))
            ).strip()
            if wrapped:
                if is_async:  # pragma: no cover
                    has_async_trace = True
                else:
                    has_sync_trace = True
            file_stub_map.setdefault(file_path, []).append(stub_content)
            file_func_map.setdefault(file_path, []).append(function_name)
            table.add_row(file_path, function_name, str(len(versions)))
            if verbose:
                print(f"\n[blue]Stub content for {function_name}:[/blue]")
                print(f"[dim]{stub_content}[/dim]")
        except Exception as e:  # pragma: no cover
            print(f"[red]Error processing {function_name}: {e}[/red]")
    for src_file, stubs in file_stub_map.items():
        merged_imports: set[str] = set()
        for stub in stubs:
            lines = stub.splitlines()
            for line in lines:
                if line.startswith("from typing import"):
                    imported = line.split("import", 1)[1].strip()
                    for token in imported.split(","):
                        merged_imports.add(token.strip())
                    break
        base_symbols = {"overload", "Literal", "Callable", "Any", "Protocol"}
        merged_imports |= base_symbols
        for stub in stubs:
            if "Coroutine" in stub:  # pragma: no cover
                merged_imports.add("Coroutine")
                break
        merged_imports_str = ", ".join(sorted(merged_imports))

        new_header = [
            "# This file was auto-generated by lilypad sync command",
            f"from typing import {merged_imports_str}",
            "from lilypad.sandbox import SandboxRunner",
        ]
        if has_async_trace:  # pragma: no cover
            new_header.append(f"from {TRACE_MODULE_NAME} import AsyncTrace")
        if has_sync_trace:
            new_header.append(f"from {TRACE_MODULE_NAME} import Trace")
        content_parts = []
        for stub in stubs:
            lines = stub.splitlines()
            idx = 0
            for i, line in enumerate(lines):
                if line.startswith("class "):
                    idx = i
                    break
            content_parts.append("\n".join(lines[idx:]))
        final_content = "\n".join(new_header) + "\n\n" + "\n\n".join(content_parts)
        stub_file = Path(src_file).with_suffix(".pyi")
        stub_file.parent.mkdir(parents=True, exist_ok=True)
        stub_file.write_text(final_content, encoding="utf-8")
    print(f"\nGenerated stub files for {len(file_stub_map)} source file(s).")
    console.print(table)


if __name__ == "__main__":  # pragma: no cover
    app.command()(sync_command)
    app()
