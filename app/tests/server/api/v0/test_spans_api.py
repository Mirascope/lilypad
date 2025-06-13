"""Tests for the spans API."""

import time
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


@pytest.fixture
def test_spans(
    session: Session,
    test_project: ProjectTable,
    test_function: FunctionTable,
    test_user,
) -> list[SpanTable]:
    """Create test spans with various timestamps."""
    now = datetime.now(timezone.utc)
    spans = []

    # Create spans with different timestamps
    for i in range(5):
        # Root span
        root_span = SpanTable(
            organization_uuid=test_project.organization_uuid,
            project_uuid=test_project.uuid,
            span_id=f"span_root_{i}",
            trace_id=f"trace_{i}",  # pyright: ignore [reportCallIssue]
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
                "name": f"test_function_{i}",
                "attributes": {
                    "lilypad.type": "function",
                    "lilypad.function.uuid": str(test_function.uuid),
                },
                "events": [],
            },
        )
        session.add(root_span)
        spans.append(root_span)

        # Child span
        child_span = SpanTable(
            organization_uuid=test_project.organization_uuid,
            project_uuid=test_project.uuid,
            span_id=f"span_child_{i}",
            trace_id=f"trace_{i}",  # pyright: ignore [reportCallIssue]
            parent_span_id=f"span_root_{i}",
            type="function",
            function_uuid=test_function.uuid,
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
        session.add(child_span)
        spans.append(child_span)

    session.commit()
    for span in spans:
        session.refresh(span)

    return spans


def test_get_recent_spans_no_since_parameter(
    client: TestClient,
    test_project: ProjectTable,
    test_spans: list[SpanTable],
):
    """Test getting recent spans without 'since' parameter (default 30 seconds)."""
    # Note: The client fixture already overrides get_current_user
    # so we don't need to pass authentication headers in tests
    response = client.get(
        f"/projects/{test_project.uuid}/spans/recent",
    )

    assert response.status_code == 200
    data = response.json()

    assert "spans" in data
    assert "timestamp" in data
    assert "project_uuid" in data
    assert data["project_uuid"] == str(test_project.uuid)

    # Should return only root spans from last 30 seconds (span 0 in our case)
    assert len(data["spans"]) == 1
    assert data["spans"][0]["span_id"] == "span_root_0"

    # Check timestamp is recent
    timestamp = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    assert (datetime.now(timezone.utc) - timestamp).total_seconds() < 5


def test_get_recent_spans_with_since_parameter(
    client: TestClient,
    test_project: ProjectTable,
    test_spans: list[SpanTable],
):
    """Test getting recent spans with specific 'since' timestamp."""
    # Get spans from last 3 minutes
    since = datetime.now(timezone.utc) - timedelta(minutes=3)

    response = client.get(
        f"/projects/{test_project.uuid}/spans/recent",
        params={"since": since.isoformat()},
    )

    assert response.status_code == 200
    data = response.json()

    # Should return root spans from last 3 minutes (spans 0, 1, 2)
    assert len(data["spans"]) == 3
    span_ids = [span["span_id"] for span in data["spans"]]
    assert "span_root_0" in span_ids
    assert "span_root_1" in span_ids
    assert "span_root_2" in span_ids

    # Verify child spans are included
    for span in data["spans"]:
        if span["span_id"] == "span_root_0":
            assert len(span["child_spans"]) == 1
            assert span["child_spans"][0]["span_id"] == "span_child_0"


def test_get_span_by_uuid(
    client: TestClient,
    test_spans: list[SpanTable],
):
    """Test getting span by UUID."""
    span = test_spans[0]
    response = client.get(f"/spans/{span.uuid}")

    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == str(span.uuid)
    assert data["span_id"] == span.span_id


def test_get_span_by_uuid_not_found(
    client: TestClient,
):
    """Test getting span by UUID when span doesn't exist."""
    fake_uuid = uuid4()
    response = client.get(f"/spans/{fake_uuid}")

    assert response.status_code == 404
    assert "Span not found" in response.json()["detail"]


def test_get_span_by_span_id(
    client: TestClient,
    test_project: ProjectTable,
    test_spans: list[SpanTable],
):
    """Test getting span by project UUID and span ID."""
    span = test_spans[0]
    response = client.get(f"/projects/{test_project.uuid}/spans/{span.span_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["span_id"] == span.span_id


def test_get_span_by_span_id_not_found(
    client: TestClient,
    test_project: ProjectTable,
):
    """Test getting span by span ID when span doesn't exist."""
    response = client.get(f"/projects/{test_project.uuid}/spans/non_existent_span")

    assert response.status_code == 404
    assert "Span not found" in response.json()["detail"]


def test_get_aggregates_by_project_uuid(
    client: TestClient,
    test_project: ProjectTable,
    test_spans: list[SpanTable],
):
    """Test getting aggregated metrics by project UUID."""
    response = client.get(
        f"/projects/{test_project.uuid}/spans/metadata", params={"time_frame": "day"}
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_aggregates_by_function_uuid(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
    test_spans: list[SpanTable],
):
    """Test getting aggregated metrics by function UUID."""
    response = client.get(
        f"/projects/{test_project.uuid}/functions/{test_function.uuid}/spans/metadata",
        params={"time_frame": "day"},
    )

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_update_span(
    client: TestClient,
    test_spans: list[SpanTable],
):
    """Test updating span."""
    span = test_spans[0]
    update_data = {"tags": {"environment": "test", "version": "1.0"}}

    response = client.patch(f"/spans/{span.uuid}", json=update_data)

    assert response.status_code == 200
    data = response.json()
    assert data["uuid"] == str(span.uuid)


def test_search_traces_opensearch_disabled(
    client: TestClient,
    test_project: ProjectTable,
):
    """Test search traces when OpenSearch is disabled."""
    with patch(
        "lilypad.server.api.v0.spans_api.get_opensearch_service"
    ) as mock_get_service:
        mock_service = Mock()
        mock_service.is_enabled = False
        mock_get_service.return_value = mock_service

        response = client.get(
            f"/projects/{test_project.uuid}/spans", params={"query_string": "test"}
        )

        assert response.status_code == 200
        assert response.json() == []


def test_search_traces_opensearch_enabled(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
):
    """Test search traces when OpenSearch is enabled."""
    mock_hits = [
        {
            "_id": str(uuid4()),
            "_score": 1.0,
            "_source": {
                "organization_uuid": str(test_project.organization_uuid),
                "span_id": "test_span_1",
                "parent_span_id": None,
                "type": "function",
                "function_uuid": str(test_function.uuid),
                "scope": "lilypad",
                "cost": 0.001,
                "input_tokens": 100,
                "output_tokens": 50,
                "duration_ms": 1000,
                "created_at": "2024-01-01T00:00:00Z",
                "data": {"attributes": {"test": "value"}},
            },
        }
    ]

    # Create mock OpenSearch service
    mock_opensearch_service = Mock()
    mock_opensearch_service.is_enabled = True
    mock_opensearch_service.search_traces.return_value = mock_hits
    
    # Create mock FunctionService
    mock_function_service = Mock()
    mock_function_service.find_records_by_uuids.return_value = [test_function]
    
    # Override dependencies
    from lilypad.server.api.v0.main import api
    from lilypad.server.services.opensearch import get_opensearch_service
    from lilypad.server.services.functions import FunctionService
    
    api.dependency_overrides[get_opensearch_service] = lambda: mock_opensearch_service
    api.dependency_overrides[FunctionService] = lambda: mock_function_service
    
    try:
        response = client.get(
            f"/projects/{test_project.uuid}/spans", params={"query_string": "test"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["span_id"] == "test_span_1"
    finally:
        # Clean up overrides
        api.dependency_overrides.pop(get_opensearch_service, None)
        api.dependency_overrides.pop(FunctionService, None)


def test_search_traces_with_parent_child_relationships(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
):
    """Test search traces establishes correct parent-child relationships."""
    mock_hits = [
        {
            "_id": str(uuid4()),
            "_score": 1.0,
            "_source": {
                "organization_uuid": str(test_project.organization_uuid),
                "span_id": "parent_span",
                "parent_span_id": None,
                "type": "function",
                "function_uuid": str(test_function.uuid),
                "scope": "lilypad",
                "cost": 0.001,
                "input_tokens": 100,
                "output_tokens": 50,
                "duration_ms": 1000,
                "created_at": "2024-01-01T00:00:00Z",
                "data": {"attributes": {}},
            },
        },
        {
            "_id": str(uuid4()),
            "_score": 0.9,
            "_source": {
                "organization_uuid": str(test_project.organization_uuid),
                "span_id": "child_span",
                "parent_span_id": "parent_span",
                "type": "function",
                "function_uuid": str(test_function.uuid),
                "scope": "lilypad",
                "cost": 0.0005,
                "input_tokens": 50,
                "output_tokens": 25,
                "duration_ms": 500,
                "created_at": "2024-01-01T00:00:01Z",
                "data": {"attributes": {}},
            },
        },
    ]

    # Create mock OpenSearch service
    mock_opensearch_service = Mock()
    mock_opensearch_service.is_enabled = True
    mock_opensearch_service.search_traces.return_value = mock_hits
    
    # Create mock FunctionService
    mock_function_service = Mock()
    mock_function_service.find_records_by_uuids.return_value = [test_function]
    
    # Override dependencies
    from lilypad.server.api.v0.main import api
    from lilypad.server.services.opensearch import get_opensearch_service
    from lilypad.server.services.functions import FunctionService
    
    api.dependency_overrides[get_opensearch_service] = lambda: mock_opensearch_service
    api.dependency_overrides[FunctionService] = lambda: mock_function_service
    
    try:
        response = client.get(
            f"/projects/{test_project.uuid}/spans", params={"query_string": "test"}
        )

        assert response.status_code == 200
        data = response.json()

        # Should return only root span
        assert len(data) == 1
        assert data[0]["span_id"] == "parent_span"

        # Root span should have child
        assert len(data[0]["child_spans"]) == 1
        assert data[0]["child_spans"][0]["span_id"] == "child_span"
    finally:
        # Clean up overrides
        api.dependency_overrides.pop(get_opensearch_service, None)
        api.dependency_overrides.pop(FunctionService, None)


def test_delete_spans_success(
    client: TestClient,
    test_project: ProjectTable,
    test_spans: list[SpanTable],
):
    """Test successful span deletion."""
    span = test_spans[0]

    with patch(
        "lilypad.server.api.v0.spans_api.get_opensearch_service"
    ) as mock_get_service:
        mock_service = Mock()
        mock_service.is_enabled = True
        mock_get_service.return_value = mock_service

        response = client.delete(f"/projects/{test_project.uuid}/spans/{span.uuid}")

        assert response.status_code == 200
        assert response.json() is True


def test_delete_spans_failure(
    client: TestClient,
    test_project: ProjectTable,
):
    """Test span deletion failure."""
    fake_uuid = uuid4()

    response = client.delete(f"/projects/{test_project.uuid}/spans/{fake_uuid}")

    assert response.status_code == 200
    assert response.json() is False


def test_get_spans_by_function_uuid_paginated(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
    test_spans: list[SpanTable],
):
    """Test getting paginated spans by function UUID."""
    response = client.get(
        f"/projects/{test_project.uuid}/functions/{test_function.uuid}/spans/paginated",
        params={"limit": 2, "offset": 0, "order": "desc"},
    )

    assert response.status_code == 200
    data = response.json()

    assert "items" in data
    assert "limit" in data
    assert "offset" in data
    assert "total" in data
    assert data["limit"] == 2
    assert data["offset"] == 0


def test_get_spans_by_function_uuid_paginated_asc_order(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
    test_spans: list[SpanTable],
):
    """Test getting paginated spans with ascending order."""
    response = client.get(
        f"/projects/{test_project.uuid}/functions/{test_function.uuid}/spans/paginated",
        params={"limit": 10, "offset": 0, "order": "asc"},
    )

    assert response.status_code == 200
    data = response.json()

    assert data["limit"] == 10
    assert data["offset"] == 0


def test_get_recent_spans_empty_result(
    client: TestClient,
    test_project: ProjectTable,
    test_spans: list[SpanTable],
):
    """Test getting recent spans with future timestamp (empty result)."""
    # Use a future timestamp
    since = datetime.now(timezone.utc) + timedelta(hours=1)

    response = client.get(
        f"/projects/{test_project.uuid}/spans/recent",
        params={"since": since.isoformat()},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["spans"]) == 0
    assert data["project_uuid"] == str(test_project.uuid)


def test_get_recent_spans_unauthorized(
    test_project: ProjectTable,
    get_test_session,
):
    """Test getting recent spans without authentication."""
    from fastapi.testclient import TestClient

    from lilypad.server.api.v0.main import api
    from lilypad.server.db.session import get_session

    # Create a client without authentication override
    api.dependency_overrides[get_session] = get_test_session
    client = TestClient(api)

    try:
        response = client.get(
            f"/projects/{test_project.uuid}/spans/recent",
        )
        assert response.status_code == 401
    finally:
        api.dependency_overrides.clear()


def test_get_recent_spans_wrong_project(
    client: TestClient,
):
    """Test getting recent spans for non-existent project."""
    fake_uuid = uuid4()

    response = client.get(
        f"/projects/{fake_uuid}/spans/recent",
    )

    # Should return 200 with empty spans (user has access but no spans exist)
    assert response.status_code == 200
    data = response.json()
    assert len(data["spans"]) == 0


def test_get_recent_spans_ordering(
    client: TestClient,
    test_project: ProjectTable,
    test_spans: list[SpanTable],
):
    """Test that recent spans are ordered by created_at descending."""
    # Get spans from last 5 minutes
    since = datetime.now(timezone.utc) - timedelta(minutes=5)

    response = client.get(
        f"/projects/{test_project.uuid}/spans/recent",
        params={"since": since.isoformat()},
    )

    assert response.status_code == 200
    data = response.json()

    # Should return all 5 root spans
    assert len(data["spans"]) == 5

    # Verify ordering (newest first)
    span_ids = [span["span_id"] for span in data["spans"]]
    expected_order = [
        "span_root_0",
        "span_root_1",
        "span_root_2",
        "span_root_3",
        "span_root_4",
    ]
    assert span_ids == expected_order


def test_get_recent_spans_with_invalid_since(
    client: TestClient,
    test_project: ProjectTable,
):
    """Test getting recent spans with invalid 'since' parameter."""
    response = client.get(
        f"/projects/{test_project.uuid}/spans/recent",
        params={"since": "invalid-date"},
    )

    assert response.status_code == 422  # Validation error


def test_get_recent_spans_performance(
    client: TestClient,
    test_project: ProjectTable,
    session: Session,
    test_function: FunctionTable,
):
    """Test recent spans endpoint performance with many spans."""
    # Create 100 spans
    now = datetime.now(timezone.utc)
    for i in range(100):
        span = SpanTable(
            organization_uuid=test_project.organization_uuid,
            project_uuid=test_project.uuid,
            span_id=f"perf_span_{i}",
            trace_id=f"perf_trace_{i}",  # pyright: ignore [reportCallIssue]
            parent_span_id=None,
            type="function",
            function_uuid=test_function.uuid,
            scope=Scope.LILYPAD,
            cost=0.001,
            input_tokens=100,
            output_tokens=50,
            duration_ms=1000,
            created_at=now - timedelta(seconds=i),
            data={"attributes": {}},
        )
        session.add(span)

    session.commit()

    # Measure response time
    start_time = time.time()

    response = client.get(
        f"/projects/{test_project.uuid}/spans/recent",
    )

    end_time = time.time()
    response_time = end_time - start_time

    assert response.status_code == 200
    # Response should be fast (under 1 second)
    assert response_time < 1.0

    data = response.json()
    # Should return only spans from last 30 seconds
    assert len(data["spans"]) <= 30
