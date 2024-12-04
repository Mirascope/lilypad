"""Root Test configuration and fixtures."""

import os

from pytest import Config


def pytest_configure(config: Config):
    """Configure pytest."""
    os.environ["LILYPAD_ENVIRONMENT"] = "test"
