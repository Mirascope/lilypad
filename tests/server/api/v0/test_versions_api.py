"""Tests for the versions API."""

from collections.abc import Generator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.server.models import (
    FunctionTable,
    OpenAICallParams,
    ProjectTable,
    PromptTable,
    Provider,
    ResponseFormat,
    VersionTable,
)


@pytest.fixture
def test_prompt(
    session: Session, test_project: ProjectTable
) -> Generator[PromptTable, None, None]:
    """Create a test prompt."""
    call_params = OpenAICallParams(
        max_tokens=100,
        temperature=0.7,
        top_p=1.0,
        response_format=ResponseFormat(type="text"),
    ).model_dump()

    prompt = PromptTable(
        organization_uuid=test_project.organization_uuid,
        project_uuid=test_project.uuid,
        template="Test template",
        provider=Provider.OPENAI,
        model="gpt-4",
        hash="test_hash",
        call_params=call_params,
    )
    session.add(prompt)
    session.commit()
    session.refresh(prompt)
    yield prompt


@pytest.fixture
def test_version(
    session: Session,
    test_project: ProjectTable,
    test_function: FunctionTable,
    test_prompt: PromptTable,
) -> Generator[VersionTable, None, None]:
    """Create a test version with all required relationships."""
    version = VersionTable(
        organization_uuid=test_project.organization_uuid,
        version_num=1,
        project_uuid=test_project.uuid,
        function_uuid=test_function.uuid,
        prompt_uuid=test_prompt.uuid,
        function_name=test_function.name,
        function_hash=test_function.hash,
        prompt_hash=test_prompt.hash,
        is_active=True,
    )
    session.add(version)
    session.commit()
    session.refresh(version)
    yield version


def test_create_version(client: TestClient, test_project: ProjectTable):
    """Test version creation with function and prompt."""
    data = {
        "function_create": {
            "name": "test_function",
            "hash": "test_hash",
            "code": "def test(): pass",
            "arg_types": {"arg1": "str"},
        },
        "prompt_create": {
            "template": "Test template",
            "provider": Provider.OPENAI.value,
            "model": "gpt-4",
            "call_params": {
                "max_tokens": 100,
                "temperature": 0.7,
                "top_p": 1.0,
                "response_format": {"type": "text"},
            },
        },
    }

    response = client.post(f"/projects/{test_project.uuid}/versions", json=data)
    assert response.status_code == 200
    created = response.json()
    assert created["function_name"] == "test_function"
    assert created["version_num"] == 1
    assert created["is_active"] is True
    assert created["prompt"]["call_params"] is not None


def test_get_version(client: TestClient, test_version: VersionTable):
    """Test getting version by UUID returns expected version."""
    response = client.get(
        f"/projects/{test_version.project_uuid}/versions/{test_version.uuid}"
    )
    assert response.status_code == 200
    version = response.json()
    assert version["function_name"] == test_version.function_name
    assert version["prompt"]["call_params"] is not None
    assert version["prompt"]["call_params"]["max_tokens"] == 100


def test_get_versions_by_function(client: TestClient, test_version: VersionTable):
    """Test getting versions for a function returns expected versions."""
    response = client.get(
        f"/projects/{test_version.project_uuid}/functions/name/{test_version.function_name}/versions"
    )
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) == 1
    assert versions[0]["function_name"] == test_version.function_name
    assert versions[0]["prompt"]["call_params"] is not None
    assert versions[0]["prompt"]["call_params"]["max_tokens"] == 100


def test_get_nonexistent_version(client: TestClient, test_project: ProjectTable):
    """Test getting nonexistent version returns 404."""
    version_uuid = UUID("123e4567-e89b-12d3-a456-426614174000")
    response = client.get(f"/projects/{test_project.uuid}/versions/{version_uuid}")
    assert response.status_code == 404
