"""Features for each tier for Lilypad Enterprise Edition"""

from pydantic import BaseModel

from ee.validate import Tier


class FeatureSettings(BaseModel):
    """Feature settings for a given tier."""

    traces_per_month: int | float
    data_retention_days: int | float


# Cloud
cloud_features = {
    Tier.FREE: FeatureSettings(
        traces_per_month=10_000,
        data_retention_days=30,
    ),
    Tier.PRO: FeatureSettings(
        traces_per_month=100_000,
        data_retention_days=180,
    ),
    Tier.TEAM: FeatureSettings(
        traces_per_month=1_000_000,
        data_retention_days=float("inf"),
    ),
    Tier.ENTERPRISE: FeatureSettings(
        traces_per_month=float("inf"),
        data_retention_days=float("inf"),
    ),
}
