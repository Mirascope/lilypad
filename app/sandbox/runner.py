"""This module contains the SandboxRunner abstract base class."""

import inspect
from abc import ABC, abstractmethod
from typing import Any, TypeVar

from lilypad._utils import Closure


class SandboxRunner(ABC):
    """Abstract base class for executing code in a sandbox.

    Subclasses must implement the execute_function method.
    """

    def __init__(self, environment: dict[str, str] | None = None) -> None:
        self.environment: dict[str, str] = environment or {}

    @abstractmethod
    def execute_function(self, closure: Closure, *args: Any, **kwargs: Any) -> str:
        """Execute the function in the sandbox."""
        ...

    @classmethod
    def _is_async_func(cls, closure: Closure) -> bool:
        lines = closure.signature.splitlines()
        return any(
            line.strip() for line in lines if line.strip().startswith("async def ")
        )

    @classmethod
    def _generate_async_run(cls, closure: Closure, *args: Any, **kwargs: Any) -> str:
        return inspect.cleandoc("""
                import asyncio
                    result = asyncio.run({name}(*{args}, **{kwargs}))
                """).format(name=closure.name, args=args, kwargs=kwargs)

    @classmethod
    def _generate_sync_run(cls, closure: Closure, *args: Any, **kwargs: Any) -> str:
        return inspect.cleandoc("""
                    result = {name}(*{args}, **{kwargs})
                """).format(name=closure.name, args=args, kwargs=kwargs)

    @classmethod
    def generate_script(cls, closure: Closure, *args: Any, **kwargs: Any) -> str:
        """Generate a script that executes the function in the sandbox."""
        return inspect.cleandoc("""
                # /// script
                # dependencies = [
                #   {dependencies}
                # ]
                # ///

                {code}


                if __name__ == "__main__":
                    import json
                    {result}
                    print(json.dumps(result))
                """).format(
            dependencies=",\n#   ".join(
                [
                    f'"{key}[{",".join(extras)}]=={value["version"]}"'
                    if (extras := value["extras"])
                    else f'"{key}=={value["version"]}"'
                    for key, value in closure.dependencies.items()
                ]
            ),
            code=closure.code,
            result=cls._generate_async_run(closure, *args, **kwargs)
            if cls._is_async_func(closure)
            else cls._generate_sync_run(closure, *args, **kwargs),
        )


SandboxRunnerT = TypeVar("SandboxRunnerT", bound=SandboxRunner)
