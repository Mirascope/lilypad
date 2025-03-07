import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .. import Closure
from . import SandBoxFactory, SandboxRunner


class SubprocessSandboxRunner(SandboxRunner):
    """Runs code in a subprocess."""

    def __init__(
        self, closure: Closure, environment: dict[str, str] | None = None
    ) -> None:
        super().__init__(closure, environment)
        if "PATH" not in self.environment:
            # Set uv path to the default value if not provided
            self.environment["PATH"] = os.environ["PATH"]

    def execute_function(self, *args: Any, **kwargs: Any) -> str:
        script = self.generate_script(*args, **kwargs)
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
                env=self.environment,
            )
            return json.loads(result.stdout.strip())
        except subprocess.CalledProcessError as e:
            error_message = (
                f"Process exited with non-zero status.\n"
                f"Stdout: {e.stdout}\n"
                f"Stderr: {e.stderr}"
            )
            raise RuntimeError(error_message)
        finally:
            tmp_path.unlink()


class SubprocessSandboxFactory(SandBoxFactory[SubprocessSandboxRunner]):
    """Creates subprocess sandbox runners."""

    def __init__(self, environment: dict[str, str] | None = None) -> None:
        if environment is None:
            environment = os.environ.copy()
        super().__init__(environment)

    def create(self, closure: Closure) -> SubprocessSandboxRunner:
        return SubprocessSandboxRunner(closure, self.environment)
