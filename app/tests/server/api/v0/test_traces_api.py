"""Tests for the traces API."""

import time
from collections.abc import Generator
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from sqlmodel import Session

from lilypad.server.api.v0.traces_api import _process_span
from lilypad.server.models import (
    APIKeyTable,
    FunctionTable,
    ProjectTable,
    Scope,
    SpanTable,
    SpanType,
)


@pytest.fixture
def test_function(
    session: Session, test_project: ProjectTable, test_function: FunctionTable
) -> Generator[FunctionTable, None, None]:
    """Create a test function.

    Args:
        session: Database session
        test_project: Parent project
        test_function: The Function

    Yields:
        FunctionTable: Test function
    """
    session.add(test_function)
    session.commit()
    session.refresh(test_function)
    yield test_function


@pytest.fixture
def test_span(
    session: Session, test_project: ProjectTable, test_function: FunctionTable
) -> Generator[SpanTable, None, None]:
    """Create a test span.

    Args:
        session: Database session
        test_project: Parent project
        test_function: Parent function

    Yields:
        SpanTable: Test span
    """
    current_time = time.time_ns() // 1_000_000  # Convert to milliseconds

    span = SpanTable(
        span_id="test_span_1",
        trace_id="test_trace_1",
        organization_uuid=test_project.organization_uuid,
        project_uuid=test_project.uuid,
        function_uuid=test_function.uuid,
        type=SpanType.FUNCTION,
        scope=Scope.LILYPAD,
        duration_ms=100,
        data={
            "start_time": current_time,
            "end_time": current_time + 100,
            "attributes": {
                "lilypad.project_uuid": str(test_project.uuid),
                "lilypad.type": "function",
                "lilypad.function.uuid": str(test_function.uuid),
                "lilypad.function.name": test_function.name,
                "lilypad.function.signature": "def test(): pass",
                "lilypad.function.code": "def test(): pass",
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
    assert response.json() == {"items": [], "limit": 100, "offset": 0, "total": 0}


def test_get_traces_by_project(
    client: TestClient, test_project: ProjectTable, test_span: SpanTable
):
    """Test getting traces for a project returns expected traces."""
    response = client.get(f"/projects/{test_project.uuid}/traces")
    assert response.status_code == 200
    traces = response.json()
    assert len(traces["items"]) == 1
    assert traces["items"][0]["span_id"] == test_span.span_id


def test_post_traces(
    client: TestClient,
    test_project: ProjectTable,
    test_function: FunctionTable,
    test_api_key: APIKeyTable,
):
    """Test posting trace data creates expected spans."""
    # Mock Kafka to be unavailable
    from fastapi import FastAPI

    from lilypad.server.services import get_span_kafka_service

    mock_kafka_service = MagicMock()
    mock_kafka_service.send_batch = AsyncMock(return_value=False)

    app: FastAPI = client.app  # pyright: ignore [reportAssignmentType]
    app.dependency_overrides[get_span_kafka_service] = lambda: mock_kafka_service

    try:
        current_time = time.time_ns() // 1_000_000  # Convert to milliseconds

        trace_data = [
            {
                "span_id": "test_span_2",
                "trace_id": "test_trace_2",

                "instrumentation_scope": {"name": "lilypad"},
                "start_time": current_time,
                "end_time": current_time + 100,
                "attributes": {
                    "lilypad.project_uuid": str(test_project.uuid),
                    "lilypad.type": "function",
                    "lilypad.function.uuid": str(test_function.uuid),
                    "lilypad.function.name": "test_function",
                    "lilypad.function.signature": "def test(): pass",
                    "lilypad.function.code": "def test(): pass",
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
        result = response.json()
        # Since Kafka is mocked to be unavailable, it should process synchronously
        assert result["trace_status"] == "processed"
        assert result["span_count"] == 1
        assert "message" in result
    finally:
        # Clean up the override
        app.dependency_overrides.pop(get_span_kafka_service, None)


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
        "trace_id": "trace1",
        "start_time": 1000,
        "end_time": 2000,
        "attributes": {
            "lilypad.type": "function",
            "lilypad.function.uuid": "123e4567-e89b-12d3-a456-426614174000",
            "lilypad.prompt.uuid": "123e4567-e89b-12d3-a456-426614174001",
        },
        "instrumentation_scope": {"name": "lilypad"},
    }
    parent_to_children = {"span1": []}
    span_creates = []

    result = await _process_span(trace, parent_to_children, span_creates)

    assert result.span_id == "span1"
    assert result.type == "function"
    assert result.scope == Scope.LILYPAD
    assert result.cost == 0
    assert result.input_tokens is None
    assert result.output_tokens is None
    assert result.duration_ms == 1000
    assert len(span_creates) == 1


@pytest.mark.asyncio
async def test_process_span_without_trace_id():
    """Test processing a span without trace_id (legacy span)"""
    trace = {
        "span_id": "span-legacy",
        # Note: trace_id is intentionally missing
        "start_time": 1000,
        "end_time": 2000,
        "attributes": {
            "lilypad.type": "function",
        },
        "instrumentation_scope": {"name": "lilypad"},
    }
    parent_to_children = {"span-legacy": []}
    span_creates = []

    result = await _process_span(trace, parent_to_children, span_creates)

    assert result.span_id == "span-legacy"
    assert result.trace_id is None  # Should handle missing trace_id gracefully
    assert result.type == "function"
    assert result.scope == Scope.LILYPAD
    assert result.duration_ms == 1000
    assert len(span_creates) == 1


@pytest.mark.asyncio
async def test_process_llm_span_with_openrouter():
    """Test processing an LLM span using openrouter"""
    trace = {
        "span_id": "span1",
        "trace_id": "trace1",
        "start_time": 1000,
        "end_time": 2000,
        "attributes": {
            "lilypad.type": "function",
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
        "lilypad.server._utils.span_processing.calculate_openrouter_cost",
        return_value=0.123,
    ):
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
        "trace_id": "trace1",
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
        "trace_id": "trace1",
        "start_time": 1000,
        "end_time": 2000,
        "attributes": {},
        "instrumentation_scope": {"name": "lilypad"},
    }

    child_trace = {
        "span_id": "child",
        "trace_id": "trace1",
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
        "trace_id": "trace1",
        "start_time": 1000,
        "end_time": 2000,
        "attributes": {
            "lilypad.function.uuid": "invalid-uuid",
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
        "trace_id": "trace1",
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


def test_create_traces_with_kafka_success(
    client: TestClient,
    test_api_key: APIKeyTable,
    test_project: ProjectTable,
    test_function: FunctionTable,
):
    """Test creating traces with Kafka queue (success case)."""
    traces_data = [
        {
            "span_id": "span_root",
            "trace_id": "trace123",
            "parent_span_id": None,
            "start_time": int(time.time() * 1000),
            "end_time": int(time.time() * 1000) + 1000,
            "attributes": {
                "lilypad.type": "function",
                "lilypad.function.uuid": str(test_function.uuid),
            },
            "instrumentation_scope": {"name": "lilypad"},
        },
        {
            "span_id": "span_child",
            "trace_id": "trace123",
            "parent_span_id": "span_root",
            "start_time": int(time.time() * 1000),
            "end_time": int(time.time() * 1000) + 500,
            "attributes": {
                "lilypad.type": "function",
                gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS: 100,
                gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS: 50,
                gen_ai_attributes.GEN_AI_SYSTEM: "anthropic",
                gen_ai_attributes.GEN_AI_RESPONSE_MODEL: "claude-2.0",
            },
            "instrumentation_scope": {"name": "other"},
        },
    ]

    # Import necessary modules
    from lilypad.server.services import get_span_kafka_service

    # Create mock Kafka service
    mock_kafka_service = MagicMock()
    mock_kafka_service.send_batch = AsyncMock(return_value=True)

    # Override the FastAPI dependency
    from fastapi import FastAPI

    app: FastAPI = client.app  # pyright: ignore [reportAssignmentType]

    # Override the dependency
    app.dependency_overrides[get_span_kafka_service] = lambda: mock_kafka_service

    try:
        response = client.post(
            f"/projects/{test_project.uuid}/traces",
            json=traces_data,
            headers={"X-API-Key": test_api_key.key_hash},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["trace_status"] == "queued"
        assert data["span_count"] == 2
        assert data["message"] == "Spans queued for processing"

        # Verify Kafka was called
        mock_kafka_service.send_batch.assert_called_once()
        sent_spans = mock_kafka_service.send_batch.call_args[0][0]
        assert len(sent_spans) == 2
        # Verify project UUID was added to attributes
        assert sent_spans[0]["attributes"]["lilypad.project.uuid"] == str(
            test_project.uuid
        )
    finally:
        # Clean up the override
        app.dependency_overrides.pop(get_span_kafka_service, None)


def test_create_traces_kafka_unavailable_fallback(
    client: TestClient,
    test_api_key: APIKeyTable,
    test_project: ProjectTable,
    test_function: FunctionTable,
):
    """Test creating traces when Kafka is unavailable (fallback to sync)."""
    from lilypad.server.services import get_span_kafka_service

    traces_data = [
        {
            "span_id": "span_root",
            "trace_id": "trace123",
            "parent_span_id": None,
            "start_time": int(time.time() * 1000),
            "end_time": int(time.time() * 1000) + 1000,
            "attributes": {
                "lilypad.type": "function",
                "lilypad.function.uuid": str(test_function.uuid),
            },
            "instrumentation_scope": {"name": "lilypad"},
        },
    ]

    # Create mock Kafka service that returns False (unavailable)
    mock_kafka_service = MagicMock()
    mock_kafka_service.send_batch = AsyncMock(return_value=False)

    # Override the FastAPI dependency
    from fastapi import FastAPI

    app: FastAPI = client.app  # pyright: ignore [reportAssignmentType]

    # Override the dependency
    app.dependency_overrides[get_span_kafka_service] = lambda: mock_kafka_service

    try:
        response = client.post(
            f"/projects/{test_project.uuid}/traces",
            json=traces_data,
            headers={"X-API-Key": test_api_key.key_hash},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["trace_status"] == "processed"
        assert data["span_count"] == 1
        assert data["message"] == "Spans processed synchronously"
    finally:
        # Clean up the override
        app.dependency_overrides.pop(get_span_kafka_service, None)


def test_create_traces_cloud_limit_exceeded(
    client: TestClient,
    test_api_key: APIKeyTable,
    test_project: ProjectTable,
):
    """Test creating traces when cloud limit is exceeded."""
    from ee.validate import LicenseInfo, Tier
    from lilypad.ee.server.require_license import (
        get_organization_license,
        is_lilypad_cloud,
    )
    from lilypad.server.api.v0.main import api
    from lilypad.server.services.spans import SpanService

    traces_data = [
        {
            "span_id": "span_root",
            "trace_id": "trace123",
            "parent_span_id": None,
            "start_time": int(time.time() * 1000),
            "end_time": int(time.time() * 1000) + 1000,
            "attributes": {},
            "instrumentation_scope": {"name": "lilypad"},
        },
    ]

    # Create mock span service
    mock_span_service = MagicMock(spec=SpanService)
    mock_span_service.count_by_current_month = MagicMock(return_value=10001)

    # Override dependencies
    def override_span_service():
        return mock_span_service

    def override_is_lilypad_cloud():
        return True

    def override_get_organization_license():
        return LicenseInfo(
            customer="test",
            license_id="test_license",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            tier=Tier.FREE,
            organization_uuid=test_project.organization_uuid,
        )

    api.dependency_overrides[SpanService] = override_span_service
    api.dependency_overrides[is_lilypad_cloud] = override_is_lilypad_cloud
    api.dependency_overrides[get_organization_license] = (
        override_get_organization_license
    )

    try:
        # Mock cloud features
        with patch("lilypad.server.api.v0.traces_api.cloud_features") as mock_features:
            mock_features.__getitem__.return_value = MagicMock(traces_per_month=10000)

            response = client.post(
                f"/projects/{test_project.uuid}/traces",
                json=traces_data,
                headers={"X-API-Key": test_api_key.key_hash},
            )

        assert response.status_code == 402
        assert "Exceeded the maximum number of traces" in response.json()["detail"]
    finally:
        # Clean up overrides
        api.dependency_overrides.pop(SpanService, None)
        api.dependency_overrides.pop(is_lilypad_cloud, None)
        api.dependency_overrides.pop(get_organization_license, None)


@pytest.mark.asyncio
async def test_process_span_with_kafka_attributes():
    """Test processing span preserves Kafka-required attributes."""
    trace = {
        "span_id": "span1",
        "trace_id": "trace123",
        "start_time": 1000,
        "end_time": 2000,
        "attributes": {
            "lilypad.project.uuid": "550e8400-e29b-41d4-a716-446655440000",
            "lilypad.function.uuid": "660e8400-e29b-41d4-a716-446655440000",
        },
        "instrumentation_scope": {"name": "lilypad"},
    }
    parent_to_children = {"span1": []}
    span_creates = []

    result = await _process_span(trace, parent_to_children, span_creates)

    # Original attributes should be preserved in data
    assert (
        result.data["attributes"]["lilypad.project.uuid"]
        == "550e8400-e29b-41d4-a716-446655440000"
    )


def test_convert_system_to_provider():
    """Test converting system names to provider names."""
    from lilypad.server._utils.span_processing import _convert_system_to_provider

    # Test Azure conversion
    assert _convert_system_to_provider("az.ai.inference") == "azure"

    # Test Google conversion
    assert _convert_system_to_provider("google_genai") == "google"

    # Test passthrough for other systems
    assert _convert_system_to_provider("anthropic") == "anthropic"
    assert _convert_system_to_provider("openai") == "openai"


def test_create_traces_no_attributes(
    client: TestClient,
    test_api_key: APIKeyTable,
    test_project: ProjectTable,
    test_function: FunctionTable,
):
    """Test creating traces without attributes field."""
    from lilypad.server.services import get_span_kafka_service

    traces_data = [
        {
            "span_id": "span_no_attrs",
            "trace_id": "trace123",
            "parent_span_id": None,
            "start_time": int(time.time() * 1000),
            "end_time": int(time.time() * 1000) + 1000,
            # No attributes field
            "instrumentation_scope": {"name": "lilypad"},
        },
    ]

    # Mock Kafka service to be unavailable (force sync processing)
    mock_kafka_service = MagicMock()
    mock_kafka_service.send_batch = AsyncMock(return_value=False)

    from fastapi import FastAPI

    app: FastAPI = client.app  # pyright: ignore [reportAssignmentType]
    app.dependency_overrides[get_span_kafka_service] = lambda: mock_kafka_service

    try:
        response = client.post(
            f"/projects/{test_project.uuid}/traces",
            json=traces_data,
            headers={"X-API-Key": test_api_key.key_hash},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["trace_status"] == "processed"
        assert data["span_count"] == 1
    finally:
        app.dependency_overrides.pop(get_span_kafka_service, None)


def test_create_traces_with_parent_child_relationship(
    client: TestClient,
    test_api_key: APIKeyTable,
    test_project: ProjectTable,
    test_function: FunctionTable,
):
    """Test creating traces with parent-child relationships processed correctly."""
    from lilypad.server.services import get_span_kafka_service

    current_time = int(time.time() * 1000)
    traces_data = [
        {
            "span_id": "child1",
            "trace_id": "trace123",
            "parent_span_id": "parent",  # Parent defined later
            "start_time": current_time + 100,
            "end_time": current_time + 400,
            "attributes": {
                "lilypad.type": "function",
                "lilypad.function.uuid": str(test_function.uuid),
            },
            "instrumentation_scope": {"name": "lilypad"},
        },
        {
            "span_id": "parent",
            "trace_id": "trace123",
            "parent_span_id": None,  # Root span
            "start_time": current_time,
            "end_time": current_time + 1000,
            "attributes": {
                "lilypad.type": "function",
                "lilypad.function.uuid": str(test_function.uuid),
            },
            "instrumentation_scope": {"name": "lilypad"},
        },
        {
            "span_id": "child2",
            "trace_id": "trace123",
            "parent_span_id": "parent",
            "start_time": current_time + 500,
            "end_time": current_time + 800,
            "attributes": {
                "lilypad.type": "function",
                "lilypad.function.uuid": str(test_function.uuid),
            },
            "instrumentation_scope": {"name": "lilypad"},
        },
    ]

    # Mock Kafka service to be unavailable (force sync processing)
    mock_kafka_service = MagicMock()
    mock_kafka_service.send_batch = AsyncMock(return_value=False)

    from fastapi import FastAPI

    app: FastAPI = client.app  # pyright: ignore [reportAssignmentType]
    app.dependency_overrides[get_span_kafka_service] = lambda: mock_kafka_service

    try:
        response = client.post(
            f"/projects/{test_project.uuid}/traces",
            json=traces_data,
            headers={"X-API-Key": test_api_key.key_hash},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["trace_status"] == "processed"
        assert data["span_count"] == 3
    finally:
        app.dependency_overrides.pop(get_span_kafka_service, None)


def test_create_traces_billing_error(
    client: TestClient,
    test_api_key: APIKeyTable,
    test_project: ProjectTable,
    test_function: FunctionTable,
):
    """Test creating traces when billing service fails but traces still succeed."""
    from lilypad.server.services import get_span_kafka_service
    from lilypad.server.services.billing import BillingService

    traces_data = [
        {
            "span_id": "span_billing_error",
            "trace_id": "trace123",
            "parent_span_id": None,
            "start_time": int(time.time() * 1000),
            "end_time": int(time.time() * 1000) + 1000,
            "attributes": {
                "lilypad.type": "function",
                "lilypad.function.uuid": str(test_function.uuid),
            },
            "instrumentation_scope": {"name": "lilypad"},
        },
    ]

    # Mock Kafka service to be unavailable (force sync processing)
    mock_kafka_service = MagicMock()
    mock_kafka_service.send_batch = AsyncMock(return_value=False)

    # Mock billing service to raise an exception
    mock_billing_service = MagicMock(spec=BillingService)
    mock_billing_service.report_span_usage_with_fallback = AsyncMock(
        side_effect=Exception("Billing service error")
    )

    from fastapi import FastAPI

    app: FastAPI = client.app  # pyright: ignore [reportAssignmentType]

    app.dependency_overrides[get_span_kafka_service] = lambda: mock_kafka_service
    app.dependency_overrides[BillingService] = lambda: mock_billing_service

    try:
        response = client.post(
            f"/projects/{test_project.uuid}/traces",
            json=traces_data,
            headers={"X-API-Key": test_api_key.key_hash},
        )

        # Should still succeed despite billing error
        assert response.status_code == 200
        data = response.json()
        assert data["trace_status"] == "processed"
        assert data["span_count"] == 1

        # Verify billing was attempted
        mock_billing_service.report_span_usage_with_fallback.assert_called_once()
    finally:
        app.dependency_overrides.pop(get_span_kafka_service, None)
        app.dependency_overrides.pop(BillingService, None)


# ===== Additional Edge Case Tests =====


def test_convert_system_to_provider_azure():
    """Test _convert_system_to_provider for azure."""
    from lilypad.server._utils.span_processing import _convert_system_to_provider

    result = _convert_system_to_provider("az.ai.inference")
    assert result == "azure"


def test_convert_system_to_provider_google():
    """Test _convert_system_to_provider for google."""
    from lilypad.server._utils.span_processing import _convert_system_to_provider

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
            mock_kafka_service = MagicMock()
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


def test_traces_opensearch_indexing(client: TestClient, test_project: ProjectTable):
    """Test OpenSearch indexing in traces endpoint."""
    import asyncio

    from lilypad.server.api.v0.traces_api import traces

    # Create mock objects
    mock_span = MagicMock(spec=SpanTable)
    mock_span.model_dump.return_value = {"span_id": "test", "data": "test"}

    # Call the traces function directly with all mocks
    match_api_key = True
    license = MagicMock(tier="free")
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

    mock_span_service = MagicMock()
    mock_span_service.count_by_current_month.return_value = 0
    mock_span_service.create_bulk_records.return_value = [mock_span]

    mock_opensearch_service = MagicMock()
    mock_opensearch_service.is_enabled = True

    mock_background_tasks = MagicMock()

    mock_project_service = MagicMock()
    mock_project_service.find_record_no_organization.return_value = test_project

    mock_billing_service = MagicMock()
    mock_billing_service.report_span_usage_with_fallback = AsyncMock()

    mock_user = MagicMock(uuid=UUID("12345678-1234-5678-1234-567812345678"))

    mock_kafka_service = MagicMock()
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
            uuid=UUID("12345678-1234-5678-1234-567812345678"),
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
            uuid=UUID("12345678-1234-5678-1234-567812345678"),
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
