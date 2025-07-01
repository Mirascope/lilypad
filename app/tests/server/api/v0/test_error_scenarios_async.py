"""Error scenario tests for async infrastructure."""

import asyncio
import os
from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlmodel import select

from lilypad.server.models import OrganizationTable, ProjectTable
from tests.server.async_test_fixtures import (
    create_deadlock_scenario,
    simulate_database_error,
    test_session_recovery,
)


class TestAsyncErrorScenarios:
    """Test error handling and recovery in async operations."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_session_recovery_after_error(self, async_session: AsyncSession):
        """Test that session can recover after database errors."""
        # First, verify session works
        result = await async_session.execute(select(ProjectTable).limit(1))
        assert result is not None

        # Simulate an error
        await simulate_database_error(async_session)

        # Test recovery
        await test_session_recovery(async_session)

        # Verify session still works for normal operations
        from uuid import UUID

        project = ProjectTable(
            name="recovery_test",
            organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        )
        async_session.add(project)
        await async_session.flush()
        assert project.uuid is not None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_concurrent_transaction_conflicts(
        self, async_session: AsyncSession, async_test_project: ProjectTable
    ):
        """Test handling of concurrent transaction conflicts."""
        from sqlalchemy import text

        # Create a second session
        async with AsyncSession(async_session.bind) as session2:
            # Both sessions try to update the same record
            async def update_in_session1():
                await async_session.execute(
                    text("UPDATE projects SET name = :name WHERE uuid = :uuid"),
                    {
                        "name": "updated_by_session1",
                        "uuid": str(async_test_project.uuid),
                    },
                )
                await async_session.commit()

            async def update_in_session2():
                await session2.execute(
                    text("UPDATE projects SET name = :name WHERE uuid = :uuid"),
                    {
                        "name": "updated_by_session2",
                        "uuid": str(async_test_project.uuid),
                    },
                )
                await session2.commit()

            # Run concurrently - one should succeed, one might fail or be serialized
            results = await asyncio.gather(
                update_in_session1(), update_in_session2(), return_exceptions=True
            )

            # At least one should succeed
            successes = [r for r in results if not isinstance(r, Exception)]
            assert len(successes) >= 1

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_integrity_constraint_handling(
        self, async_session: AsyncSession, async_test_organization: OrganizationTable
    ):
        """Test proper handling of integrity constraints."""
        # Create a project
        # Type guard
        assert async_test_organization.uuid is not None

        project1 = ProjectTable(
            name="unique_project", organization_uuid=async_test_organization.uuid
        )
        async_session.add(project1)
        await async_session.flush()

        # Try to create another project with same name (if unique constraint exists)
        project2 = ProjectTable(
            name="unique_project", organization_uuid=async_test_organization.uuid
        )
        async_session.add(project2)

        # This might raise IntegrityError depending on schema
        try:
            await async_session.flush()
            # If no error, rollback to clean up
            await async_session.rollback()
        except IntegrityError:
            # Expected - properly handle the error
            await async_session.rollback()

        # Session should still be usable
        project3 = ProjectTable(
            name="different_project", organization_uuid=async_test_organization.uuid
        )
        async_session.add(project3)
        await async_session.flush()
        assert project3.uuid is not None

    @pytest.mark.asyncio
    @pytest.mark.skipif(
        not (os.getenv("ENVIRONMENT") == "development" and os.getenv("DB_HOST")),
        reason="Deadlock tests require PostgreSQL",
    )
    async def test_deadlock_detection(self, async_db_session: AsyncSession):
        """Test deadlock detection and handling."""
        # Create test data
        org_uuid = uuid4()
        project_uuid = uuid4()

        org = OrganizationTable(uuid=org_uuid, name="deadlock_test_org")
        project = ProjectTable(
            uuid=project_uuid, name="deadlock_test_project", organization_uuid=org_uuid
        )

        async_db_session.add(org)
        async_db_session.add(project)
        await async_db_session.commit()

        # Create two sessions for deadlock scenario
        engine = async_db_session.bind
        async with AsyncSession(engine) as session1:
            async with AsyncSession(engine) as session2:
                results = await create_deadlock_scenario(session1, session2)

                # One transaction should fail with deadlock error
                errors = [r for r in results if isinstance(r, Exception)]
                assert len(errors) >= 1

                # Check for deadlock-related error
                deadlock_errors = [
                    e
                    for e in errors
                    if "deadlock" in str(e).lower() or "lock" in str(e).lower()
                ]
                # Note: SQLite doesn't have real deadlock detection
                # Check if using PostgreSQL
                engine_url = str(
                    getattr(engine, "url", None)
                    or getattr(getattr(engine, "engine", None), "url", "")
                )
                if "postgresql" in engine_url:
                    assert len(deadlock_errors) > 0

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_connection_failure_recovery(self):
        """Test recovery from connection failures."""
        # Create an engine with invalid connection
        invalid_engine = create_async_engine(
            "postgresql+asyncpg://invalid:invalid@localhost:9999/invalid",
            pool_pre_ping=True,  # Enable connection health checks
            pool_size=1,
            max_overflow=0,
        )

        async with AsyncSession(invalid_engine) as session:
            with pytest.raises(OperationalError):
                await session.execute(select(ProjectTable))

        # Engine should handle the failure gracefully
        await invalid_engine.dispose()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_transaction_rollback_cascade(
        self, async_session: AsyncSession, async_test_organization: OrganizationTable
    ):
        """Test that rollback properly cascades through operations."""
        # Start a transaction
        async with async_session.begin_nested() as savepoint:
            # Create multiple related objects
            # Type guard
            assert async_test_organization.uuid is not None

            project = ProjectTable(
                name="rollback_test_project",
                organization_uuid=async_test_organization.uuid,
            )
            async_session.add(project)
            await async_session.flush()

            # Create related data
            from lilypad.server.models import FunctionTable

            # Type guard
            assert project.uuid is not None

            function = FunctionTable(
                name="rollback_test_function",
                project_uuid=project.uuid,
                organization_uuid=async_test_organization.uuid,
                signature="def test(): pass",
                code="def test(): pass",
                hash="test_hash",
                arg_types={},
                version_num=1,
            )
            async_session.add(function)
            await async_session.flush()

            # Verify they exist in the transaction
            assert project.uuid is not None
            assert function.uuid is not None

            # Rollback the transaction
            await savepoint.rollback()

        # Verify rollback worked - objects should not exist
        result = await async_session.execute(
            select(ProjectTable).where(ProjectTable.name == "rollback_test_project")
        )
        assert result.scalar_one_or_none() is None

        result = await async_session.execute(
            select(FunctionTable).where(FunctionTable.name == "rollback_test_function")
        )
        assert result.scalar_one_or_none() is None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_async_context_manager_error_handling(
        self, async_test_organization: OrganizationTable
    ):
        """Test error handling in async context managers."""
        from lilypad.server.db.session import get_async_session

        # Test that session properly cleans up on error
        with pytest.raises(RuntimeError):
            async for session in get_async_session():
                # Create some data
                # Type guard
                assert async_test_organization.uuid is not None

                project = ProjectTable(
                    name="context_error_test",
                    organization_uuid=async_test_organization.uuid,
                )
                session.add(project)
                await session.flush()

                # Simulate an error
                raise RuntimeError("Simulated error in context")

        # Verify we can still get a new session after error
        async for session in get_async_session():
            result = await session.execute(select(ProjectTable).limit(1))
            assert result is not None
            break  # Exit after verification

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_concurrent_session_isolation(
        self, async_session: AsyncSession, async_test_organization: OrganizationTable
    ):
        """Test that concurrent sessions are properly isolated."""
        # Create initial data
        # Type guard
        assert async_test_organization.uuid is not None

        project = ProjectTable(
            name="isolation_test",
            organization_uuid=async_test_organization.uuid,
        )
        async_session.add(project)
        await async_session.commit()

        # Create multiple concurrent sessions
        async def read_project(session_id: int):
            async with AsyncSession(async_session.bind) as session:
                # Each session reads the project
                stmt = select(ProjectTable).where(ProjectTable.uuid == project.uuid)
                result = await session.execute(stmt)
                proj = result.scalar_one()

                # Simulate some processing time
                await asyncio.sleep(0.01)

                # Try to update (might conflict)
                # Skip metadata update as ProjectTable doesn't have metadata field
                proj.name = f"{proj.name}_updated_{session_id}"

                try:
                    await session.commit()
                    return f"Session {session_id} succeeded"
                except Exception as e:
                    await session.rollback()
                    return f"Session {session_id} failed: {e}"

        # Run multiple sessions concurrently
        results = await asyncio.gather(*[read_project(i) for i in range(5)])

        # At least one should succeed
        successes = [r for r in results if "succeeded" in r]
        assert len(successes) >= 1

        # Verify final state is consistent
        stmt = select(ProjectTable).where(ProjectTable.uuid == project.uuid)
        result = await async_session.execute(stmt)
        final_project = result.scalar_one()
        # Just verify the project still exists
        assert final_project.name.startswith("isolation_test")
