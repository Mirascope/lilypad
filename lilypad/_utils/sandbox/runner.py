import inspect
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from lilypad._utils import Closure


class SandboxRunner(ABC):
    """Abstract base class for executing code in a sandbox.

    Subclasses must implement the execute_function method.
    """

    def __init__(
        self, closure: Closure, environment: dict[str, str] | None = None
    ) -> None:
        self.closure: Closure = closure
        self.environment: dict[str, str] = environment or {}

    @abstractmethod
    def execute_function(self, *args: Any, **kwargs: Any) -> str: ...

    """Execute the function in the sandbox."""

    def _is_async_func(self) -> bool:
        lines = self.closure.signature.splitlines()
        return any(
            line.strip() for line in lines if line.strip().startswith("async def ")
        )

    def _generate_async_run(self, *args: Any, **kwargs: Any) -> str:
        return inspect.cleandoc("""
                import asyncio
                    result = asyncio.run({name}(*{args}, **{kwargs}))
                """).format(name=self.closure.name, args=args, kwargs=kwargs)

    def _generate_sync_run(self, *args: Any, **kwargs: Any) -> str:
        return inspect.cleandoc("""
                    result = {name}(*{args}, **{kwargs})
                """).format(name=self.closure.name, args=args, kwargs=kwargs)

    def generate_script(self, *args: Any, **kwargs: Any) -> str:
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
                    for key, value in self.closure.dependencies.items()
                ]
            ),
            code=self.closure.code,
            result=self._generate_async_run(*args, **kwargs)
            if self._is_async_func()
            else self._generate_sync_run(*args, **kwargs),
        )


SandBoxRunnerT = TypeVar("SandBoxRunnerT", bound=SandboxRunner)


class SandBoxFactory(Generic[SandBoxRunnerT], ABC):
    """Abstract base class for creating sandbox runners."""

    def __init__(self, environment: dict[str, str] | None = None) -> None:
        self.environment: dict[str, str] = environment or {}

    @abstractmethod
    def create(self, closure: Closure) -> SandBoxRunnerT: ...
