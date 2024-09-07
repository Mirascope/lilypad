"""Lilypad commands."""

import requests

from lilypad.app.models import PromptVersionTable


def pull(project_name: str) -> str:
    """Pull the latest prompt version."""
    url = f"http://localhost:8000/projects/{project_name}/versions"
    response = requests.get(url)
    return PromptVersionTable(**response.json()).prompt_template
