"""Edge case tests for spans API."""

from unittest.mock import Mock, create_autospec, patch
from uuid import uuid4

import pytest
from fastapi import BackgroundTasks
from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.server.api.v0.spans_api import delete_spans
from lilypad.server.models import ProjectTable
from lilypad.server.schemas.users import UserPublic
from lilypad.server.services.opensearch import OpenSearchService
from lilypad.server.services.spans import SpanService

# Import fixtures
pytest_plugins = ["tests.server.api.v0.conftest"]


@pytest.mark.asyncio
async def test_delete_spans_with_opensearch_background_task():
    """Direct test for delete_spans function to cover OpenSearch integration."""
    project_uuid = uuid4()
    span_uuid = uuid4()

    # Create mocks
    mock_span_service = Mock(spec=SpanService)
    # Make delete succeed
    mock_span_service.delete_record_by_uuid.return_value = True

    mock_opensearch = create_autospec(OpenSearchService, instance=True)
    mock_opensearch.is_enabled = True

    mock_bg_tasks = create_autospec(BackgroundTasks, instance=True)

    # Call the function directly
    result = await delete_spans(
        project_uuid=project_uuid,
        span_uuid=span_uuid,
        span_service=mock_span_service,
        opensearch_service=mock_opensearch,
        background_tasks=mock_bg_tasks,
    )

    # Should return True and add background task
    assert result is True

    # Verify delete was called
    mock_span_service.delete_record_by_uuid.assert_called_once_with(span_uuid)

    # Verify background task was added
    mock_bg_tasks.add_task.assert_called_once()
    call_args = mock_bg_tasks.add_task.call_args
    assert call_args is not None


@pytest.mark.asyncio
async def test_delete_spans_exception_handling():
    """Test delete_spans exception handling."""
    project_uuid = uuid4()
    span_uuid = uuid4()

    # Create mocks
    mock_span_service = Mock(spec=SpanService)
    # Make delete raise an exception
    mock_span_service.delete_record_by_uuid.side_effect = Exception("Database error")

    mock_opensearch = create_autospec(OpenSearchService, instance=True)
    mock_opensearch.is_enabled = True

    mock_bg_tasks = create_autospec(BackgroundTasks, instance=True)

    # Call the function directly
    result = await delete_spans(
        project_uuid=project_uuid,
        span_uuid=span_uuid,
        span_service=mock_span_service,
        opensearch_service=mock_opensearch,
        background_tasks=mock_bg_tasks,
    )

    # Should return False on exception
    assert result is False

    # Background task should not be called on exception
    mock_bg_tasks.add_task.assert_not_called()


def test_delete_span_with_opensearch_enabled(
    client: TestClient, test_project: ProjectTable
):
    """Test delete_span with OpenSearch enabled."""
    span_uuid = uuid4()

    with patch(
        "lilypad.server.api.v0.spans_api.get_opensearch_service"
    ) as mock_get_service:
        # Mock OpenSearch service to be enabled
        mock_service = Mock()
        mock_service.is_enabled = True
        mock_get_service.return_value = mock_service

        # Delete the span
        response = client.delete(f"/projects/{test_project.uuid}/spans/{span_uuid}")

        # Should succeed even if span doesn't exist
        assert response.status_code == 200
        assert response.json() is False  # Returns False when span doesn't exist


@pytest.fixture
def mock_user():
    """Create a mock user."""
    return UserPublic(
        uuid=uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
    )


def test_spans_service_find_root_span_edge_case(mock_user):
    """Test find_root_span_for_span edge case."""
    from lilypad.server.services.spans import SpanService

    mock_session = Mock(spec=Session)
    service = SpanService(session=mock_session, user=mock_user)

    # Mock the first query to return a result with uuid
    mock_result = Mock()
    mock_result.uuid = uuid4()

    # Mock the second query to return None - this tests edge case
    mock_session.exec.side_effect = [
        Mock(first=Mock(return_value=mock_result)),  # First query succeeds
        Mock(first=Mock(return_value=None)),  # Second query fails
    ]

    # Call the actual method
    result = service.find_root_parent_span("test-span-id")
    assert result is None
