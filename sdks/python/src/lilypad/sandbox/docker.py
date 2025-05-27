"""Docker sandbox runner."""

import io
import tarfile
from typing import Any
from contextlib import suppress

import docker

from . import SandboxRunner
from .runner import Result
from .._utils import Closure

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

    def execute_function(
        self,
        closure: Closure,
        custom_result: dict[str, str] | None = None,
        pre_actions: list[str] | None = None,
        after_actions: list[str] | None = None,
        extra_imports: list[str] | None = None,
        *args: Any,
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

            return self.parse_execution_result(stdout or b"", stderr or b"", exit_code)
        finally:
            if container:
                with suppress(Exception):
                    container.stop()
