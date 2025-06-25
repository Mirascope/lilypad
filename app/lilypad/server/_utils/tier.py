"""Utility functions for tier management to avoid circular imports."""

import logging
from uuid import UUID

from sqlmodel import Session, col, desc, select

from ee import Tier

from ...ee.server.features import cloud_features
from ..models.billing import BillingTable
from ..settings import get_settings

logger = logging.getLogger(__name__)


def get_organization_tier(session: Session, organization_uuid: UUID) -> Tier:
    """Get the tier for an organization from billing table.

    This is a standalone utility function to avoid circular imports
    between services.

    Args:
        session: Database session
        organization_uuid: The organization UUID to check

    Returns:
        The tier for the organization
    """
    try:
        stmt = (
            select(BillingTable)
            .where(col(BillingTable.organization_uuid) == organization_uuid)
            .order_by(desc(BillingTable.created_at))
            .limit(1)
        )

        billing = session.exec(stmt).first()  # pyright: ignore[reportCallIssue, reportArgumentType]

        if not billing:
            return Tier.FREE

        if not billing.stripe_price_id:
            return Tier.FREE

        settings = get_settings()
        # Determine tier based on stripe_price_id
        if billing.stripe_price_id == settings.stripe_cloud_team_flat_price_id:
            return Tier.TEAM
        elif billing.stripe_price_id == settings.stripe_cloud_pro_flat_price_id:
            return Tier.PRO
        else:
            return Tier.FREE
    except Exception as e:
        # Expected for organizations without billing setup
        logger.debug(
            f"Could not determine organization tier for {organization_uuid}: {e}"
        )
        return Tier.FREE


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
        return None

    # Convert float('inf') to None for unlimited retention
    days = feature_settings.display_retention_days
    return None if days == float("inf") else int(days)
