"""Data retention service for enforcing data retention policies based on organization tier."""

import asyncio
import contextlib
import hashlib
import json
import logging
from collections.abc import AsyncIterator, Generator
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from time import time
from uuid import UUID

from sqlalchemy import func, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.exc import TimeoutError as SQLTimeoutError
from sqlmodel import Session, col, desc, select

from ee import Tier

from ...ee.server.features import cloud_features
from ..db.session import create_session
from ..models.billing import BillingTable
from ..models.organizations import OrganizationTable
from ..settings import get_settings

log = logging.getLogger(__name__)
settings = get_settings()


@dataclass
class CleanupMetrics:
    """Metrics for cleanup operations."""

    organization_uuid: UUID | None
    organization_name: str | None = None
    duration_seconds: float = 0.0
    spans_deleted: int = 0
    comments_deleted: int = 0
    annotations_deleted: int = 0
    error: str | None = None
    lock_acquired: bool = True
    dry_run: bool = False
    cutoff_date: datetime | None = None


@dataclass
class DeletionAuditLog:
    """Audit log entry for deleted data."""

    organization_uuid: UUID
    organization_name: str
    cutoff_date: datetime
    spans_deleted: list[UUID]
    deletion_timestamp: datetime
    dry_run: bool

    def to_json(self) -> str:
        """Convert to JSON for logging."""
        data = asdict(self)
        # Convert UUIDs and datetimes to strings
        data["organization_uuid"] = str(data["organization_uuid"])
        data["cutoff_date"] = data["cutoff_date"].isoformat()
        data["deletion_timestamp"] = data["deletion_timestamp"].isoformat()
        data["spans_deleted"] = [str(uuid) for uuid in data["spans_deleted"]]
        return json.dumps(data)


class DataRetentionService:
    """Service for managing data retention policies.

    This service is designed for PostgreSQL and provides:
    - Distributed locking via advisory locks
    - Connection pool management
    - Comprehensive metrics and monitoring
    - Audit logging before deletion
    - Dry run mode for testing
    - Proper error handling and retries
    """

    # Configuration constants
    BATCH_SIZE = settings.data_retention_batch_size
    LOCK_TIMEOUT_MS = settings.data_retention_lock_timeout_ms
    QUERY_TIMEOUT_MS = settings.data_retention_query_timeout_ms
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 1.0  # seconds
    MAX_CONCURRENT_CONNECTIONS = settings.data_retention_max_concurrent_connections

    # Fixed batch size for simplicity
    DEFAULT_STREAMING_BATCH_SIZE = 100

    # Feature flags
    DRY_RUN_ENABLED = settings.data_retention_dry_run
    AUDIT_LOG_ENABLED = settings.data_retention_audit_log

    @staticmethod
    def _is_retryable_error(error: DBAPIError) -> bool:
        """Check if a database error is retryable.

        Retryable errors include:
        - Serialization failures
        - Deadlocks
        - Connection errors
        """
        error_str = str(error).lower()
        retryable_patterns = [
            "could not serialize",
            "deadlock detected",
            "connection",
            "could not connect",
            "connection refused",
            "connection reset",
        ]
        return any(pattern in error_str for pattern in retryable_patterns)

    def __init__(self, session: Session) -> None:
        """Initialize data retention service."""
        self.session = session
        self._semaphore = asyncio.Semaphore(self.MAX_CONCURRENT_CONNECTIONS)

    async def _process_organization_async(
        self, org: OrganizationTable, dry_run: bool
    ) -> CleanupMetrics:
        """Process a single organization asynchronously."""
        async with self._semaphore:
            try:
                # Run synchronous cleanup in thread pool
                loop = asyncio.get_event_loop()
                metrics = await loop.run_in_executor(
                    None, self.cleanup_organization_data, org, dry_run
                )
                return metrics
            except Exception as e:
                log.error(
                    f"Failed to cleanup organization {org.uuid} ({org.name}): {e}",
                    exc_info=True,
                )
                return CleanupMetrics(
                    organization_uuid=org.uuid,  # type: ignore[arg-type]
                    organization_name=org.name,
                    duration_seconds=0.0,
                    spans_deleted=0,
                    comments_deleted=0,
                    annotations_deleted=0,
                    error=str(e),
                    dry_run=dry_run,
                )

    @contextlib.contextmanager
    def cleanup_transaction(self) -> Generator[None, None, None]:
        """Context manager for cleanup transactions with proper rollback handling."""
        savepoint = self.session.begin_nested()
        try:
            yield
            savepoint.commit()
        except Exception as e:
            savepoint.rollback()
            log.error(f"Transaction rolled back due to error: {e}")
            raise

    def _get_organization_tier(self, organization_uuid: UUID) -> Tier:
        """Get the tier for an organization from billing table."""
        stmt = (
            select(BillingTable)
            .where(col(BillingTable.organization_uuid) == organization_uuid)
            .order_by(desc(BillingTable.created_at))
            .limit(1)
        )

        billing = self.session.exec(stmt).first()  # pyright: ignore[reportCallIssue, reportArgumentType]

        if not billing:
            return Tier.FREE

        if not billing.stripe_price_id:
            return Tier.FREE

        # Determine tier based on stripe_price_id (same logic as BillingService)
        if billing.stripe_price_id == settings.stripe_cloud_team_flat_price_id:
            return Tier.TEAM
        elif billing.stripe_price_id == settings.stripe_cloud_pro_flat_price_id:
            return Tier.PRO
        else:
            return Tier.FREE

    @classmethod
    def get_retention_days(cls, tier: Tier) -> int | None:
        """Get the retention days for a tier.

        Returns None if retention is unlimited (infinity).
        """
        features = cloud_features.get(tier)

        if not features:
            log.warning(f"No features found for tier {tier}, defaulting to FREE tier")
            features = cloud_features[Tier.FREE]

        retention_days = features.data_retention_days

        # Handle infinity case (unlimited retention)
        if retention_days == float("inf"):
            return None

        return int(retention_days)

    def get_retention_cutoff(self, tier: Tier) -> datetime | None:
        """Get the cutoff datetime for data retention.

        Returns None if retention is unlimited.
        """
        retention_days = self.get_retention_days(tier)

        if retention_days is None:
            return None

        return datetime.now(timezone.utc) - timedelta(days=retention_days)

    @staticmethod
    def _get_advisory_lock_id(organization_uuid: UUID) -> int:
        """Get a deterministic lock ID for an organization.

        Uses SHA256 for deterministic hashing to avoid collisions.
        """
        # Use SHA256 for deterministic, collision-resistant hashing
        hash_bytes = hashlib.sha256(str(organization_uuid).encode()).digest()
        # Take first 8 bytes as signed 64-bit integer
        lock_id = int.from_bytes(hash_bytes[:8], byteorder="big", signed=True)
        # Ensure it's within PostgreSQL bigint range
        return lock_id & 0x7FFFFFFFFFFFFFFF

    def _acquire_advisory_lock(
        self, organization_uuid: UUID, timeout_ms: int = LOCK_TIMEOUT_MS
    ) -> bool:
        """Acquire PostgreSQL advisory lock for organization with timeout.

        Returns True if lock acquired, False if timeout or already locked.
        """
        lock_id = self._get_advisory_lock_id(organization_uuid)

        try:
            # Set lock timeout for the session
            self.session.execute(text(f"SET LOCAL lock_timeout = '{timeout_ms}ms'"))

            # First try non-blocking lock acquisition
            acquired = self.session.execute(
                select(func.pg_try_advisory_xact_lock(lock_id))
            ).scalar_one()

            if acquired:
                return True

            # If not acquired, try blocking version with timeout
            # This will either acquire the lock or timeout
            self.session.execute(
                select(func.pg_advisory_xact_lock(lock_id))
            ).first()  # pragma: no cover

            return True  # pragma: no cover
        except DBAPIError as e:  # pragma: no cover
            if "lock timeout" in str(e):
                return False
            raise

    def _audit_deletion(
        self,
        organization: OrganizationTable,
        span_uuids: list[UUID],
        cutoff_date: datetime,
        dry_run: bool = False,
    ) -> None:
        """Create audit log entry for deletion."""
        if not self.AUDIT_LOG_ENABLED:
            return

        audit_log = DeletionAuditLog(
            organization_uuid=organization.uuid,  # type: ignore[arg-type]
            organization_name=organization.name,
            cutoff_date=cutoff_date,
            spans_deleted=span_uuids,
            deletion_timestamp=datetime.now(timezone.utc),
            dry_run=dry_run,
        )

        # Log to structured logging
        log.info(f"AUDIT_LOG: {audit_log.to_json()}")

        # Could also write to database audit table or external system
        # self._write_audit_to_database(audit_log)

    def _cleanup_with_counts(
        self,
        organization: OrganizationTable,
        cutoff_date: datetime,
        dry_run: bool = False,
    ) -> CleanupMetrics:
        """Delete old data and return accurate counts using CASCADE DELETE.

        Returns CleanupMetrics with deletion counts and audit information.
        """
        start_time = time()
        metrics = CleanupMetrics(
            organization_uuid=organization.uuid,
            organization_name=organization.name,
            duration_seconds=0.0,
            spans_deleted=0,
            comments_deleted=0,
            annotations_deleted=0,
            dry_run=dry_run,
            cutoff_date=cutoff_date,
        )

        if organization.uuid is None:
            return metrics  # pragma: no cover

        try:
            # Acquire advisory lock to prevent concurrent cleanup
            if not self._acquire_advisory_lock(organization.uuid):
                log.warning(
                    f"Could not acquire lock for organization {organization.uuid} "
                    f"within {self.LOCK_TIMEOUT_MS}ms, skipping"
                )
                metrics.error = "Lock acquisition timeout"
                metrics.lock_acquired = False
                metrics.duration_seconds = time() - start_time
                return metrics

            # Set query timeout
            self.session.execute(
                text(f"SET LOCAL statement_timeout = '{self.QUERY_TIMEOUT_MS}ms'")
            )

            # Common CTE for both dry run and actual deletion
            base_cte = """
                WITH target_spans AS (
                    SELECT s.uuid
                    FROM spans s
                    WHERE s.organization_uuid = :org_uuid
                    AND s.created_at < :cutoff_date
                ),
                counts_before AS (
                    SELECT 
                        COUNT(DISTINCT ts.uuid) as span_count,
                        COUNT(DISTINCT c.uuid) as comment_count,
                        COUNT(DISTINCT a.uuid) as annotation_count
                    FROM target_spans ts
                    LEFT JOIN comments c ON c.span_uuid = ts.uuid
                    LEFT JOIN annotations a ON a.span_uuid = ts.uuid
                )
            """

            if dry_run:
                # Dry run - just return counts and UUIDs
                query = text(
                    base_cte
                    + """
                    SELECT 
                        span_count,
                        comment_count,
                        annotation_count,
                        ARRAY_AGG(DISTINCT ts.uuid) as span_uuids
                    FROM target_spans ts, counts_before
                    GROUP BY span_count, comment_count, annotation_count
                """
                )
            else:
                # Real deletion with atomic counts
                query = text(
                    base_cte
                    + """,
                    deleted_spans AS (
                        DELETE FROM spans
                        WHERE uuid IN (SELECT uuid FROM target_spans)
                        RETURNING uuid
                    )
                    SELECT 
                        (SELECT span_count FROM counts_before) as span_count,
                        (SELECT comment_count FROM counts_before) as comment_count,
                        (SELECT annotation_count FROM counts_before) as annotation_count,
                        ARRAY_AGG(deleted_spans.uuid) as span_uuids
                    FROM deleted_spans
                    GROUP BY (SELECT span_count FROM counts_before),
                             (SELECT comment_count FROM counts_before),
                             (SELECT annotation_count FROM counts_before)
                """
                )

            result = self.session.execute(
                query, {"org_uuid": organization.uuid, "cutoff_date": cutoff_date}
            ).fetchone()

            if result:
                metrics.spans_deleted = result.span_count or 0
                metrics.comments_deleted = result.comment_count or 0
                metrics.annotations_deleted = result.annotation_count or 0
                span_uuids = result.span_uuids or []
            else:
                span_uuids = []

            # Audit log
            if span_uuids:
                self._audit_deletion(organization, span_uuids, cutoff_date, dry_run)

            metrics.duration_seconds = time() - start_time

            action = "Would delete" if dry_run else "Deleted"
            log.info(
                f"{action} for organization {organization.uuid} ({organization.name}): "
                f"{metrics.spans_deleted} spans, {metrics.comments_deleted} comments, "
                f"{metrics.annotations_deleted} annotations in {metrics.duration_seconds:.2f}s"
            )

            return metrics

        except SQLTimeoutError as e:
            metrics.error = f"Query timeout after {self.QUERY_TIMEOUT_MS}ms"
            metrics.duration_seconds = time() - start_time
            log.error(f"Timeout during cleanup for {organization.uuid}: {e}")
            raise
        except DBAPIError as e:
            metrics.error = f"Database error: {e}"
            metrics.duration_seconds = time() - start_time
            error_type = "retryable" if self._is_retryable_error(e) else "non-retryable"
            log.error(
                f"Database error ({error_type}) during cleanup for {organization.uuid}: {e}",
                exc_info=True,
            )
            raise
        except Exception as e:
            metrics.error = f"Unexpected error: {e}"
            metrics.duration_seconds = time() - start_time
            log.error(
                f"Unexpected error during cleanup for {organization.uuid}: {e}",
                exc_info=True,
            )
            raise

    def cleanup_organization_data(
        self, organization: OrganizationTable, dry_run: bool = False
    ) -> CleanupMetrics:
        """Clean up old data for a specific organization based on retention policy.

        Includes retry logic for transient database errors.

        Args:
            organization: The organization to clean up
            dry_run: If True, only simulate deletion without actually deleting

        Returns metrics.
        """
        if organization.uuid is None:
            log.error("Organization has no UUID, skipping cleanup")
            metrics = CleanupMetrics(
                organization_uuid=None,
                organization_name=organization.name,
                duration_seconds=0.0,
                spans_deleted=0,
                comments_deleted=0,
                annotations_deleted=0,
                error="Organization has no UUID",
                dry_run=dry_run,
            )
            return metrics

        tier = self._get_organization_tier(organization.uuid)

        cutoff_date = self.get_retention_cutoff(tier)

        if cutoff_date is None:
            log.info(
                f"Organization {organization.uuid} ({organization.name}) has unlimited retention "
                f"(tier: {tier.name}), skipping cleanup"
            )
            metrics = CleanupMetrics(
                organization_uuid=organization.uuid,
                organization_name=organization.name,
                duration_seconds=0.0,
                spans_deleted=0,
                comments_deleted=0,
                annotations_deleted=0,
                dry_run=dry_run,
            )
            return metrics

        log.info(
            f"{'[DRY RUN] ' if dry_run else ''}Cleaning up data for organization "
            f"{organization.uuid} ({organization.name}) "
            f"(tier: {tier.name}) created before {cutoff_date}"
        )

        # Retry logic for transient database errors
        for attempt in range(self.MAX_RETRIES):
            try:
                with self.cleanup_transaction():
                    return self._cleanup_with_counts(organization, cutoff_date, dry_run)
            except DBAPIError as e:
                if self._is_retryable_error(e) and attempt < self.MAX_RETRIES - 1:
                    wait_time = self.RETRY_DELAY_BASE * (2**attempt)
                    log.warning(
                        f"Retryable error for org {organization.uuid}, "
                        f"attempt {attempt + 1}/{self.MAX_RETRIES}: {e}. "
                        f"Retrying in {wait_time}s..."
                    )
                    import time

                    time.sleep(wait_time)
                else:
                    raise

        # Should never reach here
        raise RuntimeError("Max retries exceeded")  # pragma: no cover

    async def cleanup_all_organizations_streaming(
        self, batch_size: int | None = None, dry_run: bool | None = None
    ) -> AsyncIterator[CleanupMetrics]:
        """Clean up old data for all organizations using streaming.

        Yields metrics for each organization as it's processed.
        Uses semaphore to limit concurrent connections.
        """
        batch_size = batch_size or self.DEFAULT_STREAMING_BATCH_SIZE
        dry_run = dry_run if dry_run is not None else self.DRY_RUN_ENABLED

        # Query all organizations, ordered for consistent pagination
        stmt = select(OrganizationTable).order_by(col(OrganizationTable.uuid))

        # Stream organizations and process them
        offset = 0
        total_processed = 0

        while True:
            batch_stmt = stmt.offset(offset).limit(batch_size)
            organizations = self.session.exec(batch_stmt).all()  # pyright: ignore[reportCallIssue, reportArgumentType]

            if not organizations:
                break

            # Process organizations concurrently with semaphore limiting
            tasks = []
            for org in organizations:
                task = self._process_organization_async(org, dry_run)
                tasks.append(task)

            # Wait for all tasks in this batch to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)

            # Yield results
            for result in results:
                if isinstance(result, BaseException):  # pragma: no cover
                    log.error(f"Error processing organization: {result}")
                    yield CleanupMetrics(
                        organization_uuid=None,
                        organization_name="Unknown",
                        duration_seconds=0.0,
                        spans_deleted=0,
                        comments_deleted=0,
                        annotations_deleted=0,
                        error=str(result),
                        dry_run=dry_run,
                    )
                else:
                    yield result

            total_processed += len(organizations)
            offset += batch_size

            # Small delay between batches to avoid overwhelming the database
            await asyncio.sleep(0.1)

        log.info(
            f"Streaming cleanup completed: {total_processed} organizations processed"
        )

    async def cleanup_all_organizations(
        self, batch_size: int | None = None, dry_run: bool | None = None
    ) -> dict[str, CleanupMetrics]:
        """Clean up old data for all organizations.

        Returns dict mapping organization UUIDs to metrics.
        """
        results = {}

        async for metrics in self.cleanup_all_organizations_streaming(
            batch_size, dry_run
        ):
            if metrics.organization_uuid:
                results[str(metrics.organization_uuid)] = metrics

        # Log summary
        total_spans = sum(m.spans_deleted for m in results.values() if not m.error)
        total_comments = sum(
            m.comments_deleted for m in results.values() if not m.error
        )
        total_annotations = sum(
            m.annotations_deleted for m in results.values() if not m.error
        )
        total_errors = sum(1 for m in results.values() if m.error)
        total_duration = sum(m.duration_seconds for m in results.values())

        action = "Would delete" if (dry_run or self.DRY_RUN_ENABLED) else "Deleted"
        log.info(
            f"Data retention cleanup completed for {len(results)} organizations. "
            f"{action}: {total_spans} spans, {total_comments} comments, "
            f"{total_annotations} annotations. "
            f"Errors: {total_errors}. Total duration: {total_duration:.2f}s"
        )

        return results


class DataRetentionScheduler:
    """Scheduler for running data retention cleanup tasks periodically."""

    def __init__(self) -> None:
        """Initialize the scheduler."""
        self._task = None
        self._running = False
        self._consecutive_errors = 0
        self._max_consecutive_errors = settings.data_retention_max_errors
        self._lock = asyncio.Lock()  # Lock for atomic operations

    async def start(self, run_immediately: bool = False) -> None:
        """Start the retention scheduler.

        Args:
            run_immediately: If True, run cleanup after initial delay.
        """
        async with self._lock:
            if self._running:
                log.warning("Data retention scheduler is already running")
                return

            self._running = True
            self._task = asyncio.create_task(self._run_scheduler())
        log.info(
            f"Data retention scheduler started "
            f"(runs daily at {settings.data_retention_scheduler_hour} UTC, "
            f"initial delay: {settings.data_retention_initial_delay_seconds}s)"
        )

        if run_immediately:
            # Schedule initial cleanup after configured delay
            asyncio.create_task(self._run_initial_cleanup())

    async def stop(self) -> None:
        """Stop the retention scheduler."""
        async with self._lock:
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
                # Run cleanup once per day at configured hour (UTC)
                now = datetime.now(timezone.utc)
                scheduled_hour = settings.data_retention_scheduler_hour

                # Validate hour
                if not 0 <= scheduled_hour <= 23:
                    log.error(
                        f"Invalid scheduler hour: {scheduled_hour}, using default 2 AM"
                    )
                    scheduled_hour = 2

                next_run = now.replace(
                    hour=scheduled_hour, minute=0, second=0, microsecond=0
                )

                # If it's already past the scheduled hour today, schedule for tomorrow
                if now >= next_run:
                    next_run += timedelta(days=1)

                wait_seconds = (next_run - now).total_seconds()
                log.info(
                    f"Next data retention cleanup scheduled for {next_run} (in {wait_seconds} seconds)"
                )

                # Wait until next run time or until stopped
                await asyncio.sleep(wait_seconds)

                if not self._running:
                    break  # pragma: no cover

                # Perform cleanup with retries
                await self._run_cleanup_with_retries()

            except asyncio.CancelledError:
                break
            except Exception as e:
                self._consecutive_errors += 1
                log.error(
                    f"Error in data retention scheduler (consecutive errors: {self._consecutive_errors}): {e}",
                    exc_info=True,
                )

                # Exponential backoff with proper random jitter
                import random

                base_wait = min(60 * (1.5 ** (self._consecutive_errors - 1)), 3600)
                jitter = base_wait * 0.1 * random.random()
                wait_time = base_wait + jitter

                if self._consecutive_errors >= self._max_consecutive_errors:
                    log.error(
                        f"Max consecutive errors ({self._max_consecutive_errors}) reached. "
                        f"Scheduler will continue but may need manual intervention."
                    )
                    # TODO: Send alert

                log.info(f"Waiting {wait_time:.0f} seconds before retrying...")
                await asyncio.sleep(wait_time)

    async def _run_cleanup_with_retries(self) -> None:
        """Run cleanup with retry logic for transient failures."""
        for attempt in range(DataRetentionService.MAX_RETRIES):
            try:
                await self._run_cleanup()
                self._consecutive_errors = 0  # Reset on success
                return
            except DBAPIError as e:
                if (
                    "could not serialize" in str(e)
                    and attempt < DataRetentionService.MAX_RETRIES - 1
                ):
                    wait_time = DataRetentionService.RETRY_DELAY_BASE * (2**attempt)
                    log.warning(f"Serialization failure, retrying in {wait_time}s...")
                    await asyncio.sleep(wait_time)
                else:
                    raise

    async def _run_cleanup(self) -> None:  # pragma: no cover
        """Run the actual cleanup process."""
        log.info("Starting scheduled data retention cleanup")

        session = create_session()
        try:
            service = DataRetentionService(session)

            # Check if dry run is enabled
            dry_run = service.DRY_RUN_ENABLED
            if dry_run:  # pragma: no cover
                log.info("DRY RUN MODE ENABLED - No data will be deleted")

            # Use fixed batch size for predictable performance
            results = await service.cleanup_all_organizations(
                batch_size=50,  # Conservative batch size
                dry_run=dry_run,
            )

            # Log metrics for monitoring
            successful_cleanups = sum(
                1 for m in results.values() if not m.error
            )  # pragma: no cover
            failed_cleanups = sum(
                1 for m in results.values() if m.error
            )  # pragma: no cover
            total_spans_deleted = sum(  # pragma: no cover
                m.spans_deleted
                for m in results.values()
                if not m.error  # pragma: no cover
            )

            log.info(  # pragma: no cover
                f"Data retention cleanup completed. "
                f"Successful: {successful_cleanups}, Failed: {failed_cleanups}, "
                f"Total spans deleted: {total_spans_deleted}"
            )

            # TODO: Send metrics to monitoring system
            # metrics.gauge('data_retention.successful_cleanups', successful_cleanups)
            # metrics.gauge('data_retention.failed_cleanups', failed_cleanups)
            # metrics.counter('data_retention.spans_deleted', total_spans_deleted)

        finally:
            session.close()

    async def _run_initial_cleanup(self) -> None:
        """Run initial cleanup after a delay."""
        delay_seconds = settings.data_retention_initial_delay_seconds
        log.info(
            f"Scheduling initial data retention cleanup in {delay_seconds} seconds"
        )
        await asyncio.sleep(delay_seconds)

        if self._running:
            log.info("Running initial data retention cleanup")
            await self._run_cleanup_with_retries()


# Global scheduler instance
_retention_scheduler = None


def get_retention_scheduler() -> DataRetentionScheduler:
    """Get the global data retention scheduler instance."""
    global _retention_scheduler
    if _retention_scheduler is None:
        _retention_scheduler = DataRetentionScheduler()
    return _retention_scheduler
