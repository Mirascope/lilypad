"""Features for each tier for Lilypad Enterprise Edition"""

from pydantic import BaseModel

from ee.validate import Tier


class FeatureSettings(BaseModel):
    """Feature settings for a given tier."""

    num_users_per_organization: int | float
    traces_per_month: int | float
    data_retention_days: int | float
    display_retention_days: (
        int | float
    )  # Display-level retention (may be less than storage)


# Cloud
cloud_features = {
    Tier.FREE: FeatureSettings(
        num_users_per_organization=2,
        traces_per_month=30_000,
        data_retention_days=90,
        display_retention_days=30,
    ),
    Tier.PRO: FeatureSettings(
        num_users_per_organization=10,
        traces_per_month=100_000,
        data_retention_days=180,
        display_retention_days=180,
    ),
    Tier.TEAM: FeatureSettings(
        num_users_per_organization=float("inf"),
        traces_per_month=1_000_000,
        data_retention_days=float("inf"),
        display_retention_days=float("inf"),
    ),
    Tier.ENTERPRISE: FeatureSettings(
        num_users_per_organization=float("inf"),
        traces_per_month=float("inf"),
        data_retention_days=float("inf"),
        display_retention_days=float("inf"),
    ),
}
