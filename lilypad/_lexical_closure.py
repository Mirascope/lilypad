"""Utility to compute a hash of a function and its lexical closure.

Important Notes:

Modules: If a function uses modules, the attribute access may resolve to a module object. Including entire module source code may not be practical, so this code focuses on functions, classes, and constants defined in the global namespace.

Limitations: This approach assumes that all dependencies are accessible via the function's __globals__ attribute. If there are dependencies in other scopes or imported from other modules, they may not be fully captured.
"""

import ast
import hashlib
import inspect
from collections.abc import Callable
from typing import Any


def compute_function_hash(func: Callable) -> tuple[str, str]:
    """Compute a hash of a function and its lexical closure.

    Args:
        func (Callable): The function to hash.
        namespace (Dict[str, Any]): The namespace to resolve dependencies.

    Returns:
        tuple[str, str]: A tuple of the hash and the combined source code.
    """
    combined_source = get_combined_source(func)
    return hashlib.sha256(combined_source.encode("utf-8")).hexdigest(), combined_source


def get_combined_source(
    func: Callable,
) -> str:
    closure_sources = collect_closure_sources(func, {})
    combined_source = "\n\n".join(closure_sources.values())
    return combined_source


def collect_closure_sources(
    func: Callable, namespace: dict[str, Any], visited: dict[str, Any] | None = None
) -> dict[str, Any]:
    if visited is None:
        visited = {}

    func_name = func.__name__
    if func_name in visited:
        return visited

    try:
        source = inspect.getsource(func)
        tree = ast.parse(source)
    except OSError:
        source = repr(func)
        tree = None

    # Collect dependencies
    dependencies = extract_dependencies(tree)

    # Collect classes first
    for dep_name in dependencies:
        if dep_name not in visited and dep_name in func.__globals__:
            dep_obj = func.__globals__[dep_name]
            if inspect.isclass(dep_obj):
                try:
                    class_source = inspect.getsource(dep_obj)
                except OSError:
                    class_source = repr(dep_obj)
                visited[dep_name] = class_source.strip()

    # Collect variables next
    for dep_name in dependencies:
        if dep_name not in visited and dep_name in func.__globals__:
            dep_obj = func.__globals__[dep_name]
            if not inspect.isfunction(dep_obj) and not inspect.isclass(dep_obj):
                variable_repr = serialize_variable(dep_name, dep_obj)
                visited[dep_name] = variable_repr

    # Add the function source
    visited[func_name] = source.strip()

    # Collect functions
    for dep_name in dependencies:
        if dep_name not in visited and dep_name in func.__globals__:
            dep_obj = func.__globals__[dep_name]
            if inspect.isfunction(dep_obj):
                collect_closure_sources(dep_obj, namespace, visited)

    return visited


def serialize_variable(name: str, value: Any) -> str:
    if isinstance(
        value, int | float | str | bool | type(None) | (list | tuple | dict | set)
    ):
        return f"{name} = {repr(value)}"
    elif isinstance(value, object):
        class_name = value.__class__.__name__
        return f"{name} = {class_name}()"
    else:
        return f"{name} = {repr(value)}"


def extract_dependencies(tree: ast.AST | None) -> list[str]:
    class DependencyVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.dependencies = []

        def visit_Name(self, node: Any) -> None:
            self.dependencies.append(node.id)
            self.generic_visit(node)

        def visit_Attribute(self, node: Any) -> None:
            if isinstance(node.value, ast.Name):
                self.dependencies.append(node.value.id)
            self.generic_visit(node)

        def visit_FunctionDef(self, node: Any) -> None:
            # Include decorator dependencies
            for decorator in node.decorator_list:
                self.visit(decorator)
            self.generic_visit(node)

    if not tree:
        return []

    visitor = DependencyVisitor()
    visitor.visit(tree)

    return list(dict.fromkeys(visitor.dependencies))
