"""Tests for OpenSearch functionality to remove pragma: no cover comments."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from lilypad.server._utils.opensearch import index_traces_in_opensearch
from lilypad.server.api.v0.spans_api import delete_span_in_opensearch
from lilypad.server.models import ProjectTable


class TestOpenSearchIndexing:
    """Test OpenSearch indexing functionality without pragma."""

    @pytest.mark.asyncio
    async def test_index_traces_success(self):
        """Test successful trace indexing."""
        project_uuid = uuid4()
        traces = [{"span_id": "test", "data": "test_data"}]

        mock_service = Mock()
        mock_service.bulk_index_traces.return_value = True

        # Should complete without error
        await index_traces_in_opensearch(project_uuid, traces, mock_service)

        # Verify service was called
        mock_service.bulk_index_traces.assert_called_once_with(project_uuid, traces)

    @pytest.mark.asyncio
    async def test_index_traces_failure(self):
        """Test trace indexing failure logging."""
        project_uuid = uuid4()
        traces = [{"span_id": "test", "data": "test_data"}]

        mock_service = Mock()
        mock_service.bulk_index_traces.return_value = False

        with patch("lilypad.server._utils.opensearch.logger") as mock_logger:
            await index_traces_in_opensearch(project_uuid, traces, mock_service)

            # Verify error was logged
            mock_logger.error.assert_called_once()
            assert "Failed to index" in str(mock_logger.error.call_args)

    @pytest.mark.asyncio
    async def test_index_traces_exception(self):
        """Test trace indexing exception handling."""
        project_uuid = uuid4()
        traces = [{"span_id": "test", "data": "test_data"}]

        mock_service = Mock()
        mock_service.bulk_index_traces.side_effect = Exception("OpenSearch error")

        with patch("lilypad.server._utils.opensearch.logger") as mock_logger:
            await index_traces_in_opensearch(project_uuid, traces, mock_service)

            # Verify exception was logged
            mock_logger.error.assert_called_once()
            assert "Exception during trace indexing" in str(mock_logger.error.call_args)


class TestOpenSearchDeletion:
    """Test OpenSearch deletion functionality without pragma."""

    @pytest.mark.asyncio
    async def test_delete_span_when_enabled(self):
        """Test span deletion when OpenSearch is enabled."""
        project_uuid = uuid4()
        span_uuid = uuid4()

        mock_service = Mock()
        mock_service.is_enabled = True

        await delete_span_in_opensearch(project_uuid, span_uuid, mock_service)

        # Verify deletion was called
        mock_service.delete_trace_by_uuid.assert_called_once_with(
            project_uuid, span_uuid
        )

    @pytest.mark.asyncio
    async def test_delete_span_when_disabled(self):
        """Test span deletion when OpenSearch is disabled."""
        project_uuid = uuid4()
        span_uuid = uuid4()

        mock_service = Mock()
        mock_service.is_enabled = False

        await delete_span_in_opensearch(project_uuid, span_uuid, mock_service)

        # Verify deletion was NOT called
        mock_service.delete_trace_by_uuid.assert_not_called()


class TestBackgroundTaskIntegration:
    """Test background task integration with OpenSearch."""

    def test_spans_api_delete_with_opensearch_enabled(
        self, client: TestClient, test_project: ProjectTable
    ):
        """Test spans delete API with OpenSearch enabled."""
        fake_uuid = uuid4()

        with (
            patch(
                "lilypad.server.api.v0.spans_api.get_opensearch_service"
            ) as mock_get_service,
            patch(
                "lilypad.server.services.spans.SpanService.delete_record_by_uuid"
            ) as mock_delete,
        ):
            mock_service = Mock()
            mock_service.is_enabled = True
            mock_get_service.return_value = mock_service
            mock_delete.return_value = True

            response = client.delete(f"/projects/{test_project.uuid}/spans/{fake_uuid}")

            assert response.status_code == 200
            assert response.json() is True

    def test_spans_api_delete_with_opensearch_disabled(
        self, client: TestClient, test_project: ProjectTable
    ):
        """Test spans delete API with OpenSearch disabled."""
        fake_uuid = uuid4()

        with (
            patch(
                "lilypad.server.api.v0.spans_api.get_opensearch_service"
            ) as mock_get_service,
            patch(
                "lilypad.server.services.spans.SpanService.delete_record_by_uuid"
            ) as mock_delete,
        ):
            mock_service = Mock()
            mock_service.is_enabled = False
            mock_get_service.return_value = mock_service
            mock_delete.return_value = True

            response = client.delete(f"/projects/{test_project.uuid}/spans/{fake_uuid}")

            assert response.status_code == 200
            assert response.json() is True

    def test_spans_api_delete_exception_handling(
        self, client: TestClient, test_project: ProjectTable
    ):
        """Test spans delete API exception handling."""
        fake_uuid = uuid4()

        with patch(
            "lilypad.server.services.spans.SpanService.delete_record_by_uuid"
        ) as mock_delete:
            mock_delete.side_effect = Exception("Database error")

            response = client.delete(f"/projects/{test_project.uuid}/spans/{fake_uuid}")

            assert response.status_code == 200
            assert response.json() is False  # Returns False on exception
