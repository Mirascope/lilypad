"""Simple tests for spans API to improve coverage without complex validations."""

from datetime import datetime, timezone
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
def test_span_simple(
    session: Session,
    test_project: ProjectTable,
    test_function: FunctionTable,
) -> SpanTable:
    """Create a simple test span with minimal data for coverage."""
    span = SpanTable(
        organization_uuid=test_project.organization_uuid,
        project_uuid=test_project.uuid,
        span_id="simple_test_span",
        trace_id="simple_test_trace",
        parent_span_id=None,
        type="function",
        function_uuid=test_function.uuid,
        scope=Scope.LILYPAD,
        cost=0.001,
        input_tokens=100.0,
        output_tokens=50.0,
        duration_ms=1000.0,
        created_at=datetime.now(timezone.utc),
        data={
            "name": "simple_test_span",
            "attributes": {
                "lilypad.type": "function",
                "lilypad.function.uuid": str(test_function.uuid),
            },
            "request": {
                "provider": "test_provider",
                "model": "test_model",
                "messages": [{"role": "user", "content": "test"}],
            },
            "response": {
                "provider": "test_provider",
                "model": "test_model",
                "messages": [{"role": "assistant", "content": "response"}],
            },
        },
    )
    session.add(span)
    session.commit()
    session.refresh(span)
    return span


class TestSpansAPISimple:
    """Simple tests to cover missing code paths."""

    @patch("lilypad.server.api.v0.spans_api.SpanService")
    def test_get_span_success_mock(self, mock_service_cls, client: TestClient):
        """Test get_span endpoint with mocked service."""
        # Mock service to return a span
        mock_service = Mock()
        mock_span = Mock()
        mock_span.uuid = uuid4()
        mock_span.span_id = "test_span"
        mock_span.project_uuid = uuid4()
        mock_service.find_record_by_uuid.return_value = mock_span
        mock_service_cls.return_value = mock_service

        # Mock SpanMoreDetails.from_span
        with patch("lilypad.server.api.v0.spans_api.SpanMoreDetails") as mock_details:
            mock_details.from_span.return_value = {"test": "data"}

            response = client.get(f"/spans/{mock_span.uuid}")
            assert response.status_code == 200

    @patch("lilypad.server.api.v0.spans_api.SpanService")
    def test_get_span_not_found_mock(self, mock_service_cls, client: TestClient):
        """Test get_span endpoint when span not found."""
        mock_service = Mock()
        mock_service.find_record_by_uuid.return_value = None
        mock_service_cls.return_value = mock_service

        fake_uuid = uuid4()
        response = client.get(f"/spans/{fake_uuid}")
        assert response.status_code == 404

    @patch("lilypad.server.api.v0.spans_api.SpanService")
    def test_get_span_by_span_id_success_mock(
        self, mock_service_cls, client: TestClient
    ):
        """Test get_span_by_span_id endpoint with mocked service."""
        mock_service = Mock()
        mock_span = Mock()
        mock_span.uuid = uuid4()
        mock_span.span_id = "test_span"
        mock_span.project_uuid = uuid4()
        mock_service.get_record_by_span_id.return_value = mock_span
        mock_service_cls.return_value = mock_service

        with patch("lilypad.server.api.v0.spans_api.SpanMoreDetails") as mock_details:
            mock_details.from_span.return_value = {"test": "data"}

            response = client.get(
                f"/projects/{mock_span.project_uuid}/spans/{mock_span.span_id}"
            )
            assert response.status_code == 200

    @patch("lilypad.server.api.v0.spans_api.SpanService")
    def test_get_span_by_span_id_not_found_mock(
        self, mock_service_cls, client: TestClient
    ):
        """Test get_span_by_span_id endpoint when span not found."""
        mock_service = Mock()
        mock_service.get_record_by_span_id.return_value = None
        mock_service_cls.return_value = mock_service

        project_uuid = uuid4()
        response = client.get(f"/projects/{project_uuid}/spans/nonexistent_span")
        assert response.status_code == 404

    @patch("lilypad.server.api.v0.spans_api.SpanService")
    def test_update_span_mock(self, mock_service_cls, client: TestClient):
        """Test update_span endpoint with mocked service."""
        mock_service = Mock()
        mock_span = Mock()
        mock_span.uuid = uuid4()
        mock_service.update_span.return_value = mock_span
        mock_service_cls.return_value = mock_service

        update_data = {"data": {"test": "update"}}
        response = client.patch(f"/spans/{mock_span.uuid}", json=update_data)
        assert response.status_code == 200

    @patch("lilypad.server.api.v0.spans_api.SpanService")
    def test_get_aggregates_by_project_uuid_mock(
        self, mock_service_cls, client: TestClient
    ):
        """Test get_aggregates_by_project_uuid endpoint."""
        mock_service = Mock()
        mock_service.get_aggregated_metrics.return_value = []
        mock_service_cls.return_value = mock_service

        project_uuid = uuid4()
        response = client.get(
            f"/projects/{project_uuid}/spans/metadata",
            params={"time_frame": TimeFrame.LAST_7_DAYS.value},
        )
        assert response.status_code == 200

    @patch("lilypad.server.api.v0.spans_api.SpanService")
    def test_get_aggregates_by_function_uuid_mock(
        self, mock_service_cls, client: TestClient
    ):
        """Test get_aggregates_by_function_uuid endpoint."""
        mock_service = Mock()
        mock_service.get_aggregated_metrics.return_value = []
        mock_service_cls.return_value = mock_service

        project_uuid = uuid4()
        function_uuid = uuid4()
        response = client.get(
            f"/projects/{project_uuid}/functions/{function_uuid}/spans/metadata",
            params={"time_frame": TimeFrame.LAST_7_DAYS.value},
        )
        assert response.status_code == 200

    @patch("lilypad.server.api.v0.spans_api.get_opensearch_service")
    @patch("lilypad.server.api.v0.spans_api.FunctionService")
    def test_search_traces_complex_mock(
        self, mock_function_service_cls, mock_get_opensearch, client: TestClient
    ):
        """Test search_traces with complex parent-child relationships."""
        # Mock OpenSearch service
        mock_opensearch = Mock()
        mock_opensearch.is_enabled = True

        project_uuid = uuid4()
        function_uuid = uuid4()

        # Mock search results with parent-child relationship
        mock_hits = [
            {
                "_id": str(uuid4()),
                "_score": 1.0,
                "_source": {
                    "span_id": "parent_span",
                    "parent_span_id": None,
                    "organization_uuid": str(uuid4()),
                    "function_uuid": str(function_uuid),
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
                "_id": str(uuid4()),
                "_score": 0.8,
                "_source": {
                    "span_id": "child_span",
                    "parent_span_id": "parent_span",
                    "organization_uuid": str(uuid4()),
                    "function_uuid": str(function_uuid),
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

        # Mock function service
        mock_function_service = Mock()
        mock_function = Mock()
        mock_function.uuid = function_uuid
        mock_function_service.find_records_by_uuids.return_value = [mock_function]
        mock_function_service_cls.return_value = mock_function_service

        response = client.get(
            f"/projects/{project_uuid}/spans", params={"query": "test"}
        )

        assert response.status_code == 200
        data = response.json()
        # Should return only root spans with children attached
        assert len(data) == 1
        assert data[0]["span_id"] == "parent_span"
        assert len(data[0]["child_spans"]) == 1

    @patch("lilypad.server.api.v0.spans_api.get_opensearch_service")
    @patch("lilypad.server.api.v0.spans_api.FunctionService")
    def test_search_traces_no_function_uuid_mock(
        self, mock_function_service_cls, mock_get_opensearch, client: TestClient
    ):
        """Test search_traces with spans that have no function UUID."""
        mock_opensearch = Mock()
        mock_opensearch.is_enabled = True

        project_uuid = uuid4()

        mock_hit = {
            "_id": str(uuid4()),
            "_score": 1.0,
            "_source": {
                "span_id": "no_function_span",
                "parent_span_id": None,
                "organization_uuid": str(uuid4()),
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

        # Mock function service
        mock_function_service = Mock()
        mock_function_service.find_records_by_uuids.return_value = []
        mock_function_service_cls.return_value = mock_function_service

        response = client.get(
            f"/projects/{project_uuid}/spans", params={"query": "test"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["span_id"] == "no_function_span"
        assert data[0]["function_uuid"] is None

    def test_delete_span_in_opensearch_enabled(self):
        """Test delete_span_in_opensearch when enabled."""
        import asyncio

        from lilypad.server.api.v0.spans_api import delete_span_in_opensearch

        mock_opensearch = Mock()
        mock_opensearch.is_enabled = True

        project_uuid = uuid4()
        span_uuid = uuid4()

        async def test_delete():
            await delete_span_in_opensearch(project_uuid, span_uuid, mock_opensearch)
            mock_opensearch.delete_trace_by_uuid.assert_called_once_with(
                project_uuid, span_uuid
            )

        asyncio.run(test_delete())

    def test_delete_span_in_opensearch_disabled(self):
        """Test delete_span_in_opensearch when disabled."""
        import asyncio

        from lilypad.server.api.v0.spans_api import delete_span_in_opensearch

        mock_opensearch = Mock()
        mock_opensearch.is_enabled = False

        project_uuid = uuid4()
        span_uuid = uuid4()

        async def test_delete():
            await delete_span_in_opensearch(project_uuid, span_uuid, mock_opensearch)
            # Should not call delete when disabled
            mock_opensearch.delete_trace_by_uuid.assert_not_called()

        asyncio.run(test_delete())

    @patch("lilypad.server.api.v0.spans_api.get_opensearch_service")
    def test_delete_spans_with_opensearch_background_task(
        self, mock_get_opensearch, client: TestClient, test_span_simple: SpanTable
    ):
        """Test delete_spans with OpenSearch background task."""
        mock_opensearch = Mock()
        mock_opensearch.is_enabled = True
        mock_get_opensearch.return_value = mock_opensearch

        response = client.delete(
            f"/projects/{test_span_simple.project_uuid}/spans/{test_span_simple.uuid}"
        )
        assert response.status_code == 200
        assert response.json() is True

    @patch("lilypad.server.api.v0.spans_api.SpanService")
    def test_get_spans_by_function_paginated_mock(
        self, mock_service_cls, client: TestClient
    ):
        """Test get_spans_by_function_uuid_paginated endpoint."""
        mock_service = Mock()
        mock_service.find_records_by_function_uuid_paged.return_value = []
        mock_service.count_records_by_function_uuid.return_value = 0
        mock_service_cls.return_value = mock_service

        project_uuid = uuid4()
        function_uuid = uuid4()

        response = client.get(
            f"/projects/{project_uuid}/functions/{function_uuid}/spans/paginated",
            params={"limit": 10, "offset": 5, "order": "desc"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["limit"] == 10
        assert data["offset"] == 5
        assert data["total"] == 0
        assert data["items"] == []
