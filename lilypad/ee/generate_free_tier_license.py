"""
generate_free_tier_license.py

This script demonstrates how to generate a "free-tier" license key
using the existing generate_license() function from the EE validate module.

Usage:
  python generate_free_tier_license.py --private-key /path/to/private_key.pem \
                                       --password yourKeyPass \
                                       --customer "Free User" \
                                       --license-id "FREE-TIER-ABC" \
                                       --duration-days 365

Notes:
  - By default, --password is optional. If your key is unencrypted, omit it.
  - If you omit --customer, it defaults to "FreeTierUser".
  - The script will print the generated license key to stdout.
"""

import typer
from datetime import datetime, timedelta

from lilypad.ee.validate import generate_license, LicenseError

app = typer.Typer(help="Generate free-tier license keys for LilyPad EE features.")

@app.command()
def main(
    private_key_path: str = typer.Option(
        ...,
        "--private-key",
        "-k",
        help="Path to the RSA private key PEM file.",
    ),
    password: str = typer.Option(
        None,
        "--password",
        "-p",
        help="Password for the RSA private key if encrypted; leave blank if none.",
    ),
    customer: str = typer.Option(
        "FreeTierUser",
        "--customer",
        "-c",
        help="Customer or organization name embedded in the license.",
    ),
    license_id: str = typer.Option(
        "FREE-TIER",
        "--license-id",
        "-i",
        help="A unique license ID to embed in the license key.",
    ),
    duration_days: int = typer.Option(
        365,
        "--duration-days",
        "-d",
        help="Number of days until the license expires.",
    ),
):
    """
    Generate a free-tier license key for LilyPad EE features.
    """
    expires_at = datetime.now() + timedelta(days=duration_days)
    try:
        license_key = generate_license(
            private_key_path=private_key_path,
            password=password.encode() if password else None,
            customer=customer,
            license_id=license_id,
            expires_at=expires_at,
        )
        typer.echo("Successfully generated license key:")
        typer.echo(license_key)
    except LicenseError as e:
        typer.echo(f"Failed to generate license: {e}")

if __name__ == "__main__":
    app()
