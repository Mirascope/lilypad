# Enterprise Edition

The contents of the `/ee` directory are licensed under the Enterprise Edition License. This code is only available to users with a valid enterprise license. See [lilypad/ee/LICENSE](https://github.com/Mirascope/lilypad/blob/main/ee/LICENSE) for the full terms.

## Free-Tier License

For users who wish to self-host Lilypad without purchasing an enterprise license, a free-tier license is available. The free-tier license key is generated using a built-in RSA key pair and enables free-tier functionality. The built-in free-tier keys are not considered sensitive and are provided solely to allow self-hosting of the free version.

### Generating a Free-Tier License Key

A command-line tool is provided for generating free-tier license keys. To generate a free-tier license key, run:

```bash
uv run lilypad/ee/generate_free_tier_license.py  --customer "Your Organization" --license-id "FREE-TIER-XYZ" --duration-days 365
