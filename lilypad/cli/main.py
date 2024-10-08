"""Main CLI entrypoint for Lilypad."""

from typer import Typer

from .commands import (
    create_command,
    run_command,
    start_command,
)

app = Typer()

app.command(name="start", help="Initialize Lilypad")(start_command)
app.command(name="create", help="Create a Lilypad function stub")(create_command)
app.command(name="run", help="Run a Lilypad prompt")(run_command)
