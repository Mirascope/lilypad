"""Main CLI entrypoint for Lilypad."""

import importlib.metadata

from rich import print
from typer import Typer

from .commands import local_command
from .commands.stub import stubs_command

app = Typer()

app.command(name="version", help="Show the Lilypad version.")(
    lambda: print(importlib.metadata.version("python-lilypad"))
)
app.command(name="local", help="Run Lilypad Locally")(local_command)
app.command(
    "generate-version-stubs",
    help="Scan the specified module directory and generate stub files for version assignments.",
)(stubs_command)