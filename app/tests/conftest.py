"""Root Test configuration and fixtures."""

import os

from pytest import Config

from ee.validate import Tier


def pytest_configure(config: Config):
    """Configure pytest."""
    os.environ["LILYPAD_ENVIRONMENT"] = "test"
    os.environ["LILYPAD_POSTHOG_API_KEY"] = "test"
    os.environ["LILYPAD_POSTHOG_HOST"] = "test"


# Test constants for display retention days
DISPLAY_RETENTION_DAYS_FOR_TESTING = {
    Tier.FREE: 30,
    Tier.PRO: 180,
    Tier.TEAM: None,
    Tier.ENTERPRISE: None,
}
