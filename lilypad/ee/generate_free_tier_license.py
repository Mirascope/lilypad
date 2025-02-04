#!/usr/bin/env python
"""Free-Tier License Key Generator for LilyPad Enterprise Edition

This module generates a free-tier license key for users who wish to self-host
the system without requiring an externally provided private key. The license is
signed using an RSA key pair dedicated solely to the free tier. Note that
the key is not considered sensitive and is only used to enable free-tier
functionality.

Usage:
    python generate_free_tier_license.py --customer "Free User" --license-id "FREE-TIER-ABC" --duration-days 365
"""

import base64
import json
from datetime import datetime, timedelta
from pathlib import Path

import typer
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

app = typer.Typer(
    help="Generate a free-tier license key for LilyPad Enterprise Edition features."
)

FREE_TIER_PRIVATE_KEY_FILE_NAME = "free_tier_private_key.pem"
FREE_TIER_PRIVATE_KEY = (
    Path(__file__).parent.joinpath(FREE_TIER_PRIVATE_KEY_FILE_NAME).read_text()
)


def generate_free_tier_license(
    customer: str, license_id: str, expires_at: datetime
) -> str:
    """Generate a free-tier license key using the built-in RSA private key.

    Args:
        customer (str): Customer or organization name to be embedded in the license.
        license_id (str): Unique identifier for the license.
        expires_at (datetime): Expiration datetime for the license.

    Returns:
        str: The free-tier license key formatted as 'base64(data).base64(signature)'.
    """
    # Load the built-in free-tier private key. This key is unencrypted.
    private_key = serialization.load_pem_private_key(
        FREE_TIER_PRIVATE_KEY.encode(), password=None, backend=default_backend()
    )

    # Construct the license payload.
    # The "tier" field explicitly indicates that this is a free-tier license.
    license_data = {
        "customer": customer,
        "license_id": license_id,
        "exp": expires_at.timestamp(),
        "tier": "free",
    }
    data_bytes = json.dumps(license_data).encode("utf-8")

    # Sign the license data using RSA-PSS with SHA256.
    signature = private_key.sign(
        data_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    # Encode the payload and signature using URL-safe Base64 encoding.
    data_b64 = base64.urlsafe_b64encode(data_bytes).rstrip(b"=").decode("ascii")
    sig_b64 = base64.urlsafe_b64encode(signature).rstrip(b"=").decode("ascii")

    return f"{data_b64}.{sig_b64}"


@app.command()
def main(
    customer: str = typer.Option(
        "FreeTierUser",
        "--customer",
        "-c",
        help="Customer name to be embedded in the license.",
    ),
    license_id: str = typer.Option(
        "FREE-TIER", "--license-id", "-i", help="Unique identifier for the license."
    ),
    duration_days: int = typer.Option(
        365, "--duration-days", "-d", help="Number of days until the license expires."
    ),
) -> None:
    """Command-line entry point for generating a free-tier license key.

    The expiration date is calculated based on the provided duration in days.
    The generated license key is printed to standard output.
    """
    expires_at = datetime.now() + timedelta(days=duration_days)
    license_key = generate_free_tier_license(customer, license_id, expires_at)
    typer.echo("Successfully generated free-tier license key:")
    typer.echo(license_key)


if __name__ == "__main__":
    app()
