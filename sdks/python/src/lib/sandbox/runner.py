"""This module contains the SandboxRunner abstract base class."""

import inspect
from abc import ABC, abstractmethod
from typing import Any, TypeVar, cast
from typing_extensions import TypedDict

import orjson

from .._utils import Closure


class DependencyError(Exception):
    """Represents an error caused by missing or incompatible dependencies."""

    def __init__(self, message: str, module_name: str = None, error_class: str = None):
        self.message = message
        self.module_name = module_name
        self.error_class = error_class
        super().__init__(f"Dependency error: {message}")


class Result(TypedDict, total=False):
    """Result of executing a function in a sandbox."""

    result: Any


class SandboxRunner(ABC):
    """Abstract base class for executing code in a sandbox.

    Subclasses must implement the execute_function method.
    """

    def __init__(self, environment: dict[str, str] | None = None) -> None:
        self.environment: dict[str, str] = environment or {}

    @abstractmethod
    def execute_function(
        self,
        closure: Closure,
        *args: Any,
        custom_result: dict[str, str] | None = None,
        pre_actions: list[str] | None = None,
        after_actions: list[str] | None = None,
        extra_imports: list[str] | None = None,
        **kwargs: Any,
    ) -> Result:
        """Execute the function in the sandbox."""
        ...

    @classmethod
    def _is_async_func(cls, closure: Closure) -> bool:
        lines = closure.signature.splitlines()
        return any(line.strip() for line in lines if line.strip().startswith("async def "))

    @classmethod
    def parse_execution_result(cls, stdout: bytes, stderr: bytes, returncode: int) -> Result:
        """Parse the execution result from stdout, stderr, and return code."""
        try:
            data = orjson.loads(stdout.strip())

            if returncode == 0:
                return cast(Result, data)

            if isinstance(data, dict) and "error_type" in data:
                if data.get("is_dependency_error", False) or data["error_type"] in [
                    "ImportError",
                    "ModuleNotFoundError",
                ]:
                    raise DependencyError(
                        message=data.get("error_message", "Unknown dependency error"),
                        module_name=data.get("module_name"),
                        error_class=data.get("error_type"),
                    )
        except orjson.JSONDecodeError:
            pass

        if returncode != 0:
            error_message = f"Process exited with non-zero status.\nStdout: {stdout.decode(errors='replace')}\nStderr: {stderr.decode(errors='replace')}"
            raise RuntimeError(error_message)

        return cast(Result, orjson.loads(stdout.strip()))

    @classmethod
    def generate_script(
        cls,
        closure: Closure,
        *args: Any,
        custom_result: dict[str, str] | None = None,
        pre_actions: list[str] | None = None,
        after_actions: list[str] | None = None,
        extra_imports: list[str] | None = None,
        **kwargs: Any,
    ) -> str:
        """Generate a script that executes the function in the sandbox."""
        if custom_result:
            result_content = "{" + ", ".join(f'"{k}": ({v})' for k, v in custom_result.items()) + "}"
        else:
            result_content = '{"result": result}'

        base_run = "{name}(*{args}, **{kwargs})".format(name=closure.name, args=args, kwargs=kwargs)

        is_async = cls._is_async_func(closure)
        if is_async:
            extra_imports = extra_imports or []
            extra_imports.append("import asyncio")
            result_code = inspect.cleandoc("""
            async def main():
                    result = await {base_run}
                    {after_actions}
                    return {result_content}
                result = asyncio.run(main())
            """).format(
                base_run=base_run,
                result_content=result_content,
                after_actions="\n        ".join(after_actions) if after_actions else "",
            )
        else:
            result_code = inspect.cleandoc("""
            def main():
                    result = {base_run}
                    {after_actions}
                    return {result_content}
                result = main()
            """).format(
                base_run=base_run,
                result_content=result_content,
                after_actions="\n        ".join(after_actions) if after_actions else "",
            )

        dependencies_str = ",\n#   ".join(
            [
                f'"{key}[{",".join(extras)}]=={value["version"]}"'
                if (extras := value["extras"])
                else f'"{key}=={value["version"]}"'
                for key, value in closure.dependencies.items()
            ]
        )

        error_handler = """
    try:
        {code}
        
        {extra_imports}
        {pre_actions}
        {result}
        print(json.dumps(result))
    except ImportError as e:
        import traceback
        error_info = {{
            "error_type": "ImportError",
            "error_message": str(e),
            "is_dependency_error": True,
            "module_name": getattr(e, "name", None),
            "traceback": traceback.format_exc()
        }}
        print(json.dumps(error_info))
        sys.exit(1)
    except ModuleNotFoundError as e:
        import traceback
        error_info = {{
            "error_type": "ModuleNotFoundError",
            "error_message": str(e),
            "is_dependency_error": True,
            "module_name": getattr(e, "name", None),
            "traceback": traceback.format_exc()
        }}
        print(json.dumps(error_info))
        sys.exit(1)
    except Exception as e:
        import traceback
        error_info = {{
            "error_type": e.__class__.__name__,
            "error_message": str(e),
            "traceback": traceback.format_exc()
        }}
        print(json.dumps(error_info))
        sys.exit(1)
        """.format(
            code="\n        ".join(closure.code.splitlines()),
            extra_imports="\n        ".join(extra_imports) if extra_imports else "",
            pre_actions="\n        ".join(pre_actions) if pre_actions else "",
            result="\n    ".join(result_code.splitlines()),
        )

        return inspect.cleandoc(f"""
# /// script
# dependencies = [
#   {dependencies_str}
# ]
# ///


if __name__ == "__main__":
    import json
    import sys
{error_handler}
""")


SandboxRunnerT = TypeVar("SandboxRunnerT", bound=SandboxRunner)
