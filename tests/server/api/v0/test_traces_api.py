"""Tests for the traces API."""

import time
from collections.abc import Generator
from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from sqlmodel import Session

from lilypad.server.api.v0.traces_api import _process_span
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
        duration_ms=100,
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
            "name": "test_span",
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
    span = response.json()
    assert span["span_id"] == "test_span_2"


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
    assert span["display_name"] == "test_span"
    assert span["duration_ms"] == 100


def test_get_nonexistent_span(client: TestClient):
    """Test getting nonexistent span returns 404."""
    span_uuid = UUID("123e4567-e89b-12d3-a456-426614174000")
    response = client.get(f"/spans/{span_uuid}")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_process_lilypad_span():
    """Test processing a lilypad span with no children"""
    trace = {
        "span_id": "span1",
        "start_time": 1000,
        "end_time": 2000,
        "attributes": {
            "lilypad.type": "generation",
            "lilypad.generation.uuid": "123e4567-e89b-12d3-a456-426614174000",
            "lilypad.prompt.uuid": "123e4567-e89b-12d3-a456-426614174001",
        },
        "instrumentation_scope": {"name": "lilypad"},
    }
    parent_to_children = {"span1": []}
    span_creates = []

    result = await _process_span(trace, parent_to_children, span_creates)

    assert result.span_id == "span1"
    assert result.type == "generation"
    assert result.scope == Scope.LILYPAD
    assert result.cost == 0
    assert result.input_tokens == 0
    assert result.output_tokens == 0
    assert result.duration_ms == 1000
    assert len(span_creates) == 1


@pytest.mark.asyncio
async def test_process_llm_span_with_openrouter():
    """Test processing an LLM span using openrouter"""
    trace = {
        "span_id": "span1",
        "start_time": 1000,
        "end_time": 2000,
        "attributes": {
            "lilypad.type": "generation",
            gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS: 100,
            gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS: 50,
            gen_ai_attributes.GEN_AI_SYSTEM: "openrouter",
            gen_ai_attributes.GEN_AI_RESPONSE_MODEL: "gpt-4",
        },
        "instrumentation_scope": {"name": "other"},
    }
    parent_to_children = {"span1": []}
    span_creates = []

    with patch(
        "lilypad.server.api.v0.traces_api.calculate_openrouter_cost",
        new_callable=AsyncMock,
    ) as mock_calc:
        mock_calc.return_value = 0.123
        result = await _process_span(trace, parent_to_children, span_creates)
    assert result.scope == Scope.LLM
    assert result.cost == 0.123
    assert result.input_tokens == 100
    assert result.output_tokens == 50


@pytest.mark.asyncio
async def test_process_llm_span_with_other_system():
    """Test processing an LLM span using a non-openrouter system"""
    trace = {
        "span_id": "span1",
        "start_time": 1000,
        "end_time": 2000,
        "attributes": {
            gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS: 100,
            gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS: 50,
            gen_ai_attributes.GEN_AI_SYSTEM: "anthropic",
            gen_ai_attributes.GEN_AI_RESPONSE_MODEL: "claude-2.0",
        },
        "instrumentation_scope": {"name": "other"},
    }
    parent_to_children = {"span1": []}
    span_creates = []

    result = await _process_span(trace, parent_to_children, span_creates)

    assert result.scope == Scope.LLM
    assert result.cost == 0.002
    assert result.input_tokens == 100
    assert result.output_tokens == 50


@pytest.mark.asyncio
async def test_process_span_with_children():
    """Test processing a span with child spans"""
    parent_trace = {
        "span_id": "parent",
        "start_time": 1000,
        "end_time": 2000,
        "attributes": {},
        "instrumentation_scope": {"name": "lilypad"},
    }

    child_trace = {
        "span_id": "child",
        "start_time": 1200,
        "end_time": 1800,
        "attributes": {
            gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS: 50,
            gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS: 25,
            gen_ai_attributes.GEN_AI_SYSTEM: "anthropic",
            gen_ai_attributes.GEN_AI_RESPONSE_MODEL: "claude-2.0",
        },
        "instrumentation_scope": {"name": "other"},
    }

    parent_to_children = {"parent": [child_trace], "child": []}
    span_creates = []

    result = await _process_span(parent_trace, parent_to_children, span_creates)

    assert result.scope == Scope.LILYPAD
    assert result.cost == 0.001
    assert result.input_tokens == 50
    assert result.output_tokens == 25
    assert len(span_creates) == 2
    assert span_creates[0].span_id == "parent"
    assert span_creates[1].span_id == "child"


@pytest.mark.asyncio
async def test_process_span_with_invalid_uuids():
    """Test processing a span with invalid UUID strings"""
    trace = {
        "span_id": "span1",
        "start_time": 1000,
        "end_time": 2000,
        "attributes": {
            "lilypad.generation.uuid": "invalid-uuid",
            "lilypad.prompt.uuid": "invalid-uuid",
        },
        "instrumentation_scope": {"name": "lilypad"},
    }
    parent_to_children = {"span1": []}
    span_creates = []

    with pytest.raises(ValueError):
        await _process_span(trace, parent_to_children, span_creates)


@pytest.mark.asyncio
async def test_process_span_without_cost_calculation():
    """Test processing an LLM span without sufficient attributes for cost calculation"""
    trace = {
        "span_id": "span1",
        "start_time": 1000,
        "end_time": 2000,
        "attributes": {
            gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS: 100,
            gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS: 50,
        },
        "instrumentation_scope": {"name": "other"},
    }
    parent_to_children = {"span1": []}
    span_creates = []

    result = await _process_span(trace, parent_to_children, span_creates)

    assert result.scope == Scope.LLM
    assert result.cost == 0
    assert result.input_tokens == 100
    assert result.output_tokens == 50
