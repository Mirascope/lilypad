"""Security utilities for secret management."""

import re
from typing import Any


def mask_secret(secret: str | None, visible_chars: int = 4) -> str:
    """Mask a secret, leaving only the first few characters visible."""
    if not secret:
        return ""

    # Always mask at least 1 character if the string is longer than 1 char
    if len(secret) <= 1:
        return "*"

    visible = min(
        visible_chars, len(secret) - 1
    )  # Always leave at least 1 char to mask
    return secret[:visible] + "*" * (len(secret) - visible)


def sanitize_secret_data(data: dict[str, Any]) -> dict[str, Any]:
    """Remove or mask sensitive fields from a dictionary."""
    sensitive_patterns = [
        re.compile(
            r"(?i).*(password|passwd|secret|_key|key_|^key$|keychain|token|auth|credential).*"
        ),
    ]

    result = {}
    for key, value in data.items():
        # Check if key matches any sensitive pattern
        is_sensitive = any(pattern.match(key) for pattern in sensitive_patterns)

        if isinstance(value, dict):
            result[key] = sanitize_secret_data(value)
        elif isinstance(value, str) and is_sensitive:
            result[key] = mask_secret(value)
        else:
            result[key] = value

    return result
