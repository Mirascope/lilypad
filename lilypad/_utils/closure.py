"""Utility for computing the lexical closure of a function."""

import ast
import hashlib
import inspect
import sys
from collections.abc import Callable
from dataclasses import dataclass
from functools import lru_cache
from types import ModuleType
from typing import Any

import black


@dataclass
class _CodeLocation:
    """Represents the location of a piece of code."""

    module_path: str
    line_number: int

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _CodeLocation):
            return NotImplemented
        return (
            self.module_path == other.module_path
            and self.line_number == other.line_number
        )

    def __hash__(self) -> int:
        return hash((self.module_path, self.line_number))


class _DependencyCollector:
    """Collects all dependencies for a function."""

    def __init__(self) -> None:
        self._collected_code: dict[_CodeLocation, str] = {}
        self._collected_imports: set[str] = set()
        self._collected_variables: dict[str, str] = {}
        self._visited: set[_CodeLocation] = set()
        self._visited_functions: set[str] = set()
        self._visited_classes: set[str] = set()
        self._package_paths = self._get_package_paths()
        self._module_cache: dict[str, ModuleType] = {}
        self._dependency_graph: dict[str, set[str]] = {}
        self._class_dependency_graph: dict[str, set[str]] = {}
        self._main_function_name: str | None = None

    def _format_code(self, code: str) -> str:
        """Format code using ruff."""
        try:
            mode = black.Mode(
                line_length=88,
                string_normalization=True,
                is_pyi=False,
            )
            return black.format_str(code, mode=mode)
        except Exception:
            # If formatting fails, return the original code
            return code

    def _get_package_paths(self) -> set[str]:
        """Get paths where third-party packages are installed."""
        return {
            path
            for path in sys.path
            if any(substr in path for substr in ["site-packages", "dist-packages"])
        }

    def collect(self, func: Callable[..., Any]) -> str:
        """Collect all dependencies for a function and return the combined source."""
        self._main_function_name = func.__name__
        module = inspect.getmodule(func)
        if module:
            # Cache the module for later lookups
            self._module_cache[module.__name__] = module
        self._collect_function_and_deps(func)
        return self._format_output()

    def _build_dependency_graph(self, code: str, function_name: str) -> None:
        """Build dependency graph for a given function."""
        tree = ast.parse(code)
        visitor = _DependencyVisitor()
        visitor.visit(tree)

        # If it's a function, update function dependencies
        if isinstance(tree.body[0], ast.FunctionDef):
            self._dependency_graph[function_name] = set(visitor.functions)
        # If it's a class, update class dependencies
        elif isinstance(tree.body[0], ast.ClassDef):
            self._class_dependency_graph[function_name] = set(visitor.classes)

    def _get_ordered_classes(self) -> list[str]:
        """Get classes ordered by their dependencies."""
        # Start with classes that have no dependencies
        ordered: list[str] = []
        visited: set[str] = set()

        def visit(class_name: str) -> None:
            if class_name in visited:
                return
            visited.add(class_name)
            # First visit all dependencies
            for dep in self._class_dependency_graph.get(class_name, set()):
                if dep in self._class_dependency_graph:
                    visit(dep)
            ordered.append(class_name)

        # Visit all classes to ensure complete ordering
        for class_name in self._class_dependency_graph:
            visit(class_name)

        return ordered[::-1]  # Reverse to match function ordering style

    def _is_third_party_module(self, module_path: str | None) -> bool:
        """Check if a module is from a third-party package."""
        if not module_path:
            return True
        return any(module_path.startswith(path) for path in self._package_paths)

    def _find_function_in_module(
        self, name: str, module: ModuleType
    ) -> Callable[..., Any] | None:
        """Try to find a function in a module or its parent packages."""
        if hasattr(module, name):
            value = getattr(module, name)
            if inspect.isfunction(value):
                return value

        # Look in parent packages
        if "." in module.__name__:
            parent_name = module.__name__.rsplit(".", 1)[0]
            if parent_name in sys.modules:
                parent_module = sys.modules[parent_name]
                return self._find_function_in_module(name, parent_module)

        return None

    def _collect_class_definition(self, class_name: str, module: ModuleType) -> None:
        """Collect a class definition and its dependencies."""
        if class_name in self._visited_classes:
            return

        # Find the class in the module
        if hasattr(module, class_name):
            cls = getattr(module, class_name)
            if inspect.isclass(cls):
                try:
                    source = inspect.getsource(cls)
                    location = self._get_code_location(cls)
                    if location not in self._visited:
                        self._collected_code[location] = source
                        self._build_dependency_graph(source, class_name)
                        self._visited.add(location)
                        self._visited_classes.add(class_name)

                        # Parse class source to find any dependencies
                        tree = ast.parse(source)
                        visitor = _DependencyVisitor()
                        visitor.visit(tree)

                        # Process any functions or classes used within this class
                        for name in visitor.functions | visitor.classes:
                            if hasattr(module, name):
                                value = getattr(module, name)
                                if inspect.isfunction(value):
                                    self._collect_function_and_deps(value)
                                elif inspect.isclass(value):
                                    self._collect_class_definition(name, module)
                except (OSError, TypeError):
                    pass

    def _collect_function_and_deps(self, func: Callable[..., Any]) -> None:
        try:
            if func.__name__ in self._visited_functions:
                return
            self._visited_functions.add(func.__name__)

            # Get the module containing the function
            module = inspect.getmodule(func)
            if module and self._is_third_party_module(module.__file__):
                return

            # Get function source and create AST
            source = inspect.getsource(func)
            tree = ast.parse(source)
            visitor = _DependencyVisitor()
            visitor.visit(tree)

            # Store the function's source code
            location = self._get_code_location(func)
            if location not in self._visited:
                self._collected_code[location] = source
                self._build_dependency_graph(source, func.__name__)
                self._visited.add(location)

            # Process imports first
            for imp in visitor.imports:
                if self._is_user_defined_import(imp):
                    self._collected_imports.add(imp)

            # Process classes before functions
            for class_name in visitor.classes:
                if module:
                    self._collect_class_definition(class_name, module)

            # Look for functions
            for name in visitor.functions:
                # First check in globals
                if name in func.__globals__:
                    value = func.__globals__[name]
                    if inspect.isfunction(value):
                        func_module = inspect.getmodule(value)
                        if func_module and not self._is_third_party_module(
                            func_module.__file__
                        ):
                            self._collect_function_and_deps(value)
                            continue

                # Then check in the module
                if module:
                    found_func = self._find_function_in_module(name, module)
                    if found_func:
                        func_module = inspect.getmodule(found_func)
                        if func_module and not self._is_third_party_module(
                            func_module.__file__
                        ):
                            self._collect_function_and_deps(found_func)
                            continue

                # Finally check in cached modules
                for cached_module in self._module_cache.values():
                    found_func = self._find_function_in_module(name, cached_module)
                    if found_func:
                        func_module = inspect.getmodule(found_func)
                        if func_module and not self._is_third_party_module(
                            func_module.__file__
                        ):
                            self._collect_function_and_deps(found_func)
                            break

            # Process variables
            for name in visitor.variables:
                if name in func.__globals__:
                    value = func.__globals__[name]
                    if not (
                        inspect.isfunction(value) or inspect.isclass(value)
                    ) and self._is_serializable_value(value):
                        self._collected_variables[name] = self._serialize_value(
                            name, value
                        )

        except (OSError, TypeError):
            pass

    def _get_ordered_functions(self) -> list[str]:
        """Get functions ordered by their dependencies."""
        if not self._main_function_name:
            return []

        # Create a mapping of function to its dependents
        dependents: dict[str, set[str]] = {
            name: set() for name in self._dependency_graph
        }
        for func, deps in self._dependency_graph.items():
            for dep in deps:
                if dep in dependents:
                    dependents[dep].add(func)

        # Start with functions that have no dependents
        ordered: list[str] = []
        visited: set[str] = set()

        def visit(func_name: str) -> None:
            if func_name in visited:
                return
            visited.add(func_name)
            # First visit all dependencies
            for dep in self._dependency_graph.get(func_name, set()):
                if dep in self._dependency_graph:  # Only visit user-defined functions
                    visit(dep)
            ordered.append(func_name)

        # Start with the main function to ensure we get all dependencies
        visit(self._main_function_name)
        return ordered

    def _get_code_location(self, func: Callable[..., Any]) -> _CodeLocation:
        """Get the location of a function's source code."""
        module = inspect.getmodule(func)
        if module is None:
            raise ValueError(f"Could not determine module for function {func.__name__}")

        module_path = module.__file__ or ""
        try:
            lines, start_line = inspect.getsourcelines(func)
            return _CodeLocation(module_path, start_line)
        except (OSError, TypeError):
            return _CodeLocation(module_path, -1)

    def _is_user_defined_import(self, import_stmt: str) -> bool:
        """Check if an import is for user-defined code."""
        if import_stmt.startswith("from typing import"):
            return True

        return not any(name in import_stmt for name in ["openai", "mirascope"])

    def _is_serializable_value(self, value: Any) -> bool:
        """Check if a value can be serializable."""
        return isinstance(value, int | float | str | bool | type(None))

    def _serialize_value(self, name: str, value: Any) -> str:
        """Serialize a value to a string."""
        return f"{name} = {repr(value)}"

    def _format_output(self) -> str:
        """Format the collected code into a single string."""
        parts = []

        # Add imports
        if self._collected_imports:
            parts.extend(sorted(self._collected_imports))
            parts.append("")

        # Add variables
        if self._collected_variables:
            parts.extend(sorted(self._collected_variables.values()))
            parts.append("")

        # Create a mapping from names to their source code
        name_to_source: dict[str, str] = {}
        for _, source in self._collected_code.items():
            tree = ast.parse(source)
            if isinstance(tree.body[0], ast.FunctionDef | ast.ClassDef):
                name_to_source[tree.body[0].name] = source

        ordered_classes = self._get_ordered_classes()
        for class_name in ordered_classes:
            if class_name in name_to_source:
                parts.append(name_to_source[class_name])
                parts.append("")

        ordered_functions = self._get_ordered_functions()
        for func_name in ordered_functions:
            if func_name in name_to_source:
                parts.append(name_to_source[func_name])
                parts.append("")

        return self._format_code("\n".join(parts).strip())


class _DependencyVisitor(ast.NodeVisitor):
    """AST visitor to collect dependencies from code."""

    def __init__(self) -> None:
        self.imports: set[str] = set()
        self.variables: set[str] = set()
        self.functions: set[str] = set()
        self.classes: set[str] = set()
        self._current_func: str | None = None

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        module = node.module or ""
        for name in node.names:
            import_stmt = f"from {module} import {name.name}"
            if name.asname:
                import_stmt += f" as {name.asname}"
            self.imports.add(import_stmt)
        self.generic_visit(node)

    def visit_Import(self, node: ast.Import) -> None:
        for name in node.names:
            import_stmt = f"import {name.name}"
            if name.asname:
                import_stmt += f" as {name.asname}"
            self.imports.add(import_stmt)
        self.generic_visit(node)

    def visit_Name(self, node: ast.Name) -> None:
        if isinstance(node.ctx, ast.Load) and node.id not in self.functions:
            # Only add to variables if it's not already marked as a function
            self.variables.add(node.id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visit type annotations in assignments."""
        self._extract_annotation_references(node.annotation)
        self.generic_visit(node)

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        prev_func = self._current_func
        self._current_func = node.name

        # Handle return annotation
        if node.returns:
            self._extract_annotation_references(node.returns)

        # Handle argument annotations
        for arg in node.args.args:
            if arg.annotation:
                self._extract_annotation_references(arg.annotation)

        # Handle decorators - collect any function calls within decorators
        for decorator in node.decorator_list:
            self._collect_decorator_calls(decorator)

        self.generic_visit(node)
        self._current_func = prev_func

    def _extract_annotation_references(self, node: ast.AST) -> None:
        """Extract class references from type annotations."""
        if isinstance(node, ast.Name):
            self.classes.add(node.id)
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                self.classes.add(node.value.id)
        elif isinstance(node, ast.Subscript):
            self._extract_annotation_references(node.value)
            self._extract_annotation_references(node.slice)
        self.generic_visit(node)

    def _collect_decorator_calls(self, node: ast.AST) -> None:
        """Collect function calls used in decorators."""
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                self.functions.add(node.func.id)
            elif isinstance(node.func, ast.Attribute) and isinstance(
                node.func.value, ast.Name
            ):
                self.variables.add(node.func.value.id)
            for arg in node.args:
                if isinstance(arg, ast.Name):
                    self.classes.add(arg.id)
                    self.variables.add(arg.id)
            for keyword in node.keywords:
                if isinstance(keyword.value, ast.Name):
                    self.classes.add(keyword.value.id)
                    self.variables.add(keyword.value.id)
        elif isinstance(node, ast.Name):
            self.functions.add(node.id)

    def visit_Call(self, node: ast.Call) -> None:
        """Visit a function call."""
        if isinstance(node.func, ast.Name):
            # Could be either a function call or a class instantiation
            # Add to both collections and let the collector determine which it is
            self.functions.add(node.func.id)
            self.classes.add(node.func.id)
            # Remove from variables if it was added there
            self.variables.discard(node.func.id)
        elif isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                self.variables.add(node.func.value.id)
                # Could be a class method or constructor
                self.classes.add(node.func.value.id)

        # Visit the arguments as they might contain class instantiations too
        for arg in node.args:
            if isinstance(arg, ast.Call):
                self.visit(arg)
            elif isinstance(arg, ast.Name):
                self.classes.add(arg.id)
                self.variables.add(arg.id)

        for keyword in node.keywords:
            if isinstance(keyword.value, ast.Call):
                self.visit(keyword.value)
            elif isinstance(keyword.value, ast.Name):
                self.classes.add(keyword.value.id)
                self.variables.add(keyword.value.id)

        self.generic_visit(node)


@lru_cache(maxsize=128)
def compute_closure(fn: Callable[..., Any]) -> tuple[str, str]:
    """Compute the closure of a function including all its dependencies.

    Args:
        fn: The function to analyze

    Returns:
        A tuple containing the (closure, hash) of the function.
    """
    collector = _DependencyCollector()
    closure = collector.collect(fn)
    closure_hash = hashlib.sha256(closure.encode("utf-8")).hexdigest()
    return closure, closure_hash


__all__ = ["compute_closure"]
