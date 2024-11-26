"""Tests for the traces API."""

import time
from collections.abc import Generator

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
def test_project(session: Session) -> Generator[ProjectTable, None, None]:
    """Create a test project.

    Args:
        session: Database session

    Yields:
        ProjectTable: Test project
    """
    project = ProjectTable(name="test_project")
    session.add(project)
    session.commit()
    session.refresh(project)
    yield project


@pytest.fixture
def test_function(
    session: Session, test_project: ProjectTable
) -> Generator[FunctionTable, None, None]:
    """Create a test function.

    Args:
        session: Database session
        test_project: Parent project

    Yields:
        FunctionTable: Test function
    """
    function = FunctionTable(
        project_id=test_project.id,
        name="test_function",
        hash="test_hash",
        code="def test(): pass",
    )
    session.add(function)
    session.commit()
    session.refresh(function)
    yield function


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
        version_num=1,
        project_id=test_project.id,
        function_id=test_function.id,
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
        id="test_span_1",
        project_id=test_project.id,
        version_id=test_version.id,
        version_num=test_version.version_num,
        scope=Scope.LILYPAD,
        data={
            "start_time": current_time,
            "end_time": current_time + 100,
            "attributes": {
                "lilypad.function_name": test_version.function_name,
                "lilypad.project_id": test_project.id,
                "lilypad.version_id": test_version.id,
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
    response = client.get(f"/projects/{test_project.id}/traces")
    assert response.status_code == 200
    assert response.json() == []


def test_get_traces_by_project(
    client: TestClient, test_project: ProjectTable, test_span: SpanTable
):
    """Test getting traces for a project returns expected traces."""
    response = client.get(f"/projects/{test_project.id}/traces")
    assert response.status_code == 200
    traces = response.json()
    assert len(traces) == 1
    assert traces[0]["id"] == test_span.id


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
                "lilypad.project_id": test_project.id,
                "lilypad.version_id": test_version.id,
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
    assert spans[0]["id"] == "test_span_2"


def test_get_spans_by_version(
    client: TestClient,
    test_project: ProjectTable,
    test_version: VersionTable,
    test_span: SpanTable,
):
    """Test getting spans for a version returns expected spans."""
    response = client.get(
        f"/projects/{test_project.id}/versions/{test_version.id}/spans"
    )
    assert response.status_code == 200
    spans = response.json()
    assert len(spans) == 1
    assert spans[0]["id"] == test_span.id


def test_get_span_by_id(client: TestClient, test_span: SpanTable):
    """Test getting single span by ID."""
    response = client.get(f"/spans/{test_span.id}")
    assert response.status_code == 200
    span = response.json()
    assert span["display_name"] == "test_function"
    assert span["duration_ms"] == 100


def test_get_nonexistent_span(client: TestClient):
    """Test getting nonexistent span returns 404."""
    response = client.get("/spans/nonexistent_id")
    assert response.status_code == 404
