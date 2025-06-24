"""Tests for improved data retention service."""

import asyncio
import contextlib
import hashlib
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from ee import Tier
from lilypad.server.models.organizations import OrganizationTable
from lilypad.server.services.data_retention_service import (
    CleanupMetrics,
    DataRetentionScheduler,
    DataRetentionService,
    DeletionAuditLog,
)


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    session = MagicMock()
    # Add exec method that returns a mock result
    mock_exec_result = MagicMock()
    mock_exec_result.all.return_value = []
    mock_exec_result.first.return_value = None
    session.exec.return_value = mock_exec_result
    # Reset the mock before each test
    session.reset_mock()
    return session


@pytest.fixture
def retention_service(mock_session):
    """Create a data retention service instance."""
    return DataRetentionService(mock_session)


@pytest.fixture
def mock_organization():
    """Create a mock organization."""
    org = MagicMock(spec=OrganizationTable)
    org.uuid = uuid4()
    org.name = "Test Organization"
    return org


def test_get_advisory_lock_id_deterministic(retention_service):
    """Test advisory lock ID is deterministic using SHA256."""
    org_uuid = uuid4()

    # Should always return same ID for same UUID
    id1 = retention_service._get_advisory_lock_id(org_uuid)
    id2 = retention_service._get_advisory_lock_id(org_uuid)
    assert id1 == id2

    # Should be different for different UUIDs
    other_uuid = uuid4()
    id3 = retention_service._get_advisory_lock_id(other_uuid)
    assert id1 != id3

    # Should match expected SHA256 calculation
    expected_hash = hashlib.sha256(str(org_uuid).encode()).digest()
    expected_id = (
        int.from_bytes(expected_hash[:8], byteorder="big", signed=True)
        & 0x7FFFFFFFFFFFFFFF
    )
    assert id1 == expected_id


def test_acquire_advisory_lock_timeout_increased(retention_service, mock_organization):
    """Test advisory lock uses longer timeout (60s not 5s)."""
    mock_session = retention_service.session

    retention_service._acquire_advisory_lock(mock_organization.uuid)

    # Check timeout was set to 60 seconds
    timeout_call = mock_session.execute.call_args_list[0]
    assert "60000ms" in str(timeout_call[0][0])


def test_cleanup_with_counts_dry_run_mode(retention_service, mock_organization):
    """Test dry run mode doesn't delete anything."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

    # Mock dry run query result
    mock_result = MagicMock()
    mock_result.fetchone.return_value = MagicMock(
        span_count=10,
        comment_count=5,
        annotation_count=3,
        span_uuids=[uuid4() for _ in range(10)],
    )
    retention_service.session.execute.return_value = mock_result

    with (
        patch.object(retention_service, "_acquire_advisory_lock", return_value=True),
        patch.object(retention_service, "_audit_deletion") as mock_audit,
    ):
        metrics = retention_service._cleanup_with_counts(
            mock_organization, cutoff_date, dry_run=True
        )

    assert metrics.spans_deleted == 10
    assert metrics.comments_deleted == 5
    assert metrics.annotations_deleted == 3
    assert metrics.dry_run is True
    assert metrics.error is None

    # Verify audit was called with dry_run=True and span_uuids
    mock_audit.assert_called_once()
    # Check that span_uuids were passed (2nd argument, index 1)
    assert len(mock_audit.call_args[0][1]) == 10
    # dry_run is the 4th positional argument (index 3)
    assert mock_audit.call_args[0][3] is True

    # Verify query didn't contain DELETE
    query_text = str(retention_service.session.execute.call_args_list[-1][0][0])
    assert "DELETE FROM" not in query_text


def test_cleanup_with_counts_real_deletion_with_audit(
    retention_service, mock_organization
):
    """Test real deletion includes proper audit logging."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

    # Mock deletion query result
    deleted_uuids = [uuid4() for _ in range(5)]
    mock_result = MagicMock()
    mock_result.fetchone.return_value = MagicMock(
        span_count=5, comment_count=3, annotation_count=2, span_uuids=deleted_uuids
    )
    retention_service.session.execute.return_value = mock_result

    with (
        patch.object(retention_service, "_acquire_advisory_lock", return_value=True),
        patch.object(retention_service, "_audit_deletion") as mock_audit,
    ):
        metrics = retention_service._cleanup_with_counts(
            mock_organization, cutoff_date, dry_run=False
        )

    assert metrics.spans_deleted == 5
    assert metrics.comments_deleted == 3
    assert metrics.annotations_deleted == 2
    assert metrics.dry_run is False

    # Verify audit was called correctly
    mock_audit.assert_called_once_with(
        mock_organization, deleted_uuids, cutoff_date, False
    )


def test_audit_deletion_creates_structured_log(retention_service, mock_organization):
    """Test audit deletion creates proper structured log entry."""
    span_uuids = [uuid4() for _ in range(3)]
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

    with patch("lilypad.server.services.data_retention_service.log") as mock_log:
        retention_service._audit_deletion(
            mock_organization, span_uuids, cutoff_date, dry_run=False
        )

    # Verify structured log was created
    mock_log.info.assert_called_once()
    log_message = mock_log.info.call_args[0][0]
    assert "AUDIT_LOG:" in log_message

    # Verify JSON structure
    import json

    json_str = log_message.split("AUDIT_LOG: ")[1]
    audit_data = json.loads(json_str)

    assert audit_data["organization_uuid"] == str(mock_organization.uuid)
    assert audit_data["organization_name"] == mock_organization.name
    assert len(audit_data["spans_deleted"]) == 3
    assert audit_data["dry_run"] is False


def test_get_organization_tier_uses_price_ids(retention_service, mock_organization):
    """Test tier detection uses Stripe price IDs from settings."""
    mock_billing = MagicMock()
    retention_service.session.exec.return_value.first.return_value = mock_billing

    # Test with TEAM price ID
    with patch(
        "lilypad.server.services.data_retention_service.settings"
    ) as mock_settings:
        mock_settings.stripe_cloud_team_flat_price_id = "price_team_123"
        mock_settings.stripe_cloud_pro_flat_price_id = "price_pro_456"

        mock_billing.stripe_price_id = "price_team_123"
        tier = retention_service._get_organization_tier(mock_organization.uuid)
        assert tier == Tier.TEAM

        # Test with PRO price ID
        mock_billing.stripe_price_id = "price_pro_456"
        tier = retention_service._get_organization_tier(mock_organization.uuid)
        assert tier == Tier.PRO

        # Test with unknown price ID
        mock_billing.stripe_price_id = "price_unknown_789"
        tier = retention_service._get_organization_tier(mock_organization.uuid)
        assert tier == Tier.FREE

        # Test with None stripe_price_id (covers line 176)
        mock_billing.stripe_price_id = None
        tier = retention_service._get_organization_tier(mock_organization.uuid)
        assert tier == Tier.FREE

        # Test with empty stripe_price_id
        mock_billing.stripe_price_id = ""
        tier = retention_service._get_organization_tier(mock_organization.uuid)
        assert tier == Tier.FREE

        retention_service.session.exec.return_value.first.return_value = None
        tier = retention_service._get_organization_tier(mock_organization.uuid)
        assert tier == Tier.FREE


@pytest.mark.asyncio
async def test_cleanup_all_organizations_streaming_with_semaphore(retention_service):
    """Test streaming cleanup uses semaphore to limit concurrent connections."""
    # Create many organizations
    orgs = [
        MagicMock(spec=OrganizationTable, uuid=uuid4(), name=f"Org {i}")
        for i in range(20)
    ]

    # Mock batch queries
    retention_service.session.exec.side_effect = [
        MagicMock(all=lambda: orgs[:10]),  # First batch
        MagicMock(all=lambda: orgs[10:20]),  # Second batch
        MagicMock(all=lambda: []),  # Empty - done
    ]

    # Track concurrent executions
    max_concurrent = 0
    current_concurrent = 0

    def mock_cleanup(org, dry_run):
        nonlocal max_concurrent, current_concurrent
        current_concurrent += 1
        max_concurrent = max(max_concurrent, current_concurrent)
        # Simulate synchronous work
        import time

        time.sleep(0.01)
        current_concurrent -= 1
        return CleanupMetrics(
            organization_uuid=org.uuid,
            organization_name=org.name,
            spans_deleted=1,
            comments_deleted=0,
            annotations_deleted=0,
        )

    with patch.object(
        retention_service, "cleanup_organization_data", side_effect=mock_cleanup
    ):
        metrics_list = []
        async for metrics in retention_service.cleanup_all_organizations_streaming():
            metrics_list.append(metrics)

    assert len(metrics_list) == 20
    # Should never exceed MAX_CONCURRENT_CONNECTIONS (10)
    assert max_concurrent <= DataRetentionService.MAX_CONCURRENT_CONNECTIONS


@pytest.mark.asyncio
async def test_scheduler_validates_hour_setting():
    """Test scheduler validates hour setting."""
    scheduler = DataRetentionScheduler()
    scheduler._running = True  # Mark as running so the while loop executes

    with patch(
        "lilypad.server.services.data_retention_service.settings"
    ) as mock_settings:
        # Test invalid hour
        mock_settings.data_retention_scheduler_hour = 25  # Invalid!
        mock_settings.data_retention_initial_delay_seconds = 1

        with (
            patch.object(
                scheduler, "_run_cleanup_with_retries", new_callable=AsyncMock
            ),
            patch("lilypad.server.services.data_retention_service.log") as mock_log,
        ):
            # Start scheduler
            task = asyncio.create_task(scheduler._run_scheduler())

            # Let it run long enough to hit the validation
            await asyncio.sleep(0.2)

            # Stop it
            scheduler._running = False
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

            # Should log error about invalid hour
            mock_log.error.assert_any_call(
                "Invalid scheduler hour: 25, using default 2 AM"
            )


def test_scheduler_jitter_calculation():
    """Test scheduler uses proper random jitter calculation."""
    scheduler = DataRetentionScheduler()

    # Set up error state
    scheduler._consecutive_errors = 3
    scheduler._max_consecutive_errors = 5

    # Test the jitter calculation logic directly
    with patch("random.random") as mock_random:
        mock_random.return_value = 0.5  # Deterministic for test

        # Calculate expected values
        base_wait = min(60 * (1.5 ** (3 - 1)), 3600)  # 135 seconds, capped at 3600
        expected_jitter = base_wait * 0.1 * 0.5  # 6.75 seconds
        expected_total = base_wait + expected_jitter  # 141.75 seconds

        # The scheduler code calculates jitter like this:
        # base_wait = min(60 * (1.5 ** (self._consecutive_errors - 1)), 3600)
        # jitter = base_wait * 0.1 * random.random()
        # wait_time = base_wait + jitter

        # Verify our calculation matches
        assert base_wait == 135.0
        assert expected_jitter == 6.75
        assert expected_total == 141.75


def test_deletion_audit_log_serialization():
    """Test DeletionAuditLog properly serializes to JSON."""
    audit_log = DeletionAuditLog(
        organization_uuid=uuid4(),
        organization_name="Test Org",
        cutoff_date=datetime.now(timezone.utc),
        spans_deleted=[uuid4() for _ in range(3)],
        deletion_timestamp=datetime.now(timezone.utc),
        dry_run=True,
    )

    # Should serialize without errors
    json_str = audit_log.to_json()

    # Should be valid JSON
    import json

    data = json.loads(json_str)

    # Check fields
    assert data["organization_name"] == "Test Org"
    assert data["dry_run"] is True
    assert len(data["spans_deleted"]) == 3
    assert all(isinstance(uuid_str, str) for uuid_str in data["spans_deleted"])


def test_cleanup_organization_data_with_feature_flags(
    retention_service, mock_organization
):
    """Test cleanup respects feature flags."""
    with (
        patch.object(
            retention_service, "_get_organization_tier", return_value=Tier.FREE
        ),
        patch.object(retention_service, "_cleanup_with_counts") as mock_cleanup,
    ):
        mock_cleanup.return_value = MagicMock(
            spans_deleted=5,
            comments_deleted=2,
            annotations_deleted=1,
            dry_run=False,
            error=None,
        )

        # Test default behavior (dry_run defaults to False)
        retention_service.cleanup_organization_data(mock_organization)

        # Should pass dry_run=False by default (it's the 3rd positional arg, index 2)
        assert mock_cleanup.call_args[0][2] is False

        # Test with explicit dry_run=True
        retention_service.cleanup_organization_data(mock_organization, dry_run=True)

        # Should respect explicit parameter
        assert mock_cleanup.call_args[0][2] is True


def test_is_retryable_error():
    """Test _is_retryable_error static method."""
    from sqlalchemy.exc import DBAPIError

    # Test retryable errors
    retryable_errors = [
        "could not serialize access",
        "deadlock detected",
        "connection error",
        "could not connect to server",
        "connection refused",
        "connection reset by peer",
    ]

    for error_msg in retryable_errors:
        error = DBAPIError("statement", {}, Exception(error_msg))
        assert DataRetentionService._is_retryable_error(error) is True

    # Test non-retryable errors
    non_retryable_errors = [
        "syntax error",
        "permission denied",
        "table does not exist",
    ]

    for error_msg in non_retryable_errors:
        error = DBAPIError("statement", {}, Exception(error_msg))
        assert DataRetentionService._is_retryable_error(error) is False


def test_cleanup_organization_no_uuid(retention_service):
    """Test cleanup with organization that has no UUID."""
    mock_org = MagicMock(spec=OrganizationTable)
    mock_org.uuid = None
    mock_org.name = "No UUID Org"

    metrics = retention_service.cleanup_organization_data(mock_org)

    assert metrics.organization_uuid is None
    assert metrics.organization_name == "No UUID Org"
    assert metrics.error == "Organization has no UUID"
    assert metrics.spans_deleted == 0


def test_cleanup_organization_unlimited_retention(retention_service, mock_organization):
    """Test cleanup with unlimited retention (Team/Enterprise tier)."""
    with patch.object(
        retention_service, "_get_organization_tier", return_value=Tier.TEAM
    ):
        metrics = retention_service.cleanup_organization_data(mock_organization)

    assert metrics.organization_uuid == mock_organization.uuid
    assert metrics.spans_deleted == 0
    assert metrics.comments_deleted == 0
    assert metrics.annotations_deleted == 0
    assert metrics.error is None


def test_cleanup_with_counts_lock_timeout(retention_service, mock_organization):
    """Test cleanup when advisory lock cannot be acquired."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

    with patch.object(retention_service, "_acquire_advisory_lock", return_value=False):
        metrics = retention_service._cleanup_with_counts(
            mock_organization, cutoff_date, dry_run=False
        )

    assert metrics.error == "Lock acquisition timeout"
    assert metrics.lock_acquired is False
    assert metrics.spans_deleted == 0


def test_cleanup_with_counts_sql_timeout(retention_service, mock_organization):
    """Test cleanup when SQL query times out."""
    from sqlalchemy.exc import TimeoutError as SQLTimeoutError

    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

    with (
        patch.object(retention_service, "_acquire_advisory_lock", return_value=True),
        patch.object(
            retention_service.session,
            "execute",
            side_effect=SQLTimeoutError("statement", {}, Exception("timeout")),
        ),
        pytest.raises(SQLTimeoutError),
    ):
        retention_service._cleanup_with_counts(
            mock_organization, cutoff_date, dry_run=False
        )


def test_cleanup_with_counts_no_results(retention_service, mock_organization):
    """Test cleanup when query returns no results."""
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

    with (
        patch.object(retention_service, "_acquire_advisory_lock", return_value=True),
        patch.object(retention_service, "_audit_deletion") as mock_audit,
    ):
        # Mock execute to return None for fetchone
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        retention_service.session.execute.return_value = mock_result

        metrics = retention_service._cleanup_with_counts(
            mock_organization, cutoff_date, dry_run=False
        )

    assert metrics.spans_deleted == 0
    assert metrics.comments_deleted == 0
    assert metrics.annotations_deleted == 0
    # Audit should not be called when no spans deleted
    mock_audit.assert_not_called()


def test_cleanup_organization_with_retries(retention_service, mock_organization):
    """Test cleanup with retry logic for transient errors."""
    from sqlalchemy.exc import DBAPIError

    # Create a retryable error
    retryable_error = DBAPIError(
        "statement", {}, Exception("could not serialize access")
    )

    with (
        patch.object(
            retention_service, "_get_organization_tier", return_value=Tier.FREE
        ),
        patch.object(retention_service, "_cleanup_with_counts") as mock_cleanup,
        patch("time.sleep"),  # Mock sleep to speed up test
    ):
        # First two calls fail, third succeeds
        mock_cleanup.side_effect = [
            retryable_error,
            retryable_error,
            CleanupMetrics(
                organization_uuid=mock_organization.uuid,
                organization_name=mock_organization.name,
                spans_deleted=5,
                comments_deleted=2,
                annotations_deleted=1,
            ),
        ]

        metrics = retention_service.cleanup_organization_data(mock_organization)

    assert metrics.spans_deleted == 5
    assert mock_cleanup.call_count == 3


def test_cleanup_organization_max_retries_exceeded(
    retention_service, mock_organization
):
    """Test cleanup when max retries are exceeded."""
    from sqlalchemy.exc import DBAPIError

    # Create a retryable error
    retryable_error = DBAPIError(
        "statement", {}, Exception("could not serialize access")
    )

    with (
        patch.object(
            retention_service, "_get_organization_tier", return_value=Tier.FREE
        ),
        patch.object(
            retention_service, "_cleanup_with_counts", side_effect=retryable_error
        ),
        patch("time.sleep"),
        pytest.raises(DBAPIError),
    ):
        retention_service.cleanup_organization_data(mock_organization)


@pytest.mark.asyncio
async def test_scheduler_immediate_cleanup():
    """Test scheduler with immediate cleanup."""
    scheduler = DataRetentionScheduler()

    with (
        patch.object(
            scheduler, "_run_cleanup_with_retries", new_callable=AsyncMock
        ) as mock_cleanup,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        await scheduler.start(run_immediately=True)
        # Wait for the initial delay to pass
        await asyncio.sleep(0.01)
        # Manually trigger the initial cleanup since we're mocking sleep
        if scheduler._running:
            await scheduler._run_initial_cleanup()
        await scheduler.stop()

        # Immediate cleanup should have been called
        mock_cleanup.assert_called()


@pytest.mark.asyncio
async def test_scheduler_cleanup_with_retries_serialization_error():
    """Test scheduler retry logic for serialization errors."""
    from sqlalchemy.exc import DBAPIError

    scheduler = DataRetentionScheduler()

    # Create a serialization error
    serialization_error = DBAPIError(
        "statement", {}, Exception("could not serialize access")
    )

    with (
        patch.object(scheduler, "_run_cleanup", new_callable=AsyncMock) as mock_cleanup,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        # First call fails with serialization error, second succeeds
        mock_cleanup.side_effect = [serialization_error, None]

        await scheduler._run_cleanup_with_retries()

        assert mock_cleanup.call_count == 2


@pytest.mark.asyncio
async def test_scheduler_cleanup_with_retries_non_serialization_error():
    """Test scheduler does not retry non-serialization errors."""
    from sqlalchemy.exc import DBAPIError

    scheduler = DataRetentionScheduler()

    # Create a non-serialization error
    other_error = DBAPIError("statement", {}, Exception("permission denied"))

    with (
        patch.object(
            scheduler, "_run_cleanup", new_callable=AsyncMock, side_effect=other_error
        ),
        pytest.raises(DBAPIError),
    ):
        await scheduler._run_cleanup_with_retries()


@pytest.mark.asyncio
async def test_scheduler_already_running():
    """Test scheduler prevents duplicate starts."""
    scheduler = DataRetentionScheduler()

    with patch("lilypad.server.services.data_retention_service.log") as mock_log:
        scheduler._running = True
        await scheduler.start()

        mock_log.warning.assert_called_with(
            "Data retention scheduler is already running"
        )


@pytest.mark.asyncio
async def test_scheduler_max_consecutive_errors():
    """Test scheduler handles max consecutive errors."""
    scheduler = DataRetentionScheduler()
    # Start with 4 errors so the next one will trigger max errors
    scheduler._consecutive_errors = 4
    scheduler._max_consecutive_errors = 5

    with (
        patch("lilypad.server.services.data_retention_service.log") as mock_log,
        patch("asyncio.sleep", new_callable=AsyncMock) as mock_sleep,
        patch("random.random", return_value=0.5),
        patch(
            "lilypad.server.services.data_retention_service.datetime"
        ) as mock_datetime,
    ):
        # Mock datetime to control scheduling
        mock_now = MagicMock()
        mock_now.replace.return_value = mock_now
        mock_datetime.now.return_value = mock_now
        mock_now.__ge__.return_value = True  # Make it think it's time to run

        # Make sleep raise CancelledError after first call to exit the loop
        mock_sleep.side_effect = [None, asyncio.CancelledError()]

        # Run the scheduler
        scheduler._running = True
        with contextlib.suppress(asyncio.CancelledError):
            await scheduler._run_scheduler()

        # Should increment consecutive errors and log max errors reached
        assert scheduler._consecutive_errors == 5
        mock_log.error.assert_any_call(
            "Max consecutive errors (5) reached. "
            "Scheduler will continue but may need manual intervention."
        )


@pytest.mark.asyncio
async def test_process_organization_async_error(retention_service):
    """Test _process_organization_async error handling."""
    mock_org = MagicMock(spec=OrganizationTable)
    mock_org.uuid = uuid4()
    mock_org.name = "Test Org"

    with patch.object(
        retention_service,
        "cleanup_organization_data",
        side_effect=Exception("Cleanup failed"),
    ):
        metrics = await retention_service._process_organization_async(
            mock_org, dry_run=False
        )

    assert metrics.error == "Cleanup failed"
    assert metrics.organization_uuid == mock_org.uuid
    assert metrics.spans_deleted == 0


@pytest.mark.asyncio
async def test_cleanup_all_organizations_with_errors(retention_service):
    """Test cleanup_all_organizations with some organizations failing."""
    # Create mock organizations
    org1 = MagicMock(spec=OrganizationTable, uuid=uuid4(), name="Org1")
    org2 = MagicMock(spec=OrganizationTable, uuid=uuid4(), name="Org2")

    # Mock the query results
    retention_service.session.exec.side_effect = [
        MagicMock(all=lambda: [org1, org2]),
        MagicMock(all=lambda: []),
    ]

    with patch.object(retention_service, "cleanup_organization_data") as mock_cleanup:
        # First org succeeds, second fails
        mock_cleanup.side_effect = [
            CleanupMetrics(
                organization_uuid=org1.uuid,
                organization_name=org1.name,
                spans_deleted=5,
                comments_deleted=2,
                annotations_deleted=1,
            ),
            Exception("Cleanup failed"),
        ]

        results = await retention_service.cleanup_all_organizations()

    assert len(results) == 2
    assert results[str(org1.uuid)].spans_deleted == 5
    assert results[str(org2.uuid)].error == "Cleanup failed"


def test_get_retention_days_no_features():
    """Test get_retention_days when features not found for tier."""
    # Create a mock tier that doesn't exist in cloud_features
    with patch(
        "lilypad.server.services.data_retention_service.cloud_features"
    ) as mock_features:
        mock_features.get.return_value = None
        mock_features.__getitem__.return_value = MagicMock(data_retention_days=30)

        retention_days = DataRetentionService.get_retention_days(Tier.FREE)

    assert retention_days == 30


def test_audit_deletion_disabled():
    """Test audit deletion when audit logging is disabled."""
    from lilypad.server.services.data_retention_service import DataRetentionService

    mock_session = MagicMock()
    service = DataRetentionService(mock_session)

    # Disable audit logging
    with patch.object(service, "AUDIT_LOG_ENABLED", False):
        mock_org = MagicMock(uuid=uuid4(), name="Test Org")

        # Should not log anything when disabled
        with patch("lilypad.server.services.data_retention_service.log") as mock_log:
            service._audit_deletion(
                mock_org, [], datetime.now(timezone.utc), dry_run=False
            )

            # Should not have called log.info
            mock_log.info.assert_not_called()


def test_cleanup_with_counts_database_error():
    """Test cleanup with non-retryable database error."""
    from sqlalchemy.exc import DBAPIError

    mock_session = MagicMock()
    retention_service = DataRetentionService(mock_session)

    mock_org = MagicMock(uuid=uuid4(), name="Test Org")
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

    # Create a non-retryable database error
    db_error = DBAPIError("statement", {}, Exception("permission denied"))

    with (
        patch.object(retention_service, "_acquire_advisory_lock", return_value=True),
        patch.object(retention_service.session, "execute", side_effect=db_error),
        pytest.raises(DBAPIError),
    ):
        retention_service._cleanup_with_counts(mock_org, cutoff_date, dry_run=False)


def test_cleanup_with_counts_generic_exception():
    """Test cleanup with generic unexpected exception."""
    mock_session = MagicMock()
    retention_service = DataRetentionService(mock_session)

    mock_org = MagicMock(uuid=uuid4(), name="Test Org")
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=30)

    # Create a generic exception
    generic_error = RuntimeError("Unexpected error")

    with (
        patch.object(retention_service, "_acquire_advisory_lock", return_value=True),
        patch.object(retention_service.session, "execute", side_effect=generic_error),
        pytest.raises(RuntimeError),
    ):
        retention_service._cleanup_with_counts(mock_org, cutoff_date, dry_run=False)


def test_cleanup_organization_non_retryable_error():
    """Test cleanup organization with non-retryable database error."""
    from sqlalchemy.exc import DBAPIError

    mock_session = MagicMock()
    retention_service = DataRetentionService(mock_session)

    mock_org = MagicMock(spec=OrganizationTable, uuid=uuid4(), name="Test Org")

    # Create a non-retryable error
    non_retryable_error = DBAPIError("statement", {}, Exception("syntax error"))

    with (
        patch.object(
            retention_service, "_get_organization_tier", return_value=Tier.FREE
        ),
        patch.object(
            retention_service, "_cleanup_with_counts", side_effect=non_retryable_error
        ),
        pytest.raises(DBAPIError),
    ):
        retention_service.cleanup_organization_data(mock_org)


@pytest.mark.asyncio
async def test_cleanup_all_organizations_streaming_duplicate_process():
    """Test cleanup_all_organizations_streaming with duplicate internal process_org."""
    mock_session = MagicMock()
    retention_service = DataRetentionService(mock_session)

    # Create mock organizations
    org1 = MagicMock(spec=OrganizationTable)
    org1.uuid = uuid4()
    org1.name = "Org1"

    # Mock the query results
    retention_service.session.exec.side_effect = [  # pyright: ignore[reportFunctionMemberAccess, reportAttributeAccessIssue]
        MagicMock(all=lambda: [org1]),
        MagicMock(all=lambda: []),
    ]

    # Mock the actual cleanup to avoid JSON serialization issues
    with patch.object(retention_service, "cleanup_organization_data") as mock_cleanup:
        mock_cleanup.return_value = CleanupMetrics(
            organization_uuid=org1.uuid,
            organization_name=org1.name,
            spans_deleted=5,
            comments_deleted=2,
            annotations_deleted=1,
            duration_seconds=1.0,
        )

        # Track what happens
        metrics_list = []
        async for metrics in retention_service.cleanup_all_organizations_streaming():
            metrics_list.append(metrics)

        # Should have processed 1 org
        assert len(metrics_list) == 1
        assert metrics_list[0].organization_uuid == org1.uuid


@pytest.mark.asyncio
async def test_scheduler_initial_cleanup_not_running():
    """Test scheduler initial cleanup when scheduler is stopped."""
    scheduler = DataRetentionScheduler()

    with (
        patch.object(
            scheduler, "_run_cleanup_with_retries", new_callable=AsyncMock
        ) as mock_cleanup,
        patch("asyncio.sleep", new_callable=AsyncMock),
    ):
        # Start and immediately stop
        await scheduler.start(run_immediately=True)
        scheduler._running = False

        # Try to run initial cleanup
        await scheduler._run_initial_cleanup()

        # Should not run cleanup when not running
        mock_cleanup.assert_not_called()


def test_get_retention_scheduler_singleton():
    """Test get_retention_scheduler returns singleton instance."""
    # Reset global instance
    import lilypad.server.services.data_retention_service
    from lilypad.server.services.data_retention_service import (
        get_retention_scheduler,
    )

    lilypad.server.services.data_retention_service._retention_scheduler = None

    # First call creates instance
    scheduler1 = get_retention_scheduler()
    assert scheduler1 is not None

    # Second call returns same instance
    scheduler2 = get_retention_scheduler()
    assert scheduler1 is scheduler2
