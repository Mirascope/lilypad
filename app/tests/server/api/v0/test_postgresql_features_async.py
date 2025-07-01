"""Tests for PostgreSQL-specific features in async mode."""

import os

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from lilypad.server.models import ProjectTable
from tests.async_test_utils import AsyncDatabaseTestMixin, AsyncTestFactory


@pytest.mark.skipif(
    not (os.getenv("ENVIRONMENT") == "development" and os.getenv("DB_HOST")),
    reason="PostgreSQL tests only run in development environment with DB_HOST set",
)
class TestPostgreSQLFeaturesAsync(AsyncDatabaseTestMixin):
    """Test PostgreSQL-specific features."""

    @pytest.mark.asyncio
    async def test_jsonb_operations(
        self, async_session: AsyncSession, async_test_project: ProjectTable
    ):
        """Test JSONB field operations."""
        # Using SpanTable for JSONB testing since it has data field
        from lilypad.server.models import Scope, SpanTable, SpanType

        span = SpanTable(
            organization_uuid=async_test_project.organization_uuid,
            project_uuid=async_test_project.uuid,
            span_id="test_span_123",
            trace_id="test_trace_123",
            type=SpanType.FUNCTION,
            scope=Scope.LILYPAD,
            data={
                "name": "jsonb_test",
                "version": "1.0",
                "features": ["async", "postgres"],
                "config": {"nested": {"value": 42}},
            },
        )
        async_session.add(span)
        await async_session.flush()

        # Test JSONB query operations
        result = await async_session.execute(
            text("""
                SELECT span_id, data->>'version' as version 
                FROM spans 
                WHERE data @> '{"features": ["async"]}'::jsonb
            """)
        )
        row = result.first()
        assert row is not None
        assert row.version == "1.0"

        # Test JSONB path operations
        result = await async_session.execute(
            text("""
                SELECT data #>> '{config,nested,value}' as nested_value
                FROM spans
                WHERE data->>'name' = :name
            """).bindparams(name="jsonb_test")
        )
        row = result.first()
        assert row is not None and row.nested_value == "42"

    @pytest.mark.asyncio
    async def test_array_operations(self, async_session: AsyncSession):
        """Test array operations (if we had array fields)."""
        # This is a placeholder test showing how to test array operations
        # In a real scenario, you'd have a model with array fields

        # Create a test table with array field
        await async_session.execute(
            text("""
                CREATE TEMP TABLE test_arrays (
                    id SERIAL PRIMARY KEY,
                    tags TEXT[]
                )
            """)
        )

        # Insert data with arrays
        await async_session.execute(
            text("""
                INSERT INTO test_arrays (tags) 
                VALUES (:tags)
            """).bindparams(tags=["python", "async", "postgres"])
        )

        # Query array operations
        result = await async_session.execute(
            text("""
                SELECT * FROM test_arrays 
                WHERE 'async' = ANY(tags)
            """)
        )
        assert len(result.all()) == 1

    @pytest.mark.asyncio
    async def test_transaction_isolation_levels(self, async_session: AsyncSession):
        """Test different transaction isolation levels."""
        # Test READ COMMITTED (default)
        await async_session.execute(
            text("SET TRANSACTION ISOLATION LEVEL READ COMMITTED")
        )

        # Create a project
        from uuid import UUID

        project = ProjectTable(
            name="isolation_test",
            organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        )
        async_session.add(project)
        await async_session.flush()

        # In a real test, you'd test concurrent access patterns here
        assert project.uuid is not None

    @pytest.mark.asyncio
    async def test_deadlock_handling(self, async_session: AsyncSession):
        """Test deadlock detection and handling."""
        # This is a simplified test - real deadlock testing requires
        # multiple concurrent connections

        # PostgreSQL automatically detects and resolves deadlocks
        # by aborting one of the transactions
        try:
            # In production, this would involve multiple sessions
            # trying to lock resources in different orders
            await async_session.execute(text("SELECT pg_advisory_lock(1)"))
            # Release the lock
            await async_session.execute(text("SELECT pg_advisory_unlock(1)"))
        except Exception as e:
            # Handle deadlock errors (would be OperationalError with specific code)
            pytest.fail(f"Unexpected error: {e}")

    @pytest.mark.asyncio
    async def test_full_text_search(
        self, async_session: AsyncSession, async_test_project: ProjectTable
    ):
        """Test PostgreSQL full-text search capabilities."""
        # Create projects with searchable content
        projects = [
            ProjectTable(
                name="search_test_1_advanced_async_postgresql",
                organization_uuid=async_test_project.organization_uuid,
            ),
            ProjectTable(
                name="search_test_2_simple_sqlite_testing",
                organization_uuid=async_test_project.organization_uuid,
            ),
            ProjectTable(
                name="search_test_3_postgresql_features",
                organization_uuid=async_test_project.organization_uuid,
            ),
        ]

        for project in projects:
            async_session.add(project)
        await async_session.flush()

        # Test full-text search on name field
        result = await async_session.execute(
            text("""
                SELECT name
                FROM projects
                WHERE to_tsvector('english', name) @@ to_tsquery('english', 'postgresql')
                ORDER BY name
            """)
        )
        rows = result.all()
        assert len(rows) == 2  # search_test_1 and search_test_3 contain 'postgresql'

    @pytest.mark.asyncio
    async def test_window_functions(
        self, async_session: AsyncSession, async_test_project: ProjectTable
    ):
        """Test PostgreSQL window functions."""
        # Create multiple projects
        factory = AsyncTestFactory(async_session)
        for i in range(5):
            await factory.create(
                ProjectTable,
                name=f"window_test_{i}",
                organization_uuid=async_test_project.organization_uuid,
            )

        # Test window function query
        result = await async_session.execute(
            text("""
                SELECT 
                    name,
                    ROW_NUMBER() OVER (ORDER BY created_at) as row_num,
                    RANK() OVER (ORDER BY created_at) as rank
                FROM projects
                WHERE name LIKE 'window_test_%'
                ORDER BY row_num
            """)
        )
        rows = result.all()
        assert len(rows) == 5
        assert rows[0].row_num == 1
        assert rows[4].row_num == 5

    @pytest.mark.asyncio
    async def test_cte_recursive_queries(self, async_session: AsyncSession):
        """Test Common Table Expressions (CTEs) with recursion."""
        # Create a hierarchical structure (simulated)
        await async_session.execute(
            text("""
                CREATE TEMP TABLE test_hierarchy (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    parent_id INTEGER REFERENCES test_hierarchy(id)
                )
            """)
        )

        # Insert hierarchical data
        await async_session.execute(
            text("""
                INSERT INTO test_hierarchy (name, parent_id) VALUES
                ('root', NULL),
                ('child1', 1),
                ('child2', 1),
                ('grandchild1', 2),
                ('grandchild2', 2)
            """)
        )

        # Test recursive CTE
        result = await async_session.execute(
            text("""
                WITH RECURSIVE hierarchy AS (
                    SELECT id, name, parent_id, 0 as level
                    FROM test_hierarchy
                    WHERE parent_id IS NULL
                    
                    UNION ALL
                    
                    SELECT h.id, h.name, h.parent_id, p.level + 1
                    FROM test_hierarchy h
                    JOIN hierarchy p ON h.parent_id = p.id
                )
                SELECT * FROM hierarchy
                ORDER BY level, name
            """)
        )
        rows = result.all()
        assert len(rows) == 5
        assert rows[0].level == 0  # root
        assert rows[1].level == 1  # child1
        assert rows[3].level == 2  # grandchild1
