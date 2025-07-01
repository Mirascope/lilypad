"""Performance regression tests for async infrastructure."""

import asyncio
import time
from datetime import datetime, timezone

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from lilypad.server.models import ProjectTable, Scope, SpanTable, SpanType
from tests.server.async_test_fixtures import PerformanceTracker


class TestAsyncPerformance:
    """Test performance characteristics of async operations."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_concurrent_reads_performance(
        self,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
        performance_tracker: PerformanceTracker,
    ):
        """Test performance of concurrent read operations."""
        # Create test data
        projects = []
        for i in range(10):
            project = ProjectTable(
                name=f"perf_test_{i}",
                organization_uuid=async_test_project.organization_uuid,
            )
            async_session.add(project)
            projects.append(project)
        await async_session.flush()

        # Test concurrent reads
        async def read_project(project_uuid):
            from sqlmodel import select

            stmt = select(ProjectTable).where(ProjectTable.uuid == project_uuid)
            result = await async_session.execute(stmt)
            return result.scalar_one()

        # Measure sequential reads
        start_sequential = time.perf_counter()
        for project in projects:
            await read_project(project.uuid)
        sequential_time = time.perf_counter() - start_sequential

        # Measure concurrent reads
        start_concurrent = time.perf_counter()
        await asyncio.gather(*[read_project(p.uuid) for p in projects])
        concurrent_time = time.perf_counter() - start_concurrent

        # Concurrent should be faster than sequential
        assert concurrent_time < sequential_time * 0.8  # At least 20% faster

        # Track for regression
        await performance_tracker.track_operation(
            "concurrent_reads_10",
            asyncio.sleep(0),  # Dummy operation
        )
        performance_tracker.metrics["concurrent_reads_10"]["elapsed"] = concurrent_time

        # Assert no regression (baseline: 100ms for 10 reads)
        performance_tracker.assert_no_regression("concurrent_reads_10", baseline_ms=100)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_bulk_insert_performance(
        self,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
        performance_tracker: PerformanceTracker,
    ):
        """Test performance of bulk insert operations."""
        # Prepare data
        spans_data = []
        for i in range(100):
            spans_data.append(
                {
                    "name": f"bulk_span_{i}",
                    "start_time": datetime.now(timezone.utc),
                    "end_time": datetime.now(timezone.utc),
                    "organization_uuid": async_test_project.organization_uuid,
                    "project_uuid": async_test_project.uuid,
                    "type": SpanType.FUNCTION,
                }
            )

        # Test single insert performance
        async def single_inserts():
            for data in spans_data[:10]:  # Only first 10 for comparison
                span = SpanTable(**data)
                async_session.add(span)
                await async_session.flush()

        # Test bulk insert performance
        async def bulk_insert():
            spans = [SpanTable(**data) for data in spans_data]
            async_session.add_all(spans)
            await async_session.flush()

        # Measure single inserts
        start_single = time.perf_counter()
        await single_inserts()
        single_time = time.perf_counter() - start_single

        # Clear session
        await async_session.rollback()

        # Measure bulk insert
        start_bulk = time.perf_counter()
        await performance_tracker.track_operation("bulk_insert_100", bulk_insert())
        bulk_time = time.perf_counter() - start_bulk

        # Bulk should be much faster per record
        assert (bulk_time / 100) < (single_time / 10) * 0.5

        # Assert no regression (baseline: 500ms for 100 inserts)
        performance_tracker.assert_no_regression("bulk_insert_100", baseline_ms=500)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_connection_pool_performance(
        self, async_session: AsyncSession, connection_pool_tester
    ):
        """Test connection pool behavior under load."""
        # Test with moderate load
        results, errors = await connection_pool_tester(num_connections=10)
        assert len(errors) == 0, f"Connection pool errors: {errors}"
        assert len(results) == 10

        # Test with high load (might hit pool limits)
        results, errors = await connection_pool_tester(num_connections=50)
        # Some errors might be acceptable at high load
        error_rate = len(errors) / len(results)
        assert error_rate < 0.1, f"Too many connection errors: {error_rate:.1%}"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_query_complexity_performance(
        self,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
        performance_tracker: PerformanceTracker,
    ):
        """Test performance of complex queries."""
        from sqlalchemy import text

        # Create test data with relationships
        for i in range(20):
            span = SpanTable(
                span_id=f"complex_span_{i}",
                trace_id=f"complex_trace_{i}",
                organization_uuid=async_test_project.organization_uuid,
                project_uuid=async_test_project.uuid,
                type=SpanType.FUNCTION,
                scope=Scope.LILYPAD,
                data={"name": f"complex_span_{i}", "complexity": i % 5},
            )
            async_session.add(span)
        await async_session.flush()

        # Test simple query
        async def simple_query():
            result = await async_session.execute(
                text("SELECT COUNT(*) FROM spans WHERE project_uuid = :project_uuid"),
                {"project_uuid": str(async_test_project.uuid)},
            )
            return result.scalar()

        # Test complex query with aggregations
        async def complex_query():
            result = await async_session.execute(
                text("""
                    SELECT 
                        project_uuid,
                        span_type,
                        COUNT(*) as count,
                        AVG(EXTRACT(EPOCH FROM (end_time - start_time))) as avg_duration
                    FROM spans
                    WHERE project_uuid = :project_uuid
                    GROUP BY project_uuid, type
                    HAVING COUNT(*) > 0
                    ORDER BY count DESC
                """),
                {"project_uuid": str(async_test_project.uuid)},
            )
            return result.all()

        # Measure performance
        await performance_tracker.track_operation("simple_query", simple_query())
        await performance_tracker.track_operation("complex_query", complex_query())

        # Complex query should still be reasonably fast
        performance_tracker.assert_no_regression("simple_query", baseline_ms=10)
        performance_tracker.assert_no_regression("complex_query", baseline_ms=50)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_sync_vs_async_performance_comparison(
        self,
        async_session: AsyncSession,
        session,  # sync session
        async_test_project: ProjectTable,
    ):
        """Compare performance between sync and async operations."""
        from sqlmodel import select

        # Define operations
        async def async_operations():
            for _i in range(50):
                stmt = select(ProjectTable).where(
                    ProjectTable.uuid == async_test_project.uuid
                )
                result = await async_session.execute(stmt)
                _ = result.scalar_one()

        def sync_operations():
            for _i in range(50):
                stmt = select(ProjectTable).where(
                    ProjectTable.uuid == async_test_project.uuid
                )
                result = session.exec(stmt)
                _ = result.first()

        # Measure async performance
        start_async = time.perf_counter()
        await async_operations()
        async_time = time.perf_counter() - start_async

        # Measure sync performance
        start_sync = time.perf_counter()
        sync_operations()
        sync_time = time.perf_counter() - start_sync

        # Async should be comparable or better than sync
        # Allow some overhead for async coordination
        assert async_time < sync_time * 1.2
