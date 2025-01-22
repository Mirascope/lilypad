"""The `Closure` class."""

from __future__ import annotations

import ast
import hashlib
import importlib.metadata
import importlib.util
import inspect
import io
import json
import os
import site
import subprocess
import sys
import tempfile
import tokenize
from collections.abc import Callable
from functools import cached_property, lru_cache
from pathlib import Path
from textwrap import dedent
from types import ModuleType
from typing import Any, cast

from packaging.requirements import Requirement
from pydantic import BaseModel
from typing_extensions import TypedDict


class DependencyInfo(TypedDict):
    version: str
    extras: list[str] | None


def _is_third_party(module: ModuleType, site_packages: set[str]) -> bool:
    module_file = getattr(module, "__file__", None)
    return (
        module.__name__ == "lilypad"  # always consider lilypad as third-party
        or module.__name__ in sys.stdlib_module_names
        or module_file is None
        or any(
            str(Path(module_file).resolve()).startswith(site_pkg)
            for site_pkg in site_packages
        )
    )


def _convert_embedded_newlines_to_triple_quoted(code: str) -> str:
    """Convert single/double-quoted string tokens containing actual newlines
    into triple-quoted strings. If the token is already triple-quoted, it is unchanged.
    """
    tokens = list(tokenize.generate_tokens(io.StringIO(code).readline))
    new_tokens = []

    for tok_type, tok_string, _start, _end, _line_text in tokens:
        if tok_type == tokenize.STRING:
            # If it's already triple-quoted, leave it as is.
            if tok_string.startswith(('"""', "'''", 'r"""', 'r"""', 'R"""', "R'''")):
                new_tokens.append((tok_type, tok_string))
            else:
                # If it looks like an f-string, skip ast.literal_eval since it won't parse.
                if tok_string.startswith(('f"', "f'", 'f"""', "f''''")):
                    new_tokens.append((tok_type, tok_string))
                    continue

                # For normal string literals, parse and check for newlines.
                val = ast.literal_eval(tok_string)
                if "\n" in val:
                    triple_str = f'"""{val}"""'
                    new_tokens.append((tok_type, triple_str))
                else:
                    new_tokens.append((tok_type, tok_string))
        else:
            new_tokens.append((tok_type, tok_string))

    return tokenize.untokenize(new_tokens)


def _clean_source_code(
    fn: Callable[..., Any] | type,
    *,
    exclude_fn_body: bool = False,
) -> str:
    """Removes true docstrings from the given function/class definition, while preserving
    code-like “docstrings” that appear to contain real Python statements.

    - If the first statement in the body is a string token:
      - If it "looks like code" (def/class/from/import/@, etc.), keep it.
      - Else treat it as a docstring and remove it.
      - If removing leaves no statements in the body, insert `pass`.
    - Optionally truncate the body if `exclude_fn_body=True`.
    - Convert multi-line strings into triple-quoted strings.
    """
    # 1) Grab and dedent the source
    source = dedent(inspect.getsource(fn))

    # 2) Tokenize
    orig_tokens = list(tokenize.generate_tokens(io.StringIO(source).readline))
    new_tokens: list[tokenize.TokenInfo] = []

    found_def_or_class = False
    found_colon = False
    in_body = False
    docstring_removed = False
    body_tokens: list[tokenize.TokenInfo] = []

    for _i, tok in enumerate(orig_tokens):
        tok_type, tok_string, start, end, line_text = tok

        # 2a) Detect "async def", "def", or "class"
        if not found_def_or_class:
            if tok_type == tokenize.NAME and tok_string in ("async", "def", "class"):
                found_def_or_class = True
            new_tokens.append(tok)
            continue

        # 2b) We found a def/class, but haven't seen its colon yet
        if found_def_or_class and not found_colon:
            new_tokens.append(tok)
            if tok_type == tokenize.OP and tok_string == ":":
                found_colon = True
            continue

        # 2c) Once we have def/class(...) and a colon, the next INDENT means the body starts
        if found_colon and not in_body:
            new_tokens.append(tok)
            if tok_type == tokenize.INDENT:
                in_body = True
            continue

        # 2d) Now we are inside the *first* def/class body. We'll store these tokens in `body_tokens`.
        # We will handle removing the docstring after collecting them.
        body_tokens.append(tok)

    # If we never found a def/class, nothing special to remove
    if not found_def_or_class:
        # Rejoin tokens, done
        cleaned_source = tokenize.untokenize(new_tokens)
    else:
        # We have `new_tokens` for everything up to (and including) the body INDENT.
        # Next, we remove the docstring if the first statement is a string, unless it looks like code.

        # 3) Identify the first statement in `body_tokens`.
        #    If it's a standalone STRING, check if it's code-like or not.
        # We'll parse body_tokens carefully to see if the first non-(NL, NEWLINE, INDENT, DEDENT)
        # token is a STRING.
        idx = 0
        skip_tokens: list[tokenize.TokenInfo] = []
        while idx < len(body_tokens):
            ttype, tstring, *_ = body_tokens[idx]
            if ttype in (
                tokenize.NL,
                tokenize.NEWLINE,
                tokenize.INDENT,
                tokenize.DEDENT,
            ):
                skip_tokens.append(body_tokens[idx])
                idx += 1
                continue
            # The first real body token
            if ttype == tokenize.STRING:
                docstring_removed = True
                idx += 1
            break  # we only handle the first real statement

        # Now re-add the remainder
        rest_tokens = body_tokens[idx:]

        # 4) If docstring removed, we need to ensure there's still content in rest_tokens
        #    If there's no statements left except maybe indentation or newlines,
        #    we'll insert a `pass` or `...` to keep the function valid.
        # Let's see if we have real code in the remainder.
        # We'll filter out (NL, NEWLINE, DEDENT, INDENT) for the remainder
        real_code_tokens = [
            t
            for t in rest_tokens
            if t.type
            not in (tokenize.NL, tokenize.NEWLINE, tokenize.INDENT, tokenize.DEDENT)
        ]
        if docstring_removed and len(real_code_tokens) == 0:
            # Insert a `pass` statement at the correct indentation
            # We'll guess the indentation from the first line in rest_tokens or skip_tokens
            indent_str = ""
            # find a token with type=INDENT if possible
            # new_tokens should contain the last known indent from the definition
            # We'll see if the last token in new_tokens was an INDENT
            if new_tokens and new_tokens[-1].type == tokenize.INDENT:
                indent_str = new_tokens[-1].string

            # We'll insert a pass token
            pass_line = f"{indent_str}pass\n"
            skip_tokens.append(
                tokenize.TokenInfo(tokenize.NAME, "pass", (0, 0), (0, 0), pass_line)
            )
            skip_tokens.append(
                tokenize.TokenInfo(tokenize.NEWLINE, "\n", (0, 0), (0, 0), pass_line)
            )

        # 5) Now combine them back: new_tokens + skip_tokens + rest_tokens
        combined = new_tokens + skip_tokens + rest_tokens
        cleaned_source = tokenize.untokenize(combined)

    # If exclude_fn_body=True, we only keep the signature up to the first ':\n'
    if exclude_fn_body and (idx := cleaned_source.find(":\n")) != -1:
        cleaned_source = cleaned_source[: idx + 2]

    # Trim trailing whitespace
    cleaned_source = cleaned_source.rstrip()

    # If it ends with ':', add ' ...' to avoid IndentationError on a blank body
    if cleaned_source.endswith(":"):
        cleaned_source += " ..."

    # Convert multi-line strings to triple-quoted
    cleaned_source = _convert_embedded_newlines_to_triple_quoted(cleaned_source)

    # If it ends with '\', add ' ...' to avoid SyntaxError on a blank body
    if cleaned_source.endswith("\\"):
        cleaned_source = cleaned_source[:-1] + " ..."
    return cleaned_source


class _NameCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.used_names: list[str] = []

    def visit_Name(self, node: ast.Name) -> None:
        self.used_names.append(node.id)

    def visit_Call(self, node: ast.Call) -> None:
        if isinstance(node.func, ast.Name):
            self.used_names.append(node.func.id)
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute) -> None:
        names = []
        current = node
        while True:
            if isinstance(current, ast.Attribute):
                names.append(current.attr)
                current = current.value
            elif isinstance(current, ast.Call):
                current = current.func
            else:
                break
        if isinstance(current, ast.Name):
            names.append(current.id)
            full_path = ".".join(reversed(names))
            self.used_names.append(full_path)
            self.used_names.append(names[-1])


class _ImportCollector(ast.NodeVisitor):
    def __init__(self, used_names: list[str], site_packages: set[str]) -> None:
        self.imports: set[str] = set()
        self.user_defined_imports: set[str] = set()
        self.used_names = used_names
        self.site_packages = site_packages
        self.alias_map: dict[str, str] = {}

    def visit_Import(self, node: ast.Import) -> None:
        for name in node.names:
            module_name = name.name.split(".")[0]
            module = __import__(module_name)
            import_name = name.asname or module_name
            is_used = import_name in self.used_names or any(
                u.startswith(f"{import_name}.") for u in self.used_names
            )
            if is_used:
                import_stmt = (
                    f"import {name.name} as {name.asname}"
                    if name.asname
                    else f"import {name.name}"
                )
                if name.asname:
                    self.alias_map[name.asname] = import_stmt

                if _is_third_party(module, self.site_packages):
                    self.imports.add(import_stmt)
                else:
                    self.user_defined_imports.add(import_stmt)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if not (module := node.module):
            return
        try:
            is_third_party = _is_third_party(
                __import__(module.split(".")[0]), self.site_packages
            )
        except ImportError:
            module = "." * node.level + module
            is_third_party = False
        for name in node.names:
            import_name = name.asname or name.name
            is_used = import_name in self.used_names or any(
                u.startswith(f"{import_name}.") for u in self.used_names
            )
            if is_used:
                if name.asname:
                    import_stmt = f"from {module} import {name.name} as {name.asname}"
                    self.alias_map[name.asname] = import_stmt
                else:
                    import_stmt = f"from {module} import {name.name}"

                if is_third_party:
                    self.imports.add(import_stmt)
                else:
                    self.user_defined_imports.add(import_stmt)


class _LocalAssignmentCollector(ast.NodeVisitor):
    def __init__(self) -> None:
        self.assignments: set[str] = set()

    def visit_Assign(self, node: ast.Assign) -> None:
        if isinstance(node.targets[0], ast.Name):
            self.assignments.add(node.targets[0].id)
        self.generic_visit(node)

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if isinstance(node.target, ast.Name):
            self.assignments.add(node.target.id)
        self.generic_visit(node)


class _GlobalAssignmentCollector(ast.NodeVisitor):
    def __init__(self, used_names: list[str]) -> None:
        self.used_names = used_names
        self.assignments: list[str] = []
        self.current_function = None

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        old_function = self.current_function
        self.current_function = node
        self.generic_visit(node)
        self.current_function = old_function

    def visit_Assign(self, node: ast.Assign) -> None:
        if self.current_function is not None:
            return
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in self.used_names:
                self.assignments.append(ast.unparse(node))

    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        if self.current_function is not None:
            return
        if isinstance(node.target, ast.Name) and node.target.id in self.used_names:
            self.assignments.append(ast.unparse(node))


class _DefinitionCollector(ast.NodeVisitor):
    def __init__(
        self, module: ModuleType, used_names: list[str], site_packages: set[str]
    ) -> None:
        self.module = module
        self.used_names = used_names
        self.site_packages = site_packages
        self.definitions_to_include: list[Callable[..., Any] | type] = []
        self.definitions_to_analyze: list[Callable[..., Any] | type] = []
        self.imports: set[str] = set()

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        for decorator_node in node.decorator_list:
            if isinstance(decorator_node, ast.Name):
                if decorator_func := getattr(self.module, decorator_node.id, None):
                    self.definitions_to_include.append(decorator_func)
            elif isinstance(decorator_node, ast.Attribute):
                names = []
                current = decorator_node
                while isinstance(current, ast.Attribute):
                    names.append(current.attr)
                    current = current.value
                if isinstance(current, ast.Name):
                    names.append(current.id)
                    full_path = ".".join(reversed(names))
                    if (
                        full_path in self.used_names
                        and (decorator_module := getattr(self.module, names[-1], None))
                        and (definition := getattr(decorator_module, names[0], None))
                    ):
                        self.definitions_to_include.append(definition)
        if nested_func := getattr(self.module, node.name, None):
            self.definitions_to_analyze.append(nested_func)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        if class_def := getattr(self.module, node.name, None):
            self.definitions_to_analyze.append(class_def)
            for item in node.body:
                if isinstance(item, ast.FunctionDef) and (
                    definition := getattr(class_def, item.name, None)
                ):
                    self.definitions_to_analyze.append(definition)
        self.generic_visit(node)

    def _process_name_or_attribute(self, node: ast.AST) -> None:
        if isinstance(node, ast.Name):
            if (obj := getattr(self.module, node.id, None)) and hasattr(
                obj, "__name__"
            ):
                self.definitions_to_include.append(obj)
        elif isinstance(node, ast.Attribute):
            names = []
            current = node
            while isinstance(current, ast.Attribute):
                names.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                names.append(current.id)
                full_path = ".".join(reversed(names))
                if (
                    full_path in self.used_names
                    and (definition := getattr(self.module, names[0], None))
                    and hasattr(definition, "__name__")
                ):
                    self.definitions_to_include.append(definition)

    def visit_Call(self, node: ast.Call) -> None:
        self._process_name_or_attribute(node.func)
        for arg in node.args:
            self._process_name_or_attribute(arg)
        for keyword in node.keywords:
            self._process_name_or_attribute(keyword.value)
        self.generic_visit(node)


class _QualifiedNameRewriter(ast.NodeTransformer):
    def __init__(self, local_names: set[str], user_defined_imports: set[str]) -> None:
        self.local_names = local_names
        self.alias_mapping = {}
        for import_stmt in user_defined_imports:
            if import_stmt.startswith("from "):
                parts = import_stmt.split(" ")
                if len(parts) >= 4 and "as" in parts:
                    original_name = parts[parts.index("import") + 1]
                    alias = parts[parts.index("as") + 1]
                    self.alias_mapping[alias] = original_name

    def visit_Attribute(self, node: ast.Attribute) -> ast.AST:
        names = []
        current = node
        while isinstance(current, ast.Attribute):
            names.append(current.attr)
            current = current.value
        if isinstance(current, ast.Name) and current.id not in ["self", "cls"]:
            names.append(current.id)
            if names[0] in self.local_names:
                return ast.Name(id=names[0], ctx=node.ctx)
        return node

    def visit_Name(self, node: ast.Name) -> ast.AST:
        if node.id in self.alias_mapping:
            return ast.Name(id=self.alias_mapping[node.id], ctx=node.ctx)
        return node


class _DependencyCollector:
    """Collects all dependencies for a function."""

    def __init__(self) -> None:
        self.imports: set[str] = set()
        self.fn_internal_imports: set[str] = set()
        self.user_defined_imports: set[str] = set()
        self.assignments: list[str] = []
        self.source_code: list[str] = []
        self.visited_functions: set[str] = set()
        self.site_packages: set[str] = {
            str(Path(p).resolve()) for p in site.getsitepackages()
        }
        self._last_import_collector: _ImportCollector | None = None

    def _collect_assignments_and_imports(
        self,
        fn_tree: ast.Module,
        module_tree: ast.Module,
        used_names: list[str],
    ) -> None:
        local_assignment_collector = _LocalAssignmentCollector()
        local_assignment_collector.visit(fn_tree)
        local_assignments = local_assignment_collector.assignments

        global_assignment_collector = _GlobalAssignmentCollector(used_names)
        global_assignment_collector.visit(module_tree)

        for global_assignment in global_assignment_collector.assignments:
            tree = ast.parse(global_assignment)
            stmt = cast(ast.Assign | ast.AnnAssign, tree.body[0])
            if isinstance(stmt, ast.Assign):
                var_name = cast(ast.Name, stmt.targets[0]).id
            else:
                var_name = cast(ast.Name, stmt.target).id

            if var_name not in used_names or var_name in local_assignments:
                continue

            self.assignments.append(global_assignment)

            name_collector = _NameCollector()
            name_collector.visit(tree)
            import_collector = _ImportCollector(
                name_collector.used_names, self.site_packages
            )
            import_collector.visit(module_tree)
            self.imports.update(import_collector.imports)
            self.user_defined_imports.update(import_collector.user_defined_imports)

    def _collect_imports_and_source_code(
        self, definition: Callable[..., Any] | type, include_source: bool
    ) -> None:
        try:
            if isinstance(definition, property):
                if definition.fget is None:
                    return
                definition = definition.fget

            elif isinstance(definition, cached_property):
                definition = definition.func
            if definition.__name__ in self.visited_functions:
                return
            self.visited_functions.add(definition.__name__)

            module = inspect.getmodule(definition)
            if not module or _is_third_party(module, self.site_packages):
                return

            source = _clean_source_code(definition)
            module_source = inspect.getsource(module)
            module_tree = ast.parse(module_source)
            fn_tree = ast.parse(source)

            name_collector = _NameCollector()
            name_collector.visit(fn_tree)
            used_names = list(dict.fromkeys(name_collector.used_names))

            import_collector = _ImportCollector(used_names, self.site_packages)
            import_collector.visit(module_tree)
            new_imports: set[str] = {
                import_stmt
                for import_stmt in import_collector.imports
                if import_stmt not in source
            }
            self.imports.update(new_imports)
            self.fn_internal_imports.update(import_collector.imports - new_imports)
            self.user_defined_imports.update(import_collector.user_defined_imports)

            if include_source:
                for user_defined_import in self.user_defined_imports:
                    source = source.replace(user_defined_import, "")
                self.source_code.insert(0, source)

            self._collect_assignments_and_imports(fn_tree, module_tree, used_names)
            definition_collector = _DefinitionCollector(
                module, used_names, self.site_packages
            )
            definition_collector.visit(fn_tree)
            for collected_definition in definition_collector.definitions_to_include:
                self._collect_imports_and_source_code(collected_definition, True)
            for collected_definition in definition_collector.definitions_to_analyze:
                self._collect_imports_and_source_code(collected_definition, False)

        except (OSError, TypeError):  # pragma: no cover
            pass

    def _collect_required_dependencies(
        self, imports: set[str]
    ) -> dict[str, DependencyInfo]:
        stdlib_modules = set(sys.stdlib_module_names)
        installed_packages = {
            dist.name: dist for dist in importlib.metadata.distributions()
        }
        import_to_dist = importlib.metadata.packages_distributions()

        dependencies = {}
        for import_stmt in imports:
            parts = import_stmt.strip().split()
            root_module = parts[1].split(".")[0]
            if root_module in stdlib_modules:
                continue

            dist_names = import_to_dist.get(root_module, [root_module])
            for dist_name in dist_names:
                # only >= 3.12 properly discovers this in testing due to structure
                if dist_name == "lilypad":  # pragma: no cover
                    dist_name = "python-lilypad"
                if dist_name not in installed_packages:  # pragma: no cover
                    continue
                dist = installed_packages[dist_name]
                extras = []
                for extra in dist.metadata.get_all("Provides-Extra", []):
                    extra_reqs = dist.requires or []
                    extra_deps = [
                        Requirement(r).name
                        for r in extra_reqs
                        if f"extra == '{extra}'" in r
                    ]
                    if extra_deps and all(
                        dep in installed_packages for dep in extra_deps
                    ):
                        extras.append(extra)

                dependencies[dist.name] = {
                    "version": dist.version,
                    "extras": extras if extras else None,
                }

        return dependencies

    @classmethod
    def _map_child_to_parent(
        cls,
        child_to_parent: dict[ast.AST, ast.AST | None],
        node: ast.AST,
        parent: ast.AST | None = None,
    ) -> None:
        child_to_parent[node] = parent
        for _field, value in ast.iter_fields(node):
            if isinstance(value, list):
                for child in value:
                    if isinstance(child, ast.AST):
                        cls._map_child_to_parent(child_to_parent, child, node)
            elif isinstance(value, ast.AST):
                cls._map_child_to_parent(child_to_parent, value, node)

    def collect(
        self, fn: Callable[..., Any]
    ) -> tuple[list[str], list[str], list[str], dict[str, DependencyInfo]]:
        """Returns the imports and source code for a function and its dependencies."""
        self._collect_imports_and_source_code(fn, True)

        local_names = set()
        for code in self.source_code + self.assignments:
            tree = ast.parse(code)

            child_to_parent = {}

            self._map_child_to_parent(child_to_parent, tree)

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef | ast.ClassDef):
                    parent = child_to_parent.get(node)
                    if isinstance(parent, ast.Module):
                        local_names.add(node.name)

        rewriter = _QualifiedNameRewriter(local_names, self.user_defined_imports)

        assignments = []
        for code in self.assignments:
            tree = ast.parse(code)
            new_tree = rewriter.visit(tree)
            assignments.append(ast.unparse(new_tree))

        source_code = []
        for code in self.source_code:
            tree = ast.parse(code)
            new_tree = rewriter.visit(tree)
            unparsed = ast.unparse(new_tree)
            unparsed = _convert_embedded_newlines_to_triple_quoted(unparsed)
            source_code.append(unparsed)

        required_dependencies = self._collect_required_dependencies(
            self.imports | self.fn_internal_imports
        )

        return (
            list(self.imports),
            list(dict.fromkeys(assignments)),
            source_code,
            required_dependencies,
        )


def _run_ruff(code: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
        tmp_file.write(code)
        tmp_path = Path(tmp_file.name)

    try:
        subprocess.run(
            ["ruff", "check", "--isolated", "--select=I", "--fix", str(tmp_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        subprocess.run(
            ["ruff", "format", "--isolated", "--line-length=88", str(tmp_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        processed_code = tmp_path.read_text()
        return processed_code
    finally:
        tmp_path.unlink()


class Closure(BaseModel):
    """Represents the closure of a function."""

    name: str
    signature: str
    code: str
    hash: str
    dependencies: dict[str, DependencyInfo]

    @classmethod
    @lru_cache(maxsize=128)
    def from_fn(cls, fn: Callable[..., Any]) -> Closure:
        """Create a closure from a function.

        Args:
            fn: The function to analyze

        Returns:
            Closure: The closure of the function.
        """
        collector = _DependencyCollector()
        imports, assignments, source_code, dependencies = collector.collect(fn)
        code = "{imports}\n\n{assignments}\n\n{source_code}".format(
            imports="\n".join(imports),
            assignments="\n".join(assignments),
            source_code="\n\n".join(source_code),
        )
        formatted_code = _run_ruff(code)
        hash = hashlib.sha256(formatted_code.encode("utf-8")).hexdigest()
        return cls(
            name=fn.__name__,
            signature=_run_ruff(_clean_source_code(fn, exclude_fn_body=True)).strip(),
            code=formatted_code,
            hash=hash,
            dependencies=dependencies,
        )

    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Run the closure."""
        script = inspect.cleandoc("""
        # /// script
        # dependencies = [
        #   {dependencies}
        # ]
        # ///

        {code}


        if __name__ == "__main__":
            import json
            result = {name}(*{args}, **{kwargs})
            print(json.dumps(result))
        """).format(
            dependencies="\n#   ".join(
                [
                    f'"{key}[{",".join(extras)}]=={value["version"]}"'
                    if (extras := value["extras"])
                    else f'"{key}=={value["version"]}"'
                    for key, value in self.dependencies.items()
                ]
            ),
            code=self.code,
            name=self.name,
            args=args,
            kwargs=kwargs,
        )
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False
        ) as tmp_file:
            tmp_file.write(script)
            tmp_path = Path(tmp_file.name)
        try:
            result = subprocess.run(
                ["uv", "run", str(tmp_path)],
                check=True,
                capture_output=True,
                text=True,
                env=os.environ,
            )
            return json.loads(result.stdout.strip())
        finally:
            tmp_path.unlink()


__all__ = ["Closure"]
