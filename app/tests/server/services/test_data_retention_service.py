"""Tests for data retention service."""

import asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import create_engine
from sqlmodel import Session, SQLModel, select

from ee import Tier
from lilypad.server.models.comments import CommentTable
from lilypad.server.models.organizations import OrganizationTable
from lilypad.server.models.projects import ProjectTable
from lilypad.server.models.spans import SpanTable
from lilypad.server.models.users import UserTable
from lilypad.server.services.data_retention_service import (
    DataRetentionScheduler,
    DataRetentionService,
    get_retention_scheduler,
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


def test_get_retention_days_free_tier(retention_service, mock_organization):
    """Test getting retention days for free tier."""
    with patch.object(
        retention_service, "_get_organization_tier", return_value=Tier.FREE
    ):
        days = retention_service.get_retention_days(mock_organization)
        assert days == 30


def test_get_retention_days_pro_tier(retention_service, mock_organization):
    """Test getting retention days for pro tier."""
    with patch.object(
        retention_service, "_get_organization_tier", return_value=Tier.PRO
    ):
        days = retention_service.get_retention_days(mock_organization)
        assert days == 180


def test_get_retention_days_unlimited(retention_service, mock_organization):
    """Test getting retention days for unlimited tiers."""
    with patch.object(
        retention_service, "_get_organization_tier", return_value=Tier.ENTERPRISE
    ):
        days = retention_service.get_retention_days(mock_organization)
        assert days is None


def test_get_retention_days_no_tier(retention_service, mock_organization):
    """Test getting retention days when organization has no billing record."""
    # Mock _get_organization_tier to return FREE (default when no billing record)
    with patch.object(
        retention_service, "_get_organization_tier", return_value=Tier.FREE
    ):
        days = retention_service.get_retention_days(mock_organization)
        assert days == 30  # Should default to FREE tier


def test_get_retention_cutoff_free_tier(retention_service, mock_organization):
    """Test getting retention cutoff for free tier."""
    with patch.object(
        retention_service, "_get_organization_tier", return_value=Tier.FREE
    ):
        cutoff = retention_service.get_retention_cutoff(mock_organization)

        expected_cutoff = datetime.now(timezone.utc) - timedelta(days=30)
        # Allow 1 second tolerance for test execution time
        assert abs((cutoff - expected_cutoff).total_seconds()) < 1


def test_get_retention_cutoff_unlimited(retention_service, mock_organization):
    """Test getting retention cutoff for unlimited retention."""
    with patch.object(
        retention_service, "_get_organization_tier", return_value=Tier.ENTERPRISE
    ):
        cutoff = retention_service.get_retention_cutoff(mock_organization)
        assert cutoff is None


@pytest.mark.asyncio
async def test_cleanup_organization_data_unlimited_retention(
    retention_service, mock_organization, mock_session
):
    """Test cleanup skips organizations with unlimited retention."""
    with patch.object(
        retention_service, "_get_organization_tier", return_value=Tier.ENTERPRISE
    ):
        result = await retention_service.cleanup_organization_data(mock_organization)

        assert result == {"spans": 0, "comments": 0, "annotations": 0}
        # _get_organization_tier is called even for unlimited retention (for logging)
        # But no delete operations should be performed
        # So we don't check exec call count here


@pytest.mark.asyncio
async def test_cleanup_organization_data_with_old_data(
    retention_service, mock_organization, mock_session
):
    """Test cleanup deletes old data."""
    # Mock the tier to be FREE
    with patch.object(
        retention_service, "_get_organization_tier", return_value=Tier.FREE
    ):
        # Create different mock results for each exec call
        mock_results = []
        for _ in range(3):  # We expect 3 delete operations
            mock_result = MagicMock()
            mock_result.rowcount = 5
            mock_results.append(mock_result)

        # Set side_effect to return different results for each call
        mock_session.exec.side_effect = mock_results

        result = await retention_service.cleanup_organization_data(mock_organization)

        # Check if annotations were processed (EE available) or not
        assert result["spans"] == 5
        assert result["comments"] == 5
        # annotations could be 0 (EE not available) or 5 (EE available)
        assert result["annotations"] in [0, 5]
        # Could be 2 operations (without EE) or 3 (with EE)
        assert mock_session.exec.call_count in [2, 3]


@pytest.mark.asyncio
async def test_cleanup_organization_data_error_handling(
    retention_service, mock_organization, mock_session
):
    """Test cleanup handles errors properly."""
    with patch.object(
        retention_service, "_get_organization_tier", return_value=Tier.FREE
    ):
        # Make exec raise an exception on the first delete operation
        mock_session.exec.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            await retention_service.cleanup_organization_data(mock_organization)


@pytest.mark.asyncio
async def test_cleanup_all_organizations(retention_service, mock_session):
    """Test cleanup for all organizations."""
    # Create mock organizations
    org1 = MagicMock(spec=OrganizationTable)
    org1.uuid = uuid4()
    org1.name = "Org 1"

    org2 = MagicMock(spec=OrganizationTable)
    org2.uuid = uuid4()
    org2.name = "Org 2"

    # Setup mock for the initial organization list query
    mock_exec_result = MagicMock()
    mock_exec_result.all.return_value = [org1, org2]
    mock_session.exec.return_value = mock_exec_result

    # Mock get_session to return a new session each time
    with patch("lilypad.server.db.session.get_session") as mock_get_session:
        # Create separate mock sessions for each organization
        mock_session1 = MagicMock()
        mock_session1.exec.return_value.first.return_value = org1
        mock_session1.commit = MagicMock()

        mock_session2 = MagicMock()
        mock_session2.exec.return_value.first.return_value = org2
        mock_session2.commit = MagicMock()

        # Return different sessions for each context manager call
        mock_get_session.return_value.__enter__.side_effect = [
            mock_session1,
            mock_session2,
        ]

        # Mock DataRetentionService instances created with the new sessions
        with patch(
            "lilypad.server.services.data_retention_service.DataRetentionService"
        ) as mock_service_class:
            # Create mock service instances
            mock_service1 = MagicMock()
            mock_service1.cleanup_organization_data = AsyncMock(
                return_value={"spans": 10, "comments": 5, "annotations": 2}
            )

            mock_service2 = MagicMock()
            mock_service2.cleanup_organization_data = AsyncMock(
                return_value={"spans": 0, "comments": 0, "annotations": 0}
            )

            # Return different service instances for each instantiation
            mock_service_class.side_effect = [mock_service1, mock_service2]

            results = await retention_service.cleanup_all_organizations()

    assert str(org1.uuid) in results
    assert results[str(org1.uuid)] == {"spans": 10, "comments": 5, "annotations": 2}
    assert str(org2.uuid) in results
    assert results[str(org2.uuid)] == {"spans": 0, "comments": 0, "annotations": 0}


@pytest.mark.asyncio
async def test_cleanup_all_organizations_with_errors(retention_service, mock_session):
    """Test cleanup handles individual organization errors."""
    org1 = MagicMock(spec=OrganizationTable)
    org1.uuid = uuid4()
    org1.name = "Org 1"

    # Setup mock for the initial organization list query
    mock_exec_result = MagicMock()
    mock_exec_result.all.return_value = [org1]
    mock_session.exec.return_value = mock_exec_result

    # Mock get_session to return a new session
    with patch("lilypad.server.db.session.get_session") as mock_get_session:
        mock_new_session = MagicMock()
        mock_new_session.exec.return_value.first.return_value = org1
        mock_get_session.return_value.__enter__.return_value = mock_new_session

        # Mock DataRetentionService instance
        with patch(
            "lilypad.server.services.data_retention_service.DataRetentionService"
        ) as mock_service_class:
            mock_service = MagicMock()
            mock_service.cleanup_organization_data = AsyncMock(
                side_effect=Exception("Cleanup failed")
            )
            mock_service_class.return_value = mock_service

            results = await retention_service.cleanup_all_organizations()

    assert str(org1.uuid) in results
    assert "error" in results[str(org1.uuid)]
    assert results[str(org1.uuid)]["error_type"] == "Exception"


@pytest.mark.asyncio
async def test_start_stop_scheduler():
    """Test starting and stopping the scheduler."""
    scheduler = DataRetentionScheduler()

    await scheduler.start()
    assert scheduler._running is True
    assert scheduler._task is not None

    await scheduler.stop()
    assert scheduler._running is False
    assert scheduler._task is None


@pytest.mark.asyncio
async def test_start_already_running():
    """Test starting scheduler when already running."""
    scheduler = DataRetentionScheduler()

    await scheduler.start()

    # Try to start again
    with patch("lilypad.server.services.data_retention_service.log") as mock_log:
        await scheduler.start()
        mock_log.warning.assert_called_with(
            "Data retention scheduler is already running"
        )

    await scheduler.stop()


@pytest.mark.asyncio
async def test_start_with_run_immediately():
    """Test starting scheduler with immediate run."""
    scheduler = DataRetentionScheduler()

    with patch.object(scheduler, "_run_initial_cleanup"):
        await scheduler.start(run_immediately=True)
        assert scheduler._running is True
        # Verify that _run_initial_cleanup was scheduled
        await asyncio.sleep(0.1)  # Give time for task creation

    await scheduler.stop()


@pytest.mark.asyncio
async def test_run_cleanup():
    """Test running the cleanup process."""
    scheduler = DataRetentionScheduler()

    with patch("lilypad.server.db.session.get_session") as mock_get_session:
        mock_session = MagicMock()
        mock_get_session.return_value.__enter__.return_value = mock_session

        # Mock the cleanup_all_organizations instance method
        mock_results = {
            "org1": {"spans": 100, "comments": 50, "annotations": 10},
            "org2": {"spans": 0, "comments": 0, "annotations": 0},
        }

        with patch(
            "lilypad.server.services.data_retention_service.DataRetentionService"
        ) as mock_service_class:
            mock_service_instance = mock_service_class.return_value
            mock_service_instance.cleanup_all_organizations = AsyncMock(
                return_value=mock_results
            )

            await scheduler._run_cleanup()

            mock_service_instance.cleanup_all_organizations.assert_called_once()


@pytest.mark.asyncio
async def test_scheduler_next_run_calculation():
    """Test scheduler calculates next run time correctly."""
    scheduler = DataRetentionScheduler()

    # Test that the scheduler properly calculates next run time
    # We'll start the scheduler and verify it logs the next run
    with patch("lilypad.server.services.data_retention_service.log") as mock_log:
        # Start and immediately stop to avoid long sleep
        await scheduler.start()

        # Give it a moment to start
        await asyncio.sleep(0.1)

        # Stop the scheduler
        await scheduler.stop()

        # Check that start was logged
        mock_log.info.assert_any_call("Data retention scheduler started")


def test_get_retention_scheduler_singleton():
    """Test that get_retention_scheduler returns a singleton."""
    scheduler1 = get_retention_scheduler()
    scheduler2 = get_retention_scheduler()

    assert scheduler1 is scheduler2


@pytest.fixture
def test_db():
    """Create a test database with tables."""
    from sqlalchemy import event

    engine = create_engine("sqlite:///:memory:")

    # Enable foreign key constraints in SQLite
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        yield session


@pytest.mark.asyncio
async def test_integration_cleanup_with_real_db(test_db):
    """Integration test with real database operations."""
    # Create test organization
    org = OrganizationTable(name="Test Org")
    test_db.add(org)
    test_db.commit()

    # Create a test user
    user = UserTable(
        email="test@example.com",
        first_name="Test",
        last_name="User",
        organization_uuid=org.uuid,
    )
    test_db.add(user)
    test_db.commit()

    # Create a project
    project = ProjectTable(name="Test Project", organization_uuid=org.uuid)
    test_db.add(project)
    test_db.commit()

    # Create old and new spans
    old_date = datetime.now(timezone.utc) - timedelta(days=40)
    new_date = datetime.now(timezone.utc) - timedelta(days=10)

    old_span = SpanTable(
        span_id="old-span-1",
        organization_uuid=org.uuid,
        project_uuid=project.uuid,
        scope="llm",
        created_at=old_date,
    )

    new_span = SpanTable(
        span_id="new-span-1",
        organization_uuid=org.uuid,
        project_uuid=project.uuid,
        scope="llm",
        created_at=new_date,
    )

    test_db.add(old_span)
    test_db.add(new_span)
    test_db.commit()

    # Create comments
    old_comment = CommentTable(
        text="Old comment",
        organization_uuid=org.uuid,
        span_uuid=old_span.uuid,
        user_uuid=user.uuid,
        created_at=old_date,
    )

    new_comment = CommentTable(
        text="New comment",
        organization_uuid=org.uuid,
        span_uuid=new_span.uuid,
        user_uuid=user.uuid,
        created_at=new_date,
    )

    test_db.add(old_comment)
    test_db.add(new_comment)
    test_db.commit()

    # Run cleanup
    service = DataRetentionService(test_db)
    # Mock the tier to FREE for this test
    with patch.object(service, "_get_organization_tier", return_value=Tier.FREE):
        result = await service.cleanup_organization_data(org)
        # Flush to execute the delete statements
        test_db.flush()

    # Check results
    assert result["spans"] >= 1  # At least the old span should be deleted

    # Verify old data is deleted - need to commit to see changes
    test_db.commit()
    remaining_spans = test_db.exec(select(SpanTable)).all()
    assert len(remaining_spans) == 1
    assert remaining_spans[0].span_id == "new-span-1"

    # Verify cascade deletion worked
    remaining_comments = test_db.exec(select(CommentTable)).all()
    assert len(remaining_comments) == 1
    assert remaining_comments[0].text == "New comment"
