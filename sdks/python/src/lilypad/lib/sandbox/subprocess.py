"""Subprocess sandbox runner."""

import os
import tempfile
import subprocess
from typing import Any
from pathlib import Path

from . import SandboxRunner
from .runner import Result
from .._utils import Closure


class SubprocessSandboxRunner(SandboxRunner):
    """Runs code in a subprocess."""

    def __init__(self, environment: dict[str, str] | None = None) -> None:
        super().__init__(environment)
        if "PATH" not in self.environment:
            # Set uv path to the default value if not provided
            self.environment["PATH"] = os.environ["PATH"]

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
        script = self.generate_script(
            closure,
            *args,
            custom_result=custom_result,
            pre_actions=pre_actions,
            after_actions=after_actions,
            extra_imports=extra_imports,
            **kwargs,
        )
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
            tmp_file.write(script)
            tmp_path = Path(tmp_file.name)
        try:
            result = subprocess.run(
                ["uv", "run", "--no-project", str(tmp_path)],
                capture_output=True,
                text=False,
                env=self.environment,
            )

            return self.parse_execution_result(result.stdout, result.stderr, result.returncode)
        finally:
            tmp_path.unlink()
