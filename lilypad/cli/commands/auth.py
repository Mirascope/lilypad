"""The `auth` command to run before you can trace to hosted Lilypad Hosted Cloud."""

import asyncio
import json
import os
import secrets
import time
import webbrowser

import httpx
import typer

from ...server.models import DeviceCodeTable

AUTH_URL = "https://your-auth-endpoint.com/auth"
REDIRECT_PORT = 5173
LOGIN_URL = "http://localhost:5173/auth/login"
API_BASE_URL = "http://localhost:8000/api/v0"  # Your FastAPI server


def generate_device_code() -> str:
    """Generate a random code for device authentication."""
    return secrets.token_urlsafe(16)


def save_token(device_code: DeviceCodeTable) -> bool:
    """Save the token to a JSON file."""
    if not os.path.exists(".lilypad"):
        os.mkdir(".lilypad")
    try:
        with open(".lilypad/config.json") as f:
            data = json.load(f)
        data["token"] = device_code.token
        with open(".lilypad/config.json", "w") as f:
            json.dump(data, f, indent=4)
            return True
    except Exception:
        return False


async def poll_auth_status(device_code: str) -> DeviceCodeTable | None:
    """Poll the FastAPI endpoint for session data."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{API_BASE_URL}/device-codes/{device_code}")
            if response.status_code == 200:
                return DeviceCodeTable.model_validate(response.json())
        except httpx.RequestError:
            pass
    return None


async def delete_device_code(device_code: str) -> bool:
    """Delete the device code from the FastAPI server."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.delete(f"{API_BASE_URL}/device-codes/{device_code}")
            return response.status_code == 200
        except httpx.RequestError:
            return False


def auth_command() -> None:
    """Open browser for authentication and save the received token."""
    device_code = generate_device_code()
    login_url = f"{LOGIN_URL}?deviceCode={device_code}"
    webbrowser.open(login_url)

    typer.echo("\nWaiting for authentication to complete...")
    max_wait_time = 300  # 5 minutes
    poll_interval = 2  # 2 seconds
    start_time = time.time()

    while time.time() - start_time < max_wait_time:
        # Poll the FastAPI endpoint
        session_data = asyncio.run(poll_auth_status(device_code))
        if session_data:
            did_delete = asyncio.run(delete_device_code(device_code))
            did_save = save_token(session_data)
            if not did_delete and not did_save:
                typer.echo("Authentication failed. Please try again.")
                return
            typer.echo("\nAuthentication successful!")
            return
        time.sleep(poll_interval)

    typer.echo("\nAuthentication timed out. Please try again.")
