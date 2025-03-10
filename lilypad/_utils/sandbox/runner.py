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
    def execute_function(self, _closure: Closure, *args: Any, **kwargs: Any) -> str: ...

    """Execute the function in the sandbox."""

    @classmethod
    def _is_async_func(cls, closure: Closure) -> bool:
        lines = closure.signature.splitlines()
        return any(
            line.strip() for line in lines if line.strip().startswith("async def ")
        )

    @classmethod
    def _generate_async_run(cls, _closure: Closure, *args: Any, **kwargs: Any) -> str:
        return inspect.cleandoc("""
                import asyncio
                    result = asyncio.run({name}(*{args}, **{kwargs}))
                """).format(name=_closure.name, args=args, kwargs=kwargs)

    @classmethod
    def _generate_sync_run(cls, _closure: Closure, *args: Any, **kwargs: Any) -> str:
        return inspect.cleandoc("""
                    result = {name}(*{args}, **{kwargs})
                """).format(name=_closure.name, args=args, kwargs=kwargs)

    @classmethod
    def generate_script(cls, _closure: Closure, *args: Any, **kwargs: Any) -> str:
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
                    for key, value in _closure.dependencies.items()
                ]
            ),
            code=_closure.code,
            result=cls._generate_async_run(_closure, *args, **kwargs)
            if cls._is_async_func(_closure)
            else cls._generate_sync_run(_closure, *args, **kwargs),
        )


SandboxRunnerT = TypeVar("SandboxRunnerT", bound=SandboxRunner)
