"""Data retention service for enforcing data retention policies based on organization tier."""

import asyncio
import contextlib
import logging
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import delete, select
from sqlmodel import Session

from ee import Tier

from ...ee.server.features import cloud_features
from ..models.comments import CommentTable
from ..models.organizations import OrganizationTable
from ..models.spans import SpanTable
from ..settings import get_settings

log = logging.getLogger(__name__)
settings = get_settings()


class DataRetentionService:
    """Service for managing data retention policies."""

    def __init__(self, session: Session) -> None:
        """Initialize data retention service."""
        self.session = session

    def _get_organization_tier(self, organization_uuid: UUID) -> Tier:
        """Get the tier for an organization from billing table."""
        from sqlmodel import desc

        from ..models.billing import BillingTable

        billing = self.session.exec(
            select(BillingTable)
            .where(BillingTable.organization_uuid == organization_uuid)
            .order_by(desc(BillingTable.created_at))
        ).first()

        if billing and billing.stripe_price_id:
            # Determine tier based on stripe_price_id
            if billing.stripe_price_id == settings.stripe_cloud_team_flat_price_id:
                return Tier.TEAM
            elif billing.stripe_price_id == settings.stripe_cloud_pro_flat_price_id:
                return Tier.PRO

        return Tier.FREE

    def get_retention_days(self, organization: OrganizationTable) -> int | None:
        """Get retention days for an organization based on its tier.

        Returns None if retention is unlimited (infinity).
        """
        tier = self._get_organization_tier(organization.uuid)

        features = cloud_features.get(tier)

        if not features:
            log.warning(f"No features found for tier {tier}, defaulting to FREE tier")
            features = cloud_features[Tier.FREE]

        retention_days = features.data_retention_days

        # Handle infinity case (unlimited retention)
        if retention_days == float("inf"):
            return None

        return int(retention_days)

    def get_retention_cutoff(self, organization: OrganizationTable) -> datetime | None:
        """Get the cutoff datetime for data retention.

        Returns None if retention is unlimited.
        """
        retention_days = self.get_retention_days(organization)

        if retention_days is None:
            return None

        return datetime.now(timezone.utc) - timedelta(days=retention_days)

    async def cleanup_organization_data(
        self, organization: OrganizationTable
    ) -> dict[str, int]:
        """Clean up old data for a specific organization based on retention policy.

        Returns a dict with counts of deleted records by table.
        """
        cutoff_date = self.get_retention_cutoff(organization)

        if cutoff_date is None:
            log.debug(
                f"Organization {organization.uuid} has unlimited retention, skipping cleanup"
            )
            return {"spans": 0, "comments": 0, "annotations": 0}

        tier = self._get_organization_tier(organization.uuid)

        log.info(
            f"Cleaning up data for organization {organization.uuid} "
            f"(tier: {tier.name}) "
            f"older than {cutoff_date}"
        )

        deleted_counts = {}

        try:
            # Delete old spans (this will cascade delete related data)
            stmt = (
                delete(SpanTable)
                .where(SpanTable.organization_uuid == organization.uuid)
                .where(SpanTable.created_at < cutoff_date)
            )
            result = self.session.exec(stmt)
            deleted_counts["spans"] = result.rowcount

            # Delete orphaned comments (comments without spans)
            stmt = (
                delete(CommentTable)
                .where(CommentTable.organization_uuid == organization.uuid)
                .where(CommentTable.created_at < cutoff_date)
                .where(CommentTable.span_uuid.is_(None))
            )
            result = self.session.exec(stmt)
            deleted_counts["comments"] = result.rowcount

            # Delete orphaned annotations if EE is available
            try:
                from ...ee.server.models.annotations import AnnotationTable

                stmt = (
                    delete(AnnotationTable)
                    .where(AnnotationTable.organization_uuid == organization.uuid)
                    .where(AnnotationTable.created_at < cutoff_date)
                    .where(AnnotationTable.span_uuid.is_(None))
                )
                result = self.session.exec(stmt)
                deleted_counts["annotations"] = result.rowcount
            except ImportError:
                # EE not available
                deleted_counts["annotations"] = 0

            # Don't commit here - let the caller handle transaction boundaries

            log.info(
                f"Successfully cleaned up data for organization {organization.uuid}: "
                f"{deleted_counts}"
            )

            return deleted_counts

        except Exception as e:
            log.error(
                f"Error cleaning up data for organization {organization.uuid}: {e}"
            )
            # Don't rollback here - let the caller handle transaction boundaries
            raise

    async def cleanup_all_organizations(self) -> dict[str, dict[str, int]]:
        """Clean up old data for all organizations.

        Returns a dict mapping organization UUIDs to deletion counts.
        """
        # Get list of organizations first
        stmt = select(OrganizationTable)
        organizations = self.session.exec(stmt).all()
        org_uuids = [(str(org.uuid), org.name) for org in organizations]

        results = {}

        # Process each organization in a separate transaction
        from ..db.session import get_session

        for org_uuid, org_name in org_uuids:
            try:
                # Use a new session for each organization to isolate transactions
                with get_session() as org_session:
                    # Re-fetch the organization in the new session
                    org = org_session.exec(
                        select(OrganizationTable).where(
                            OrganizationTable.uuid == org_uuid
                        )
                    ).first()

                    if org:
                        service = DataRetentionService(org_session)
                        results[org_uuid] = await service.cleanup_organization_data(org)
                        # Commit the transaction for this organization
                        org_session.commit()
                    else:
                        log.warning(f"Organization {org_uuid} not found during cleanup")
                        results[org_uuid] = {"error": "Organization not found"}

            except Exception as e:
                log.error(
                    f"Failed to cleanup organization {org_uuid} ({org_name}): {e}",
                    exc_info=True,
                )
                results[org_uuid] = {"error": str(e), "error_type": type(e).__name__}

        return results


class DataRetentionScheduler:
    """Scheduler for running data retention cleanup tasks periodically."""

    def __init__(self) -> None:
        """Initialize the scheduler."""
        self._task = None
        self._running = False

    async def start(self, run_immediately: bool = False) -> None:
        """Start the retention scheduler.

        Args:
            run_immediately: If True, run cleanup 5 minutes after starting.
        """
        if self._running:
            log.warning("Data retention scheduler is already running")
            return

        self._running = True
        self._task = asyncio.create_task(self._run_scheduler())
        log.info("Data retention scheduler started")

        if run_immediately:
            # Schedule initial cleanup after 5 minutes
            asyncio.create_task(self._run_initial_cleanup())

    async def stop(self) -> None:
        """Stop the retention scheduler."""
        self._running = False

        if self._task:
            self._task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._task
            self._task = None

        log.info("Data retention scheduler stopped")

    async def _run_scheduler(self) -> None:
        """Run the scheduler loop."""
        while self._running:
            try:
                # Run cleanup once per day at 2 AM UTC
                now = datetime.now(timezone.utc)
                next_run = now.replace(hour=2, minute=0, second=0, microsecond=0)

                # If it's already past 2 AM today, schedule for tomorrow
                if now >= next_run:
                    next_run += timedelta(days=1)

                wait_seconds = (next_run - now).total_seconds()
                log.info(
                    f"Next data retention cleanup scheduled for {next_run} (in {wait_seconds} seconds)"
                )

                # Wait until next run time or until stopped
                await asyncio.sleep(wait_seconds)

                if not self._running:
                    break

                # Perform cleanup
                await self._run_cleanup()

            except asyncio.CancelledError:
                break
            except Exception as e:
                log.error(f"Error in data retention scheduler: {e}", exc_info=True)
                # Wait 1 hour before retrying on error
                await asyncio.sleep(3600)

    async def _run_cleanup(self) -> None:
        """Run the actual cleanup process."""
        log.info("Starting scheduled data retention cleanup")

        try:
            from ..db.session import get_session

            with get_session() as session:
                service = DataRetentionService(session)
                results = await service.cleanup_all_organizations()

                # Log summary
                total_deleted = {"spans": 0, "comments": 0, "annotations": 0}

                for org_result in results.values():
                    if "error" not in org_result:
                        for table, count in org_result.items():
                            total_deleted[table] += count

                log.info(
                    f"Data retention cleanup completed. Total deleted: {total_deleted}"
                )

        except Exception as e:
            log.error(f"Failed to run data retention cleanup: {e}", exc_info=True)

    async def _run_initial_cleanup(self) -> None:
        """Run initial cleanup after a delay."""
        log.info("Scheduling initial data retention cleanup in 5 minutes")
        await asyncio.sleep(300)  # Wait 5 minutes

        if self._running:
            log.info("Running initial data retention cleanup")
            await self._run_cleanup()


# Global scheduler instance
_retention_scheduler = None


def get_retention_scheduler() -> DataRetentionScheduler:
    """Get the global data retention scheduler instance."""
    global _retention_scheduler
    if _retention_scheduler is None:
        _retention_scheduler = DataRetentionScheduler()
    return _retention_scheduler
