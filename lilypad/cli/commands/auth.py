"""The `auth` command to run before you can trace to hosted Lilypad Hosted Cloud."""

import asyncio
import json
import os
import secrets
import time
import warnings
import webbrowser
from typing import Any

import httpx
import typer
from rich import print
from rich.prompt import Confirm, IntPrompt

from ...server.client import LilypadClient
from ...server.models import DeviceCodeTable
from ...server.schemas import ProjectPublic
from ...server.settings import Settings, get_settings
from ._utils import get_and_create_config


def _generate_device_code() -> str:
    """Generate a random code for device authentication."""
    return secrets.token_urlsafe(16)


def _save_token(device_code: DeviceCodeTable) -> dict[str, Any]:
    """Save the token to a JSON file."""
    config_path = os.path.join(".lilypad", "config.json")
    data = get_and_create_config(config_path)

    with open(config_path, "w") as f:
        data["token"] = device_code.token
        json.dump(data, f, indent=4)
    return data


async def _poll_auth_status(
    device_code: str, settings: Settings
) -> DeviceCodeTable | None:
    """Poll the FastAPI endpoint for session data."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{settings.api_url}/v0/device-codes/{device_code}"
            )
            if response.status_code == 200:
                return DeviceCodeTable.model_validate(response.json())
        except httpx.RequestError:
            pass
    return None


async def _delete_device_code(device_code: str, settings: Settings) -> bool:
    """Delete the device code from the FastAPI server."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(
                f"{settings.api_url}/v0/device-codes/{device_code}"
            )
            return response.status_code == 200
        except httpx.RequestError:
            return False


def _show_project_selection(projects: list[ProjectPublic]) -> ProjectPublic:
    """Show a list of projects and prompt the user to select one."""
    print("\nAvailable projects:")
    for idx, project in enumerate(projects, 1):
        print(f"[green]{idx}[/green]. {project.name}")

    choice = IntPrompt.ask("Select project number")
    return projects[choice - 1]


def _create_or_switch_project(data: dict) -> bool:
    """Prompt the user to create a new project or switch to an existing one."""
    lilypad_client = LilypadClient(token=data["token"])
    projects = lilypad_client.get_projects()
    if len(projects) == 0:
        typer.echo("You don't have any projects. Let's create one!")
        project_name = typer.prompt("What is your project name?")
        project_public = lilypad_client.post_project(project_name)
        with open(".lilypad/config.json", "w") as f:
            data["project_uuid"] = str(project_public.uuid)
            json.dump(data, f, indent=4)
        typer.echo(f"\nProject created: {project_name}. You are now ready to trace!")
        return True
    elif "project_uuid" in data:
        if Confirm.ask("Would you like to switch projects?"):
            selected_project = _show_project_selection(projects)
            typer.echo(f"\nSwitching to project: {selected_project.name}")
            with open(".lilypad/config.json", "w") as f:
                data["project_uuid"] = str(selected_project.uuid)
                json.dump(data, f, indent=4)
            return True
        else:
            typer.echo("Bye!")
            return True
    else:
        typer.echo("Project is missing in config, please select one to continue.")
        selected_project = _show_project_selection(projects)
        with open(".lilypad/config.json", "w") as f:
            data["project_uuid"] = str(selected_project.uuid)
            json.dump(data, f, indent=4)
        typer.echo(
            f"\nProject selected: {selected_project.name}. You are now ready to trace!"
        )
        return True


def _check_existing_token() -> bool:
    """Check if an existing token exists and prompt the user to switch projects."""
    if os.path.exists(".lilypad/config.json"):
        with open(".lilypad/config.json") as f:
            data = json.load(f)
        if "token" in data:
            return _create_or_switch_project(data)
    return False


def auth_command(
    base_url: str | None = typer.Option(
        default=None, help="Remote url to send generations to"
    ),
) -> None:
    """Open browser for authentication and save the received token."""
    warnings.warn(
        "`lilypad auth` is deprecated. Navigate to https://app.lilypad.so to first create a project and generate an API key.",
        UserWarning,
    )
    settings = get_settings()
    if not base_url:
        base_url = settings.api_url
    config_path = os.path.join(".lilypad", "config.json")
    data = get_and_create_config(config_path)
    with open(config_path, "w") as f:
        data["base_url"] = base_url
        json.dump(data, f, indent=4)

    if _check_existing_token():
        return

    device_code = _generate_device_code()
    login_url = f"{data['base_url']}/auth/login?deviceCode={device_code}"
    webbrowser.open(login_url)

    typer.echo("\nWaiting for authentication to complete...")
    max_wait_time = 300  # 5 minutes
    poll_interval = 2  # 2 seconds
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        # Poll the FastAPI endpoint
        session_data = asyncio.run(_poll_auth_status(device_code, settings))
        if session_data:
            did_delete = asyncio.run(_delete_device_code(device_code, settings))
            with open(config_path, "w") as f:
                data["token"] = session_data.token
                json.dump(data, f, indent=4)
            if not did_delete:
                typer.echo("Authentication failed. Please try again.")
                return
            typer.echo("\nAuthentication successful!")
            break
        time.sleep(poll_interval)
    else:
        typer.echo("Authentication timed out. Please try again.")
        return

    _create_or_switch_project(data)
