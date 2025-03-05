import inspect
from abc import ABC, abstractmethod
from typing import Any

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
                    result = {name}(*{args}, **{kwargs})
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
            name=self.closure.name,
            args=args,
            kwargs=kwargs,
        )
