"""Comprehensive tests for spans API to achieve 100% coverage."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.server.models import (
    FunctionTable,
    ProjectTable,
    Scope,
    SpanTable,
)
from lilypad.server.services.spans import TimeFrame


@pytest.fixture
def test_spans_comprehensive(
    session: Session,
    test_project: ProjectTable,
    test_function: FunctionTable,
    test_user,
) -> list[SpanTable]:
    """Create comprehensive test spans for all API endpoints."""
    now = datetime.now(timezone.utc)
    spans = []

    # Create multiple spans for testing
    for i in range(3):
        span = SpanTable(
            organization_uuid=test_project.organization_uuid,
            project_uuid=test_project.uuid,
            span_id=f"test_span_{i}",
            trace_id=f"test_trace_{i}",
            parent_span_id=None,
            type="function",
            function_uuid=test_function.uuid,
            scope=Scope.LILYPAD,
            cost=0.001 * (i + 1),
            input_tokens=100 * (i + 1),
            output_tokens=50 * (i + 1),
            duration_ms=1000 + i * 100,
            created_at=now - timedelta(minutes=i),
            data={
                "name": f"test_span_{i}",
                "attributes": {
                    "lilypad.type": "function",
                    "lilypad.function.uuid": str(test_function.uuid),
                    "test_data": f"value_{i}",
                },
            },
        )
        session.add(span)
        spans.append(span)

    session.commit()
    for span in spans:
        session.refresh(span)

    return spans


class TestGetSpan:
    """Test get_span endpoint."""

    def test_get_span_success(
        self, client: TestClient, test_spans_comprehensive: list[SpanTable]
    ):
        """Test getting span by UUID successfully."""
        span = test_spans_comprehensive[0]

        response = client.get(f"/spans/{span.uuid}")

        assert response.status_code == 200
        data = response.json()
        assert data["span_id"] == span.span_id
        assert data["uuid"] == str(span.uuid)
        assert data["project_uuid"] == str(span.project_uuid)

    def test_get_span_not_found(self, client: TestClient):
        """Test getting span by UUID when not found."""
        fake_uuid = uuid4()

        response = client.get(f"/spans/{fake_uuid}")

        assert response.status_code == 404
        assert "Span not found" in response.json()["detail"]


class TestGetSpanBySpanId:
    """Test get_span_by_span_id endpoint."""

    def test_get_span_by_span_id_success(
        self, client: TestClient, test_spans_comprehensive: list[SpanTable]
    ):
        """Test getting span by project UUID and span ID successfully."""
        span = test_spans_comprehensive[0]

        response = client.get(f"/projects/{span.project_uuid}/spans/{span.span_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["span_id"] == span.span_id
        assert data["uuid"] == str(span.uuid)
        assert data["project_uuid"] == str(span.project_uuid)

    def test_get_span_by_span_id_not_found(
        self, client: TestClient, test_project: ProjectTable
    ):
        """Test getting span by span ID when not found."""
        response = client.get(f"/projects/{test_project.uuid}/spans/nonexistent_span")

        assert response.status_code == 404
        assert "Span not found" in response.json()["detail"]


class TestUpdateSpan:
    """Test update_span endpoint."""

    def test_update_span_success(
        self, client: TestClient, test_spans_comprehensive: list[SpanTable]
    ):
        """Test updating span successfully."""
        span = test_spans_comprehensive[0]
        update_data = {
            "data": {
                "attributes": {
                    "updated_field": "updated_value",
                    "lilypad.type": "function",
                }
            }
        }

        response = client.patch(f"/spans/{span.uuid}", json=update_data)

        assert response.status_code == 200


class TestAggregatesByProject:
    """Test get_aggregates_by_project_uuid endpoint."""

    def test_get_aggregates_by_project_uuid(
        self,
        client: TestClient,
        test_project: ProjectTable,
        test_spans_comprehensive: list[SpanTable],
    ):
        """Test getting aggregated metrics by project UUID."""
        response = client.get(
            f"/projects/{test_project.uuid}/spans/metadata",
            params={"time_frame": TimeFrame.LAST_7_DAYS.value},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_aggregates_by_project_uuid_different_timeframes(
        self,
        client: TestClient,
        test_project: ProjectTable,
        test_spans_comprehensive: list[SpanTable],
    ):
        """Test getting aggregated metrics with different time frames."""
        for time_frame in [
            TimeFrame.LAST_24_HOURS,
            TimeFrame.LAST_7_DAYS,
            TimeFrame.LAST_30_DAYS,
        ]:
            response = client.get(
                f"/projects/{test_project.uuid}/spans/metadata",
                params={"time_frame": time_frame.value},
            )

            assert response.status_code == 200


class TestAggregatesByFunction:
    """Test get_aggregates_by_function_uuid endpoint."""

    def test_get_aggregates_by_function_uuid(
        self,
        client: TestClient,
        test_project: ProjectTable,
        test_function: FunctionTable,
        test_spans_comprehensive: list[SpanTable],
    ):
        """Test getting aggregated metrics by function UUID."""
        response = client.get(
            f"/projects/{test_project.uuid}/functions/{test_function.uuid}/spans/metadata",
            params={"time_frame": TimeFrame.LAST_7_DAYS.value},
        )

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)


class TestSearchTraces:
    """Test search_traces endpoint."""

    @patch("lilypad.server.api.v0.spans_api.get_opensearch_service")
    def test_search_traces_opensearch_disabled(
        self, mock_get_opensearch, client: TestClient, test_project: ProjectTable
    ):
        """Test search traces when OpenSearch is disabled."""
        # Mock OpenSearch service as disabled
        mock_opensearch = Mock()
        mock_opensearch.is_enabled = False
        mock_get_opensearch.return_value = mock_opensearch

        response = client.get(
            f"/projects/{test_project.uuid}/spans", params={"query": "test"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch("lilypad.server.api.v0.spans_api.get_opensearch_service")
    def test_search_traces_opensearch_enabled_empty_results(
        self, mock_get_opensearch, client: TestClient, test_project: ProjectTable
    ):
        """Test search traces when OpenSearch is enabled but returns no results."""
        # Mock OpenSearch service as enabled with empty results
        mock_opensearch = Mock()
        mock_opensearch.is_enabled = True
        mock_opensearch.search_traces.return_value = []
        mock_get_opensearch.return_value = mock_opensearch

        response = client.get(
            f"/projects/{test_project.uuid}/spans", params={"query": "test"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data == []

    @patch("lilypad.server.api.v0.spans_api.get_opensearch_service")
    def test_search_traces_opensearch_enabled_with_results(
        self,
        mock_get_opensearch,
        client: TestClient,
        test_project: ProjectTable,
        test_function: FunctionTable,
    ):
        """Test search traces when OpenSearch returns results."""
        # Mock OpenSearch service with results
        mock_opensearch = Mock()
        mock_opensearch.is_enabled = True

        # Mock search results
        span_uuid = str(uuid4())
        mock_hit = {
            "_id": span_uuid,
            "_score": 1.0,
            "_source": {
                "span_id": "test_span_search",
                "parent_span_id": None,
                "organization_uuid": str(test_project.organization_uuid),
                "function_uuid": str(test_function.uuid),
                "scope": "lilypad",
                "type": "function",
                "cost": 0.001,
                "input_tokens": 100,
                "output_tokens": 50,
                "duration_ms": 1000,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "data": {"attributes": {"test": "data"}},
            },
        }

        mock_opensearch.search_traces.return_value = [mock_hit]
        mock_get_opensearch.return_value = mock_opensearch

        response = client.get(
            f"/projects/{test_project.uuid}/spans", params={"query": "test"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["span_id"] == "test_span_search"
        assert data[0]["score"] == 1.0

    @patch("lilypad.server.api.v0.spans_api.get_opensearch_service")
    def test_search_traces_parent_child_relationships(
        self,
        mock_get_opensearch,
        client: TestClient,
        test_project: ProjectTable,
        test_function: FunctionTable,
    ):
        """Test search traces with parent-child relationships."""
        mock_opensearch = Mock()
        mock_opensearch.is_enabled = True

        # Mock parent and child spans
        parent_span_uuid = str(uuid4())
        child_span_uuid = str(uuid4())

        mock_hits = [
            {
                "_id": parent_span_uuid,
                "_score": 1.0,
                "_source": {
                    "span_id": "parent_span",
                    "parent_span_id": None,
                    "organization_uuid": str(test_project.organization_uuid),
                    "function_uuid": str(test_function.uuid),
                    "scope": "lilypad",
                    "type": "function",
                    "cost": 0.001,
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "duration_ms": 1000,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "data": {"attributes": {"test": "parent"}},
                },
            },
            {
                "_id": child_span_uuid,
                "_score": 0.8,
                "_source": {
                    "span_id": "child_span",
                    "parent_span_id": "parent_span",
                    "organization_uuid": str(test_project.organization_uuid),
                    "function_uuid": str(test_function.uuid),
                    "scope": "llm",
                    "type": "function",
                    "cost": 0.0005,
                    "input_tokens": 50,
                    "output_tokens": 25,
                    "duration_ms": 500,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "data": {"attributes": {"test": "child"}},
                },
            },
        ]

        mock_opensearch.search_traces.return_value = mock_hits
        mock_get_opensearch.return_value = mock_opensearch

        response = client.get(
            f"/projects/{test_project.uuid}/spans", params={"query": "test"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should return only root span (parent) with child attached
        assert len(data) == 1
        assert data[0]["span_id"] == "parent_span"
        assert len(data[0]["child_spans"]) == 1
        assert data[0]["child_spans"][0]["span_id"] == "child_span"

    @patch("lilypad.server.api.v0.spans_api.get_opensearch_service")
    def test_search_traces_no_function_uuid(
        self, mock_get_opensearch, client: TestClient, test_project: ProjectTable
    ):
        """Test search traces with spans that have no function UUID."""
        mock_opensearch = Mock()
        mock_opensearch.is_enabled = True

        mock_hit = {
            "_id": str(uuid4()),
            "_score": 1.0,
            "_source": {
                "span_id": "no_function_span",
                "parent_span_id": None,
                "organization_uuid": str(test_project.organization_uuid),
                "function_uuid": None,  # No function UUID
                "scope": "lilypad",
                "type": "function",
                "cost": 0.001,
                "input_tokens": 100,
                "output_tokens": 50,
                "duration_ms": 1000,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "data": {"attributes": {"test": "data"}},
            },
        }

        mock_opensearch.search_traces.return_value = [mock_hit]
        mock_get_opensearch.return_value = mock_opensearch

        response = client.get(
            f"/projects/{test_project.uuid}/spans", params={"query": "test"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["span_id"] == "no_function_span"
        assert data[0]["function_uuid"] is None


class TestDeleteSpans:
    """Test delete_spans endpoint."""

    def test_delete_spans_success(
        self, client: TestClient, test_spans_comprehensive: list[SpanTable]
    ):
        """Test deleting span successfully."""
        span = test_spans_comprehensive[0]

        response = client.delete(f"/projects/{span.project_uuid}/spans/{span.uuid}")

        assert response.status_code == 200
        assert response.json() is True

    @patch("lilypad.server.api.v0.spans_api.get_opensearch_service")
    def test_delete_spans_with_opensearch_enabled(
        self,
        mock_get_opensearch,
        client: TestClient,
        test_spans_comprehensive: list[SpanTable],
    ):
        """Test deleting span with OpenSearch enabled."""
        span = test_spans_comprehensive[0]

        # Mock OpenSearch service
        mock_opensearch = Mock()
        mock_opensearch.is_enabled = True
        mock_get_opensearch.return_value = mock_opensearch

        response = client.delete(f"/projects/{span.project_uuid}/spans/{span.uuid}")

        assert response.status_code == 200
        assert response.json() is True

    @patch("lilypad.server.api.v0.spans_api.SpanService")
    def test_delete_spans_failure(
        self, mock_span_service_cls, client: TestClient, test_project: ProjectTable
    ):
        """Test deleting span when service raises exception."""
        # Mock service to raise exception
        mock_service = Mock()
        mock_service.delete_record_by_uuid.side_effect = Exception("Database error")
        mock_span_service_cls.return_value = mock_service

        fake_uuid = uuid4()
        response = client.delete(f"/projects/{test_project.uuid}/spans/{fake_uuid}")

        assert response.status_code == 200
        assert response.json() is False


class TestDeleteSpanInOpensearch:
    """Test delete_span_in_opensearch function."""

    @patch("lilypad.server.api.v0.spans_api.delete_span_in_opensearch")
    def test_delete_span_in_opensearch_enabled(self, mock_delete_func):
        """Test delete_span_in_opensearch when OpenSearch is enabled."""
        from lilypad.server.api.v0.spans_api import delete_span_in_opensearch

        # Create mock OpenSearch service
        mock_opensearch = Mock()
        mock_opensearch.is_enabled = True

        project_uuid = uuid4()
        span_uuid = uuid4()

        # Test the function directly since it's async
        import asyncio

        async def test_delete():
            await delete_span_in_opensearch(project_uuid, span_uuid, mock_opensearch)
            mock_opensearch.delete_trace_by_uuid.assert_called_once_with(
                project_uuid, span_uuid
            )

        asyncio.run(test_delete())

    def test_delete_span_in_opensearch_disabled(self):
        """Test delete_span_in_opensearch when OpenSearch is disabled."""
        from lilypad.server.api.v0.spans_api import delete_span_in_opensearch

        # Create mock OpenSearch service
        mock_opensearch = Mock()
        mock_opensearch.is_enabled = False

        project_uuid = uuid4()
        span_uuid = uuid4()

        # Test the function directly since it's async
        import asyncio

        async def test_delete():
            await delete_span_in_opensearch(project_uuid, span_uuid, mock_opensearch)
            # Should not call delete_trace_by_uuid when disabled
            mock_opensearch.delete_trace_by_uuid.assert_not_called()

        asyncio.run(test_delete())


class TestGetSpansByFunctionPaginated:
    """Test get_spans_by_function_uuid_paginated endpoint."""

    def test_get_spans_by_function_paginated_default_params(
        self,
        client: TestClient,
        test_project: ProjectTable,
        test_function: FunctionTable,
        test_spans_comprehensive: list[SpanTable],
    ):
        """Test getting paginated spans with default parameters."""
        response = client.get(
            f"/projects/{test_project.uuid}/functions/{test_function.uuid}/spans/paginated"
        )

        assert response.status_code == 200
        data = response.json()

        assert "items" in data
        assert "limit" in data
        assert "offset" in data
        assert "total" in data
        assert data["limit"] == 50  # default
        assert data["offset"] == 0  # default

    def test_get_spans_by_function_paginated_custom_params(
        self,
        client: TestClient,
        test_project: ProjectTable,
        test_function: FunctionTable,
        test_spans_comprehensive: list[SpanTable],
    ):
        """Test getting paginated spans with custom parameters."""
        response = client.get(
            f"/projects/{test_project.uuid}/functions/{test_function.uuid}/spans/paginated",
            params={"limit": 10, "offset": 5, "order": "asc"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["limit"] == 10
        assert data["offset"] == 5

    def test_get_spans_by_function_paginated_invalid_limit(
        self,
        client: TestClient,
        test_project: ProjectTable,
        test_function: FunctionTable,
    ):
        """Test getting paginated spans with invalid limit."""
        response = client.get(
            f"/projects/{test_project.uuid}/functions/{test_function.uuid}/spans/paginated",
            params={"limit": 0},  # Invalid limit
        )

        assert response.status_code == 422  # Validation error

    def test_get_spans_by_function_paginated_invalid_order(
        self,
        client: TestClient,
        test_project: ProjectTable,
        test_function: FunctionTable,
    ):
        """Test getting paginated spans with invalid order."""
        response = client.get(
            f"/projects/{test_project.uuid}/functions/{test_function.uuid}/spans/paginated",
            params={"order": "invalid"},  # Invalid order
        )

        assert response.status_code == 422  # Validation error

    def test_get_spans_by_function_paginated_desc_order(
        self,
        client: TestClient,
        test_project: ProjectTable,
        test_function: FunctionTable,
        test_spans_comprehensive: list[SpanTable],
    ):
        """Test getting paginated spans with descending order."""
        response = client.get(
            f"/projects/{test_project.uuid}/functions/{test_function.uuid}/spans/paginated",
            params={"order": "desc", "limit": 5},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 5


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_get_span_with_invalid_uuid(self, client: TestClient):
        """Test getting span with invalid UUID format."""
        response = client.get("/spans/invalid-uuid")

        assert response.status_code == 422  # Validation error

    def test_search_traces_with_empty_query(
        self, client: TestClient, test_project: ProjectTable
    ):
        """Test search traces with empty query."""
        response = client.get(
            f"/projects/{test_project.uuid}/spans", params={"query": ""}
        )

        assert response.status_code == 200

    def test_get_aggregates_with_invalid_timeframe(
        self, client: TestClient, test_project: ProjectTable
    ):
        """Test getting aggregates with invalid time frame."""
        response = client.get(
            f"/projects/{test_project.uuid}/spans/metadata",
            params={"time_frame": "invalid_timeframe"},
        )

        assert response.status_code == 422  # Validation error

    def test_update_span_with_invalid_data(
        self, client: TestClient, test_spans_comprehensive: list[SpanTable]
    ):
        """Test updating span with invalid data structure."""
        span = test_spans_comprehensive[0]

        response = client.patch(f"/spans/{span.uuid}", json={"invalid": "data"})

        # Should still return 200 as the service handles the update
        assert response.status_code == 200
