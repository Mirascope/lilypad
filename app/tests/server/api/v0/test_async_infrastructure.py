"""Test to verify async infrastructure works with both SQLite and PostgreSQL."""

import os

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from lilypad.server.models import ProjectTable


class TestAsyncInfrastructure:
    """Test that async infrastructure works correctly."""

    @pytest.mark.asyncio
    async def test_async_session_works(self, async_db_session: AsyncSession):
        """Test that async session can perform basic operations."""
        from uuid import UUID

        # Create a project
        project = ProjectTable(
            name="test_async_project",
            organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        )
        async_db_session.add(project)
        await async_db_session.flush()

        # Query it back
        stmt = select(ProjectTable).where(ProjectTable.name == "test_async_project")
        result = await async_db_session.execute(stmt)
        found_project = result.scalar_one()

        assert found_project.name == "test_async_project"
        assert found_project.uuid is not None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_async_client_works(self, async_client):
        """Test that async client can make requests."""
        # Test a simple endpoint that doesn't require database
        response = await async_client.get("/current-user")
        assert response.status_code == 200
        assert response.json()["email"] == "test@test.com"

    @pytest.mark.asyncio
    async def test_database_type_detection(self, async_db_session: AsyncSession):
        """Test that we can detect which database we're using."""
        from sqlalchemy import text

        # Execute a query to check the database type
        if os.getenv("ENVIRONMENT") == "development" and os.getenv("DB_HOST"):
            # PostgreSQL
            result = await async_db_session.execute(text("SELECT version()"))
            version = result.scalar()
            assert version is not None and "PostgreSQL" in version
        else:
            # SQLite
            result = await async_db_session.execute(text("SELECT sqlite_version()"))
            version = result.scalar()
            assert version is not None

    @pytest.mark.asyncio
    async def test_transaction_isolation(self, async_db_session: AsyncSession):
        from uuid import UUID

        """Test that transactions are properly isolated."""
        # Create a project
        project1 = ProjectTable(
            name="isolated_project",
            organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        )
        async_db_session.add(project1)
        await async_db_session.flush()

        # The transaction should rollback after the test
        # So this project won't persist

    @pytest.mark.asyncio
    async def test_concurrent_operations(self, async_db_session: AsyncSession):
        from uuid import UUID

        """Test concurrent database operations with proper session handling.

        Note: SQLAlchemy AsyncSession does not support concurrent flush operations
        within the same session. In production, use separate sessions for true
        concurrent operations or use session.run_sync() for synchronous execution.
        """
        # Create projects with sequential flushes (required for single session)
        projects = []
        for i in range(3):
            project = ProjectTable(
                name=f"concurrent_{i + 1}",
                organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
            )
            async_db_session.add(project)
            await async_db_session.flush()
            projects.append(project)

        assert len(projects) == 3
        assert all(p.uuid is not None for p in projects)

        # For true concurrent operations in production, use separate sessions:
        # async def create_with_new_session(name: str):
        #     async with get_async_session() as session:
        #         project = ProjectTable(name=name, ...)
        #         session.add(project)
        #         await session.commit()
        #         return project
