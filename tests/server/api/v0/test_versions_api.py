"""Tests for the versions API."""

from collections.abc import Generator

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
def test_project(session: Session) -> Generator[ProjectTable, None, None]:
    """Create a test project."""
    project = ProjectTable(name="test_project")
    session.add(project)
    session.commit()
    session.refresh(project)
    yield project


@pytest.fixture
def test_function(
    session: Session, test_project: ProjectTable
) -> Generator[FunctionTable, None, None]:
    """Create a test function."""
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
        project_id=test_project.id,
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
        version_num=1,
        project_id=test_project.id,
        function_id=test_function.id,
        prompt_id=test_prompt.id,
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

    response = client.post(f"/projects/{test_project.id}/versions", json=data)
    assert response.status_code == 200
    created = response.json()
    assert created["function_name"] == "test_function"
    assert created["version_num"] == 1
    assert created["is_active"] is True
    assert created["prompt"]["call_params"] is not None


def test_get_version(client: TestClient, test_version: VersionTable):
    """Test getting version by ID returns expected version."""
    response = client.get(
        f"/projects/{test_version.project_id}/versions/{test_version.id}"
    )
    assert response.status_code == 200
    version = response.json()
    assert version["function_name"] == test_version.function_name
    assert version["prompt"]["call_params"] is not None
    assert version["prompt"]["call_params"]["max_tokens"] == 100


def test_get_versions_by_function(client: TestClient, test_version: VersionTable):
    """Test getting versions for a function returns expected versions."""
    response = client.get(
        f"/projects/{test_version.project_id}/functions/{test_version.function_name}/versions"
    )
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) == 1
    assert versions[0]["function_name"] == test_version.function_name
    assert versions[0]["prompt"]["call_params"] is not None
    assert versions[0]["prompt"]["call_params"]["max_tokens"] == 100


def test_get_nonexistent_version(client: TestClient, test_project: ProjectTable):
    """Test getting nonexistent version returns 404."""
    response = client.get(f"/projects/{test_project.id}/versions/999")
    assert response.status_code == 404
