"""Utility functions for tier management to avoid circular imports."""

import logging

from ee import Tier

from ...ee.server.features import cloud_features

logger = logging.getLogger(__name__)


def get_display_retention_days(tier: Tier) -> int | None:
    """Get display retention days for a tier.

    This defines the display retention policy:
    - FREE: 30 days (though data is stored for 90 days)
    - PRO: 180 days
    - TEAM/ENTERPRISE: Unlimited

    Args:
        tier: The organization tier

    Returns:
        Number of days to retain display data, or None for unlimited
    """
    feature_settings = cloud_features.get(tier)
    if not feature_settings:
        return None  # pragma: no cover

    # Convert float('inf') to None for unlimited retention
    days = feature_settings.display_retention_days
    return None if days == float("inf") else int(days)
