"""Async tests for the spans API."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from lilypad.server.models import (
    FunctionTable,
    ProjectTable,
    Scope,
    SpanTable,
    SpanType,
    UserTable,
)
from tests.async_test_utils import AsyncDatabaseTestMixin, AsyncTestFactory


class TestSpansAPIAsync(AsyncDatabaseTestMixin):
    """Test spans API endpoints asynchronously."""

    @pytest_asyncio.fixture
    async def test_spans(
        self,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
        async_test_function: FunctionTable,
        async_test_user: UserTable,
    ) -> list[SpanTable]:
        """Create test spans with various timestamps."""
        factory = AsyncTestFactory(async_session)
        now = datetime.now(timezone.utc)
        spans = []

        # Create spans with different timestamps
        for i in range(5):
            # Root span
            root_span = await factory.create(
                SpanTable,
                organization_uuid=async_test_project.organization_uuid,
                project_uuid=async_test_project.uuid,
                span_id=f"span_root_{i}",
                trace_id=f"trace_{i}",
                parent_span_id=None,
                type=SpanType.FUNCTION,
                function_uuid=async_test_function.uuid,
                scope=Scope.LILYPAD,
                cost=0.001 * (i + 1),
                input_tokens=100 * (i + 1),
                output_tokens=50 * (i + 1),
                duration_ms=1000 + i * 100,
                created_at=now - timedelta(minutes=i),
                data={
                    "name": f"test_function_{i}",
                    "attributes": {
                        "lilypad.type": "function",
                        "lilypad.function.uuid": str(async_test_function.uuid),
                    },
                    "events": [],
                },
            )
            spans.append(root_span)

            # Child span
            child_span = await factory.create(
                SpanTable,
                organization_uuid=async_test_project.organization_uuid,
                project_uuid=async_test_project.uuid,
                span_id=f"span_child_{i}",
                trace_id=f"trace_{i}",
                parent_span_id=f"span_root_{i}",
                type=SpanType.FUNCTION,
                function_uuid=async_test_function.uuid,
                scope=Scope.LLM,
                cost=0.0005 * (i + 1),
                input_tokens=50 * (i + 1),
                output_tokens=25 * (i + 1),
                duration_ms=500 + i * 50,
                created_at=now - timedelta(minutes=i),
                data={
                    "name": f"child_function_{i}",
                    "attributes": {
                        "lilypad.type": "function",
                    },
                    "events": [],
                },
            )
            spans.append(child_span)

        return spans

    # ===== Parameterized Tests for Getting Recent Spans =====

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "since_minutes,expected_count,expected_span_ids",
        [
            (None, 1, ["span_root_0"]),  # Default 30 seconds
            (3, 3, ["span_root_0", "span_root_1", "span_root_2"]),  # Last 3 minutes
            (
                10,
                5,
                [
                    "span_root_0",
                    "span_root_1",
                    "span_root_2",
                    "span_root_3",
                    "span_root_4",
                ],
            ),  # All spans
        ],
    )
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    @pytest.mark.asyncio
    async def test_get_recent_spans_since(
        self,
        async_client: AsyncClient,
        test_spans: list[SpanTable],
        since_minutes: int | None,
        expected_count: int,
        expected_span_ids: list[str],
    ):
        """Test getting recent spans with since parameter."""
        params = {"limit": 100}
        if since_minutes is not None:
            params["since_minutes"] = since_minutes

        response = await async_client.get("/spans/recent", params=params)

        assert response.status_code == 200
        data = response.json()
        # Filter for root spans only
        root_spans = [s for s in data if s.get("parent_span_id") is None]
        assert len(root_spans) == expected_count
        actual_span_ids = [s["span_id"] for s in root_spans]
        for expected_id in expected_span_ids:
            assert expected_id in actual_span_ids

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_recent_spans_with_limit(
        self, async_client: AsyncClient, test_spans: list[SpanTable]
    ):
        """Test getting recent spans with limit parameter."""
        response = await async_client.get(
            "/spans/recent", params={"limit": 3, "since_minutes": 10}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 3

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_span_by_uuid(
        self, async_client: AsyncClient, test_spans: list[SpanTable]
    ):
        """Test getting a single span by UUID."""
        test_span = test_spans[0]
        response = await async_client.get(f"/spans/{test_span.uuid}")

        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == str(test_span.uuid)
        assert data["span_id"] == test_span.span_id

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_span_not_found(self, async_client: AsyncClient):
        """Test getting a non-existent span."""
        fake_uuid = uuid4()
        response = await async_client.get(f"/spans/{fake_uuid}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_span(
        self,
        async_client: AsyncClient,
        async_test_project: ProjectTable,
        async_test_function: FunctionTable,
    ):
        """Test creating a new span."""
        span_data = {
            "project_uuid": str(async_test_project.uuid),
            "span_id": "new_span_123",
            "trace_id": "new_trace_123",
            "parent_span_id": None,
            "type": "FUNCTION",
            "function_uuid": str(async_test_function.uuid),
            "scope": "LILYPAD",
            "data": {
                "name": "new_test_span",
                "attributes": {"test": True},
                "events": [],
            },
        }

        response = await async_client.post("/spans", json=span_data)
        assert response.status_code == 201
        created = response.json()
        assert created["span_id"] == "new_span_123"
        assert created["trace_id"] == "new_trace_123"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_span_metadata(
        self, async_client: AsyncClient, test_spans: list[SpanTable]
    ):
        """Test updating span metadata."""
        test_span = test_spans[0]
        update_data = {
            "metadata": {
                "updated": True,
                "tags": ["test", "async"],
            }
        }

        response = await async_client.patch(
            f"/spans/{test_span.uuid}", json=update_data
        )
        assert response.status_code == 200
        updated = response.json()
        assert updated["metadata"]["updated"] is True
        assert "test" in updated["metadata"]["tags"]

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_span(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
    ):
        """Test deleting a span."""
        factory = AsyncTestFactory(async_session)

        # Create a span to delete
        span_to_delete = await factory.create(
            SpanTable,
            organization_uuid=async_test_project.organization_uuid,
            project_uuid=async_test_project.uuid,
            span_id="span_to_delete",
            trace_id="trace_to_delete",
            parent_span_id=None,
            type=SpanType.FUNCTION,
            scope=Scope.LILYPAD,
            data={"name": "delete_me"},
        )

        response = await async_client.delete(f"/spans/{span_to_delete.uuid}")
        assert response.status_code == 200

        # Verify it's deleted
        response = await async_client.get(f"/spans/{span_to_delete.uuid}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_trace_spans(
        self, async_client: AsyncClient, test_spans: list[SpanTable]
    ):
        """Test getting all spans in a trace."""
        # Get spans from trace_0
        response = await async_client.get("/spans/trace/trace_0")
        assert response.status_code == 200

        trace_spans = response.json()
        assert len(trace_spans) == 2  # root and child
        span_ids = [s["span_id"] for s in trace_spans]
        assert "span_root_0" in span_ids
        assert "span_child_0" in span_ids

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_span_aggregation(
        self, async_client: AsyncClient, test_spans: list[SpanTable]
    ):
        """Test span aggregation endpoint."""
        response = await async_client.get(
            "/spans/aggregate",
            params={
                "group_by": "type",
                "since_minutes": 10,
            },
        )
        assert response.status_code == 200

        aggregates = response.json()
        # Should have aggregates for FUNCTION type
        function_agg = next((a for a in aggregates if a["type"] == "FUNCTION"), None)
        assert function_agg is not None
        assert function_agg["count"] > 0
        assert function_agg["total_cost"] > 0

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_span_search(
        self, async_client: AsyncClient, test_spans: list[SpanTable]
    ):
        """Test searching spans by attributes."""
        response = await async_client.get(
            "/spans/search",
            params={
                "query": "async_test_function",
                "limit": 10,
            },
        )
        assert response.status_code == 200

        results = response.json()
        assert len(results) > 0
        # All results should contain 'async_test_function' in their data
        for span in results:
            assert "async_test_function" in str(span["data"])

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_span_export(
        self, async_client: AsyncClient, test_spans: list[SpanTable]
    ):
        """Test exporting spans in different formats."""
        # Test JSON export
        response = await async_client.get(
            "/spans/export",
            params={
                "format": "json",
                "since_minutes": 10,
            },
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"

        # Test CSV export
        response = await async_client.get(
            "/spans/export",
            params={
                "format": "csv",
                "since_minutes": 10,
            },
        )
        assert response.status_code == 200
        assert "text/csv" in response.headers["content-type"]

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_span_metrics(
        self, async_client: AsyncClient, test_spans: list[SpanTable]
    ):
        """Test span metrics endpoint."""
        response = await async_client.get(
            "/spans/metrics", params={"since_minutes": 10}
        )
        assert response.status_code == 200

        metrics = response.json()
        assert "total_spans" in metrics
        assert "total_cost" in metrics
        assert "total_tokens" in metrics
        assert "average_duration_ms" in metrics
        assert metrics["total_spans"] == len(test_spans)
