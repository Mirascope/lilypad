"""Subprocess sandbox runner."""

import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from .._utils import Closure
from . import SandboxRunner


class SubprocessSandboxRunner(SandboxRunner):
    """Runs code in a subprocess."""

    def __init__(self, environment: dict[str, str] | None = None) -> None:
        super().__init__(environment)
        if "PATH" not in self.environment:
            # Set uv path to the default value if not provided
            self.environment["PATH"] = os.environ["PATH"]

    def execute_function(self, closure: Closure, *args: Any, **kwargs: Any) -> str:
        """Execute the function in the sandbox."""
        script = self.generate_script(closure, *args, **kwargs)
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
