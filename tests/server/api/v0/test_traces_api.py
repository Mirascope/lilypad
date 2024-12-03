"""Tests for the traces API."""

import time
from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.server.models import (
    FunctionTable,
    ProjectTable,
    Scope,
    SpanTable,
    VersionTable,
)


@pytest.fixture
def test_version(
    session: Session, test_project: ProjectTable, test_function: FunctionTable
) -> Generator[VersionTable, None, None]:
    """Create a test version.

    Args:
        session: Database session
        test_project: Parent project
        test_function: Function for this version

    Yields:
        VersionTable: Test version
    """
    version = VersionTable(
        organization_uuid=test_project.organization_uuid,
        version_num=1,
        project_uuid=test_project.uuid,
        function_uuid=test_function.uuid,
        function_name=test_function.name,
        function_hash=test_function.hash,
        is_active=True,
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    yield version


@pytest.fixture
def test_span(
    session: Session, test_project: ProjectTable, test_version: VersionTable
) -> Generator[SpanTable, None, None]:
    """Create a test span.

    Args:
        session: Database session
        test_project: Parent project
        test_version: Parent version

    Yields:
        SpanTable: Test span
    """
    current_time = time.time_ns() // 1_000_000  # Convert to milliseconds

    span = SpanTable(
        span_id="test_span_1",
        organization_uuid=test_project.organization_uuid,
        project_uuid=test_project.uuid,
        version_uuid=test_version.uuid,
        version_num=test_version.version_num,
        scope=Scope.LILYPAD,
        data={
            "start_time": current_time,
            "end_time": current_time + 100,
            "attributes": {
                "lilypad.function_name": test_version.function_name,
                "lilypad.project_uuid": str(test_project.uuid),
                "lilypad.version_uuid": str(test_version.uuid),
                "lilypad.version_num": test_version.version_num,
                "lilypad.lexical_closure": "def test(): pass",
            },
            "name": "test_function",
        },
    )
    session.add(span)
    session.commit()
    session.refresh(span)
    yield span


def test_get_empty_traces(client: TestClient, test_project: ProjectTable):
    """Test getting traces when no traces exist."""
    response = client.get(f"/projects/{test_project.uuid}/traces")
    assert response.status_code == 200
    assert response.json() == []


def test_get_traces_by_project(
    client: TestClient, test_project: ProjectTable, test_span: SpanTable
):
    """Test getting traces for a project returns expected traces."""
    response = client.get(f"/projects/{test_project.uuid}/traces")
    assert response.status_code == 200
    traces = response.json()
    assert len(traces) == 1
    assert traces[0]["span_id"] == test_span.span_id


def test_post_traces(
    client: TestClient, test_project: ProjectTable, test_version: VersionTable
):
    """Test posting trace data creates expected spans."""
    current_time = time.time_ns() // 1_000_000  # Convert to milliseconds

    trace_data = [
        {
            "span_id": "test_span_2",
            "instrumentation_scope": {"name": "lilypad"},
            "start_time": current_time,
            "end_time": current_time + 100,
            "attributes": {
                "lilypad.project_uuid": str(test_project.uuid),
                "lilypad.version_uuid": str(test_version.uuid),
                "lilypad.version_num": 1,
                "lilypad.function_name": "test_function",
                "lilypad.lexical_closure": "def test(): pass",
            },
            "name": "test_function",
        }
    ]

    response = client.post("/traces", json=trace_data)
    assert response.status_code == 200
    spans = response.json()
    assert len(spans) == 1
    assert spans[0]["span_id"] == "test_span_2"


def test_get_spans_by_version(
    client: TestClient,
    test_project: ProjectTable,
    test_version: VersionTable,
    test_span: SpanTable,
):
    """Test getting spans for a version returns expected spans."""
    response = client.get(
        f"/projects/{test_project.uuid}/versions/{test_version.uuid}/spans"
    )
    assert response.status_code == 200
    spans = response.json()
    assert len(spans) == 1
    assert spans[0]["span_id"] == test_span.span_id


def test_get_span_by_uuid(client: TestClient, test_span: SpanTable):
    """Test getting single span by ID."""
    response = client.get(f"/spans/{test_span.uuid}")
    assert response.status_code == 200
    span = response.json()
    assert span["display_name"] == "test_function"
    assert span["duration_ms"] == 100


def test_get_nonexistent_span(client: TestClient):
    """Test getting nonexistent span returns 404."""
    span_uuid = UUID("123e4567-e89b-12d3-a456-426614174000")
    response = client.get(f"/spans/{span_uuid}")
    assert response.status_code == 404
