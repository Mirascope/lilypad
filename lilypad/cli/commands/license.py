"""License management commands for the CLI."""

import requests
import typer
from rich import print

from ...ee.validate import LicenseError, LicenseValidator
from ...server.client import LilypadClient
from ._utils import get_and_create_config


def set_license_command(
    license_key: str = typer.Argument(..., help="License key to set"),
) -> None:
    """Set or update the license key for organization."""
    try:
        # Get config and check for token
        config_path = ".lilypad/config.json"
        config = get_and_create_config(config_path)

        if "token" not in config:
            print(
                "[red]✗[/red] No authentication token found. Please run 'lilypad auth' first"
            )
            raise typer.Exit(1)

        client = LilypadClient(token=config["token"])

        # Validate license key and get info
        validator = LicenseValidator()
        license_info = validator.verify_license(license_key)

        # Use LilypadClient to update the organization
        client.patch_organization(
            license_info.organization_uuid, {"license": license_key}
        )

        print(
            f"[green]✓[/green] License key successfully set for organization {license_info.organization_uuid}"
        )
        print(f"[blue]ℹ[/blue] License tier: {license_info.tier.value}")
        print(f"[blue]ℹ[/blue] Expires at: {license_info.expires_at}")

    except LicenseError as e:
        print(f"[red]✗[/red] Error validating license key: {str(e)}")
        raise typer.Exit(1)
    except requests.exceptions.HTTPError as e:
        print(f"[red]✗[/red] API Error: {e}")
        raise typer.Exit(1)
    except ConnectionError:
        print("[red]✗[/red] Could not connect to server. Please check your connection")
        raise typer.Exit(1)
    except Exception as e:
        print(f"[red]✗[/red] Error setting license key: {str(e)}")
        raise typer.Exit(1)
