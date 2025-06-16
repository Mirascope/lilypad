"""Tests for API error cases to remove pragma: no cover comments."""

from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from lilypad.server.models import ProjectTable


class TestAPI404ErrorCases:
    """Test all 404 error cases that currently have pragma: no cover."""

    def test_spans_api_get_span_by_uuid_not_found_mock(self, client: TestClient):
        """Test spans API get_span returns 404 when span not found - using mock."""
        fake_uuid = uuid4()

        with patch(
            "lilypad.server.services.spans.SpanService.find_record_by_uuid",
            return_value=None,
        ):
            response = client.get(f"/spans/{fake_uuid}")

            assert response.status_code == 404
            assert "Span not found" in response.json()["detail"]

    def test_spans_api_get_span_by_span_id_not_found_mock(
        self, client: TestClient, test_project: ProjectTable
    ):
        """Test spans API get_span_by_span_id returns 404 when span not found - using mock."""
        with patch(
            "lilypad.server.services.spans.SpanService.get_record_by_span_id",
            return_value=None,
        ):
            response = client.get(
                f"/projects/{test_project.uuid}/spans/non_existent_span"
            )

            assert response.status_code == 404
            assert "Span not found" in response.json()["detail"]

    def test_traces_api_get_trace_by_span_uuid_not_found(
        self, client: TestClient, test_project: ProjectTable
    ):
        """Test traces API get_trace_by_span_uuid returns 404 when span not found."""
        with patch(
            "lilypad.server.services.spans.SpanService.find_root_parent_span",
            return_value=None,
        ):
            response = client.get(
                f"/projects/{test_project.uuid}/traces/non_existent_span/root"
            )

            assert response.status_code == 404
            assert "Span not found" in response.json()["detail"]

    def test_traces_api_get_spans_by_trace_id_not_found(
        self, client: TestClient, test_project: ProjectTable
    ):
        """Test traces API get_spans_by_trace_id returns 404 when no spans found."""
        with patch(
            "lilypad.server.services.spans.SpanService.find_spans_by_trace_id",
            return_value=[],
        ):
            response = client.get(
                f"/projects/{test_project.uuid}/traces/by-trace-id/non_existent_trace"
            )

            assert response.status_code == 404
            assert (
                "No spans found for trace_id: non_existent_trace"
                in response.json()["detail"]
            )


class TestOpenSearchIntegration:
    """Test OpenSearch integration error cases."""

    def test_opensearch_indexing_in_background_task(
        self, client: TestClient, test_project: ProjectTable
    ):
        """Test OpenSearch indexing runs in background without blocking response."""
        # Override the authentication dependency in the app
        from lilypad.server._utils import validate_api_key_project_strict
        from lilypad.server.api.v0.main import api

        # Save original overrides
        original_overrides = api.dependency_overrides.copy()

        try:
            # Add our override
            api.dependency_overrides[validate_api_key_project_strict] = lambda: True

            # Mock the project service to return the test project
            from lilypad.server.services.projects import ProjectService

            with (
                patch.object(
                    ProjectService,
                    "find_record_no_organization",
                    return_value=test_project,
                ),
                # Mock the background task to simulate OpenSearch being enabled
                patch("lilypad.server.api.v0.traces_api.index_traces_in_opensearch"),
                patch(
                    "lilypad.server.api.v0.traces_api.get_opensearch_service"
                ) as mock_get_service,
            ):
                mock_service = Mock()
                mock_service.is_enabled = True
                mock_get_service.return_value = mock_service

                # Mock the service to return valid data
                with patch(
                    "lilypad.server.services.spans.SpanService.create_bulk_records"
                ) as mock_create:
                    mock_create.return_value = []

                    # Mock span count for license check
                    with patch(
                        "lilypad.server.services.spans.SpanService.count_by_current_month",
                        return_value=0,
                    ):
                        response = client.post(
                            f"/projects/{test_project.uuid}/traces",
                            json=[
                                {
                                    "span_id": "test_span",
                                    "trace_id": "test_trace",
                                    "start_time": 1000,
                                    "end_time": 2000,
                                    "instrumentation_scope": {"name": "lilypad"},
                                }
                            ],
                        )

                        # Should succeed regardless of OpenSearch state
                        assert response.status_code == 200
        finally:
            # Restore original overrides
            api.dependency_overrides = original_overrides

    def test_opensearch_delete_runs_in_background(
        self, client: TestClient, test_project: ProjectTable
    ):
        """Test OpenSearch delete runs in background without blocking response."""
        fake_uuid = uuid4()

        with patch(
            "lilypad.server.api.v0.spans_api.get_opensearch_service"
        ) as mock_get_service:
            mock_service = Mock()
            mock_service.is_enabled = True
            mock_get_service.return_value = mock_service

            # Should still succeed even if the span doesn't exist
            response = client.delete(f"/projects/{test_project.uuid}/spans/{fake_uuid}")

            # Returns False when span doesn't exist, but still 200 OK
            assert response.status_code == 200
            assert response.json() is False
