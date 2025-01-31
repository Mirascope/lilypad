"""ee server module."""

from lilypad.ee import LicenseValidator
from lilypad.server.settings import get_settings


def validate_license() -> None:
    """Validate license."""
    if get_settings().environment != "development":
        LicenseValidator().validate_license()
