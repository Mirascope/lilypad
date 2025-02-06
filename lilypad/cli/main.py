"""Main CLI entrypoint for Lilypad."""

import importlib.metadata

from rich import print
from typer import Typer

from .commands import auth_command, local_command, set_license_command

app = Typer()

app.command(name="version", help="Show the Lilypad version.")(
    lambda: print(importlib.metadata.version("python-lilypad"))
)
app.command(name="local", help="Run Lilypad Locally")(local_command)
app.command(name="auth", help="Authenticate with Lilypad")(auth_command)
app.command(
    name="set-license", help="Set or update license key for self-hosted instance"
)(set_license_command)
