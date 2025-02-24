"""Main CLI entrypoint for Lilypad."""

import importlib.metadata

from rich import print
from typer import Typer

from .commands import local_command

app = Typer()

app.command(name="version", help="Show the Lilypad version.")(
    lambda: print(importlib.metadata.version("python-lilypad"))
)
app.command(name="local", help="Run Lilypad Locally")(local_command)
