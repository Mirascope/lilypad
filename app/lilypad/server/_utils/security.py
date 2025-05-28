"""Security utilities for secret management."""

import re
from typing import Any


def mask_secret(secret: str, visible_chars: int = 4) -> str:
    """Mask a secret, leaving only the first few characters visible."""
    if not secret:
        return ""

    visible = min(visible_chars, len(secret))
    return secret[:visible] + "*" * max(0, len(secret) - visible)


def sanitize_secret_data(data: dict[str, Any]) -> dict[str, Any]:
    """Remove or mask sensitive fields from a dictionary."""
    sensitive_patterns = [
        re.compile(r"(?i)(pass|secret|key|token|auth|credential)"),
    ]

    result = {}
    for key, value in data.items():
        # Check if key matches any sensitive pattern
        is_sensitive = any(pattern.search(key) for pattern in sensitive_patterns)

        if isinstance(value, dict):
            result[key] = sanitize_secret_data(value)
        elif isinstance(value, str) and is_sensitive:
            result[key] = mask_secret(value)
        else:
            result[key] = value

    return result
