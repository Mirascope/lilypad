"""Data retention task for deleting old spans based on organization tier."""

import logging
from uuid import uuid4

from sqlmodel import select

from ee import Tier
from lilypad.ee.server.features import cloud_features
from lilypad.server.db.session import get_session
from lilypad.server.models.organizations import OrganizationTable
from lilypad.server.schemas.users import UserPublic
from lilypad.server.services.spans import SpanService

logger = logging.getLogger(__name__)

def apply_data_retention_policy() -> None:
    """Apply data retention policy for all organizations.

    This function should be run periodically (e.g., daily) to delete spans
    that are older than the retention period for each organization based on their tier.
    """
    logger.info("Starting data retention policy application")

    session = next(get_session())

    try:
        organizations = session.exec(select(OrganizationTable)).all()

        for organization in organizations:
            try:
                tier = Tier.FREE  # Default to FREE tier

                if organization.subscription_plan:
                    plan_to_tier = {
                        "free": Tier.FREE,
                        "pro": Tier.PRO,
                        "team": Tier.TEAM,
                        "enterprise": Tier.ENTERPRISE,
                    }
                    tier = plan_to_tier.get(organization.subscription_plan.lower(), Tier.FREE)

                retention_days = cloud_features[tier].data_retention_days

                system_user = UserPublic(
                    uuid=uuid4(),
                    email="support@mirascope.com",
                    first_name="System",
                    active_organization_uuid=organization.uuid,
                    user_organizations=[]
                )

                span_service = SpanService(session, system_user)

                # Mark old spans as deleted (logical deletion)
                deleted_count = span_service.delete_old_spans(organization.uuid, int(retention_days))

                logger.info(
                    f"Applied data retention policy for organization {organization.uuid}: "
                    f"marked {deleted_count} spans as deleted that are older than {retention_days} days"
                )

            except Exception as e:
                logger.error(
                    f"Error applying data retention policy for organization {organization.uuid}: {str(e)}"
                )

    except Exception as e:
        logger.error(f"Error in data retention policy application: {str(e)}")

    finally:
        session.close()

if __name__ == "__main__":
    # This allows the script to be run directly for testing or manual execution
    apply_data_retention_policy()
