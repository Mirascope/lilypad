"""Lilypad commands."""

import requests


def pull(hash: str) -> str:
    """Pull the latest prompt version."""
    url = f"http://localhost:8000/api/prompt-versions/{hash}"
    response = requests.get(url)
    return response.json()["prompt_template"]
