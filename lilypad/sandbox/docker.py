"""Docker sandbox runner."""

import io
import json
import tarfile
from contextlib import suppress
from typing import Any

import docker

from .._utils import Closure
from . import SandboxRunner

_DEFAULT_IMAGE = "ghcr.io/astral-sh/uv:python3.10-alpine"


class DockerSandboxRunner(SandboxRunner):
    """Runs code in a Docker container."""

    def __init__(
        self,
        image: str = _DEFAULT_IMAGE,
        environment: dict[str, str] | None = None,
    ) -> None:
        super().__init__(environment)
        self.image = image

    @classmethod
    def _create_tar_stream(cls, files: dict[str, str]) -> io.BytesIO:
        """Creates a tar stream from a dictionary of files."""
        stream = io.BytesIO()
        with tarfile.open(fileobj=stream, mode="w") as tar:
            for name, content in files.items():
                info = tarfile.TarInfo(name=name)
                encoded_content = content.encode("utf-8")
                info.size = len(encoded_content)
                tar.addfile(info, io.BytesIO(encoded_content))
        stream.seek(0)
        return stream

    def execute_function(self, closure: Closure, *args: Any, **kwargs: Any) -> str:
        """Execute the function in the sandbox."""
        script = self.generate_script(closure, *args, **kwargs)
        client = docker.from_env()
        container = None
        try:
            container = client.containers.run(
                self.image,
                "tail -f /dev/null",  # Keep container running
                remove=True,
                detach=True,
                security_opt=["no-new-privileges"],  # Prevent privilege escalation
                cap_drop=["ALL"],  # Drop all capabilities
                environment=self.environment,
            )
            contents = {"main.py": script}
            stream = self._create_tar_stream(contents)
            container.put_archive("/", stream)
            exit_code, (stdout, stderr) = container.exec_run(
                cmd=["uv", "run", "/main.py"],
                demux=True,
            )
            if exit_code:
                raise RuntimeError(
                    f"Error running code in Docker container: {stderr.decode('utf-8').strip()}"
                )
            return json.loads(stdout.decode("utf-8").strip())
        finally:
            if container:
                with suppress(Exception):
                    container.stop()
