"""Tests for the spans API."""

import time
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.server.models import (
    APIKeyTable,
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
    now = datetime.now(UTC)
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
                "attributes": {
                    "lilypad.type": "function",
                    "lilypad.function.uuid": str(test_function.uuid),
                }
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
                "attributes": {
                    "lilypad.type": "function",
                }
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
    test_api_key: APIKeyTable,
    test_project: ProjectTable,
    test_spans: list[SpanTable],
):
    """Test getting recent spans without 'since' parameter (default 30 seconds)."""
    response = client.get(
        f"/projects/{test_project.uuid}/spans/recent",
        headers={"X-API-Key": test_api_key.key_hash},
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
    assert (datetime.now(UTC) - timestamp).total_seconds() < 5


def test_get_recent_spans_with_since_parameter(
    client: TestClient,
    test_api_key: APIKeyTable,
    test_project: ProjectTable,
    test_spans: list[SpanTable],
):
    """Test getting recent spans with specific 'since' timestamp."""
    # Get spans from last 3 minutes
    since = datetime.now(UTC) - timedelta(minutes=3)

    response = client.get(
        f"/projects/{test_project.uuid}/spans/recent",
        params={"since": since.isoformat()},
        headers={"X-API-Key": test_api_key.key_hash},
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


def test_get_recent_spans_empty_result(
    client: TestClient,
    test_api_key: APIKeyTable,
    test_project: ProjectTable,
    test_spans: list[SpanTable],
):
    """Test getting recent spans with future timestamp (empty result)."""
    # Use a future timestamp
    since = datetime.now(UTC) + timedelta(hours=1)

    response = client.get(
        f"/projects/{test_project.uuid}/spans/recent",
        params={"since": since.isoformat()},
        headers={"X-API-Key": test_api_key.key_hash},
    )

    assert response.status_code == 200
    data = response.json()

    assert len(data["spans"]) == 0
    assert data["project_uuid"] == str(test_project.uuid)


def test_get_recent_spans_unauthorized(
    client: TestClient,
    test_project: ProjectTable,
):
    """Test getting recent spans without API key."""
    response = client.get(
        f"/projects/{test_project.uuid}/spans/recent",
    )

    assert response.status_code == 401


def test_get_recent_spans_wrong_project(
    client: TestClient,
    test_api_key: APIKeyTable,
):
    """Test getting recent spans for non-existent project."""
    fake_uuid = uuid4()

    response = client.get(
        f"/projects/{fake_uuid}/spans/recent",
        headers={"X-API-Key": test_api_key.key_hash},
    )

    # API key validation fails with 400 when project doesn't match
    assert response.status_code == 400
    assert "Invalid Project ID" in response.json()["detail"]


def test_get_recent_spans_ordering(
    client: TestClient,
    test_api_key: APIKeyTable,
    test_project: ProjectTable,
    test_spans: list[SpanTable],
):
    """Test that recent spans are ordered by created_at descending."""
    # Get spans from last 5 minutes
    since = datetime.now(UTC) - timedelta(minutes=5)

    response = client.get(
        f"/projects/{test_project.uuid}/spans/recent",
        params={"since": since.isoformat()},
        headers={"X-API-Key": test_api_key.key_hash},
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
    test_api_key: APIKeyTable,
    test_project: ProjectTable,
):
    """Test getting recent spans with invalid 'since' parameter."""
    response = client.get(
        f"/projects/{test_project.uuid}/spans/recent",
        params={"since": "invalid-date"},
        headers={"X-API-Key": test_api_key.key_hash},
    )

    assert response.status_code == 422  # Validation error


def test_get_recent_spans_performance(
    client: TestClient,
    test_api_key: APIKeyTable,
    test_project: ProjectTable,
    session: Session,
    test_function: FunctionTable,
):
    """Test recent spans endpoint performance with many spans."""
    # Create 100 spans
    now = datetime.now(UTC)
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
        headers={"X-API-Key": test_api_key.key_hash},
    )

    end_time = time.time()
    response_time = end_time - start_time

    assert response.status_code == 200
    # Response should be fast (under 1 second)
    assert response_time < 1.0

    data = response.json()
    # Should return only spans from last 30 seconds
    assert len(data["spans"]) <= 30
