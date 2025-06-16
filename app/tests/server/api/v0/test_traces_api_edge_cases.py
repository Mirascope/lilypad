"""Edge case tests for traces API."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, Mock, patch
from uuid import uuid4

from fastapi.testclient import TestClient

from lilypad.server.models import ProjectTable, SpanTable

# Import fixtures
pytest_plugins = ["tests.server.api.v0.conftest"]


def test_convert_system_to_provider_azure():
    """Test _convert_system_to_provider for azure."""
    from lilypad.server.api.v0.traces_api import _convert_system_to_provider

    result = _convert_system_to_provider("az.ai.inference")
    assert result == "azure"


def test_convert_system_to_provider_google():
    """Test _convert_system_to_provider for google."""
    from lilypad.server.api.v0.traces_api import _convert_system_to_provider

    result = _convert_system_to_provider("google_genai")
    assert result == "google"


def test_traces_post_missing_attributes(client: TestClient, test_project: ProjectTable):
    """Test traces POST with trace missing attributes."""
    from lilypad.server._utils import validate_api_key_project_strict
    from lilypad.server.api.v0.main import api

    original_overrides = api.dependency_overrides.copy()

    try:
        api.dependency_overrides[validate_api_key_project_strict] = lambda: True

        with (
            patch(
                "lilypad.server.services.projects.ProjectService.find_record_no_organization",
                return_value=test_project,
            ),
            patch(
                "lilypad.server.services.spans.SpanService.count_by_current_month",
                return_value=0,
            ),
            patch(
                "lilypad.server.api.v0.traces_api.get_span_kafka_service"
            ) as mock_kafka,
        ):
            mock_kafka_service = Mock()
            mock_kafka_service.send_batch = AsyncMock(return_value=True)
            mock_kafka.return_value = mock_kafka_service

            # Send trace without attributes
            response = client.post(
                f"/projects/{test_project.uuid}/traces",
                json=[
                    {
                        "span_id": "test_span",
                        "trace_id": "test_trace",
                        "start_time": 1000,
                        "end_time": 2000,
                        "instrumentation_scope": {"name": "lilypad"},
                        # No attributes field
                    }
                ],
            )

            assert response.status_code == 200

    finally:
        api.dependency_overrides = original_overrides


def test_traces_with_parent_child_relationship(
    client: TestClient, test_project: ProjectTable
):
    """Test traces with parent-child relationship."""
    from lilypad.server._utils import validate_api_key_project_strict
    from lilypad.server.api.v0.main import api

    original_overrides = api.dependency_overrides.copy()

    try:
        api.dependency_overrides[validate_api_key_project_strict] = lambda: True

        with (
            patch(
                "lilypad.server.services.projects.ProjectService.find_record_no_organization",
                return_value=test_project,
            ),
            patch(
                "lilypad.server.services.spans.SpanService.count_by_current_month",
                return_value=0,
            ),
            patch(
                "lilypad.server.api.v0.traces_api.get_span_kafka_service"
            ) as mock_kafka,
        ):
            # Force synchronous processing
            mock_kafka_service = Mock()
            mock_kafka_service.send_batch = AsyncMock(return_value=False)
            mock_kafka.return_value = mock_kafka_service

            with patch(
                "lilypad.server.services.spans.SpanService.create_bulk_records"
            ) as mock_create:
                mock_create.return_value = []

                with patch(
                    "lilypad.server.services.billing.BillingService.report_span_usage_with_fallback"
                ):
                    # Send parent and child spans
                    response = client.post(
                        f"/projects/{test_project.uuid}/traces",
                        json=[
                            {
                                "span_id": "parent_span",
                                "trace_id": "test_trace",
                                "start_time": 1000,
                                "end_time": 3000,
                                "instrumentation_scope": {"name": "lilypad"},
                            },
                            {
                                "span_id": "child_span",
                                "trace_id": "test_trace",
                                "parent_span_id": "parent_span",
                                "start_time": 1500,
                                "end_time": 2500,
                                "instrumentation_scope": {"name": "lilypad"},
                            },
                        ],
                    )

                    assert response.status_code == 200

    finally:
        api.dependency_overrides = original_overrides


def test_billing_service_exception_handling(
    client: TestClient, test_project: ProjectTable
):
    """Test billing service exception handling."""
    from lilypad.server._utils import validate_api_key_project_strict
    from lilypad.server.api.v0.main import api

    original_overrides = api.dependency_overrides.copy()

    try:
        api.dependency_overrides[validate_api_key_project_strict] = lambda: True

        with (
            patch(
                "lilypad.server.services.projects.ProjectService.find_record_no_organization",
                return_value=test_project,
            ),
            patch(
                "lilypad.server.services.spans.SpanService.count_by_current_month",
                return_value=0,
            ),
            patch(
                "lilypad.server.api.v0.traces_api.get_span_kafka_service"
            ) as mock_kafka,
        ):
            # Force synchronous processing
            mock_kafka_service = Mock()
            mock_kafka_service.send_batch = AsyncMock(return_value=False)
            mock_kafka.return_value = mock_kafka_service

            with patch(
                "lilypad.server.services.spans.SpanService.create_bulk_records"
            ) as mock_create:
                mock_create.return_value = []

                with patch(
                    "lilypad.server.services.billing.BillingService.report_span_usage_with_fallback"
                ) as mock_billing:
                    # Make billing service raise an exception
                    mock_billing.side_effect = Exception("Billing error")

                    # This should not fail the request
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

                    assert response.status_code == 200

    finally:
        api.dependency_overrides = original_overrides


def test_traces_opensearch_indexing(client: TestClient, test_project: ProjectTable):
    """Test OpenSearch indexing in traces endpoint."""
    from lilypad.server.api.v0.traces_api import traces

    # Create mock objects
    mock_span = MagicMock(spec=SpanTable)
    mock_span.model_dump.return_value = {"span_id": "test", "data": "test"}

    # Call the traces function directly with all mocks
    match_api_key = True
    license = Mock(tier="free")
    is_lilypad_cloud = False
    project_uuid = test_project.uuid

    class MockRequest:
        async def json(self):
            return [
                {
                    "span_id": "test_span",
                    "trace_id": "test_trace",
                    "start_time": 1000,
                    "end_time": 2000,
                    "instrumentation_scope": {"name": "lilypad"},
                }
            ]

    request = MockRequest()

    mock_span_service = Mock()
    mock_span_service.count_by_current_month.return_value = 0
    mock_span_service.create_bulk_records.return_value = [mock_span]

    mock_opensearch_service = Mock()
    mock_opensearch_service.is_enabled = True

    mock_background_tasks = Mock()

    mock_project_service = Mock()
    mock_project_service.find_record_no_organization.return_value = test_project

    mock_billing_service = Mock()
    mock_billing_service.report_span_usage_with_fallback = AsyncMock()

    mock_user = Mock(uuid=uuid4())

    mock_kafka_service = Mock()
    mock_kafka_service.send_batch = AsyncMock(return_value=False)  # Force sync

    # Run the function
    asyncio.run(
        traces(
            match_api_key=match_api_key,
            license=license,
            is_lilypad_cloud=is_lilypad_cloud,
            project_uuid=project_uuid,  # type: ignore
            request=request,  # type: ignore
            span_service=mock_span_service,
            opensearch_service=mock_opensearch_service,
            background_tasks=mock_background_tasks,
            project_service=mock_project_service,
            billing_service=mock_billing_service,
            user=mock_user,
            kafka_service=mock_kafka_service,
            stripe_kafka_service=None,
        )
    )

    # Verify model_dump was called
    mock_span.model_dump.assert_called_once()

    # Verify background task was added
    mock_background_tasks.add_task.assert_called_once()


def test_get_trace_by_span_uuid_returns_span(
    client: TestClient, test_project: ProjectTable
):
    """Test get_trace_by_span_uuid when span is found."""
    from lilypad.server.models.spans import SpanTable

    with patch(
        "lilypad.server.services.spans.SpanService.find_root_parent_span"
    ) as mock_find:
        # Create a proper SpanTable object
        span = SpanTable(
            uuid=uuid4(),
            span_id="test_span",
            trace_id="test_trace",  # type: ignore
            project_uuid=test_project.uuid,
            organization_uuid=test_project.organization_uuid,
            start_time=1000,  # type: ignore
            end_time=2000,  # type: ignore
            parent_span_id=None,
            type="function",
            function_uuid=None,
            cost=0.0,
            input_tokens=100,
            output_tokens=50,
            duration_ms=1000,
            data={},
            scope="lilypad",
        )
        mock_find.return_value = span

        response = client.get(f"/projects/{test_project.uuid}/traces/test_span/root")

        assert response.status_code == 200
        data = response.json()
        assert data["span_id"] == "test_span"


def test_get_spans_by_trace_id_returns_spans(
    client: TestClient, test_project: ProjectTable
):
    """Test get_spans_by_trace_id when spans are found."""
    from lilypad.server.models.spans import SpanTable

    with patch(
        "lilypad.server.services.spans.SpanService.find_spans_by_trace_id"
    ) as mock_find:
        # Create proper SpanTable objects
        span1 = SpanTable(
            uuid=uuid4(),
            span_id="span1",
            trace_id="test_trace",  # type: ignore
            project_uuid=test_project.uuid,
            organization_uuid=test_project.organization_uuid,
            start_time=1000,  # type: ignore
            end_time=2000,  # type: ignore
            parent_span_id=None,
            type="function",
            function_uuid=None,
            cost=0.0,
            input_tokens=100,
            output_tokens=50,
            duration_ms=1000,
            data={},
            scope="lilypad",
        )

        mock_find.return_value = [span1]

        response = client.get(
            f"/projects/{test_project.uuid}/traces/by-trace-id/test_trace"
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["span_id"] == "span1"
