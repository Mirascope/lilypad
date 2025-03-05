from contextlib import suppress

from .runner import SandboxRunner

with suppress(ImportError):
    from .docker import DockerSandboxRunner

__all__ = ["SandboxRunner", "DockerSandboxRunner"]
