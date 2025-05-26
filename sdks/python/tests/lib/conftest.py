from __future__ import annotations

import os

import pytest

api_key = "My API Key"


def pytest_configure(config: pytest.Config):
    """Configure pytest."""
    os.environ["LILYPAD_ENVIRONMENT"] = "test"
    os.environ["LILYPAD_API_KEY"] = api_key
    # Dummy project ID as UUID4
    os.environ["LILYPAD_PROJECT_ID"] = "f1b9b1b4-4b3b-4b3b-8b3b-4b3b4b3b4b3b"
