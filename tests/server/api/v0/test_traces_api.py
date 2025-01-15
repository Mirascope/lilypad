"""Tests for the traces API."""

import time
from collections.abc import Generator
from unittest.mock import patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.server.models import (
    APIKeyTable,
    GenerationTable,
    ProjectTable,
    Scope,
    SpanTable,
    SpanType,
)


@pytest.fixture
def test_generation(
    session: Session, test_project: ProjectTable, test_generation: GenerationTable
) -> Generator[GenerationTable, None, None]:
    """Create a test generation.

    Args:
        session: Database session
        test_project: Parent project
        test_generation: The Generation

    Yields:
        GenerationTable: Test generation
    """
    session.add(test_generation)
    session.commit()
    session.refresh(test_generation)
    yield test_generation


@pytest.fixture
def test_span(
    session: Session, test_project: ProjectTable, test_generation: GenerationTable
) -> Generator[SpanTable, None, None]:
    """Create a test span.

    Args:
        session: Database session
        test_project: Parent project
        test_generation: Parent generation

    Yields:
        SpanTable: Test span
    """
    current_time = time.time_ns() // 1_000_000  # Convert to milliseconds

    span = SpanTable(
        span_id="test_span_1",
        organization_uuid=test_project.organization_uuid,
        project_uuid=test_project.uuid,
        generation_uuid=test_generation.uuid,
        type=SpanType.GENERATION,
        scope=Scope.LILYPAD,
        data={
            "start_time": current_time,
            "end_time": current_time + 100,
            "attributes": {
                "lilypad.project_uuid": str(test_project.uuid),
                "lilypad.type": "generation",
                "lilypad.generation.uuid": str(test_generation.uuid),
                "lilypad.generation.name": test_generation.name,
                "lilypad.generation.signature": "def test(): pass",
                "lilypad.generation.code": "def test(): pass",
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


@patch("posthog.Posthog")
def test_post_traces(
    mock_posthog,
    client: TestClient,
    test_project: ProjectTable,
    test_generation: GenerationTable,
    test_api_key: APIKeyTable,
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
                "lilypad.type": "generation",
                "lilypad.generation.uuid": str(test_generation.uuid),
                "lilypad.generation.name": "test_function",
                "lilypad.generation.signature": "def test(): pass",
                "lilypad.generation.code": "def test(): pass",
            },
            "name": "test_function",
        }
    ]

    response = client.post(
        f"/projects/{test_project.uuid}/traces",
        headers={"X-API-Key": test_api_key.key_hash},
        json=trace_data,
    )
    assert response.status_code == 200
    spans = response.json()
    assert len(spans) == 1
    assert spans[0]["span_id"] == "test_span_2"


def test_get_spans_by_version(
    client: TestClient,
    test_project: ProjectTable,
    test_generation: GenerationTable,
    test_span: SpanTable,
):
    """Test getting spans for a version returns expected spans."""
    response = client.get(
        f"/projects/{test_project.uuid}/generations/{test_generation.uuid}/spans"
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
