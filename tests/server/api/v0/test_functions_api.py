"""Tests for the functions API."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.server.models import FunctionTable, ProjectTable


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


def test_get_empty_function_names(client: TestClient, test_project: ProjectTable):
    """Test getting function names when no functions exist."""
    response = client.get(f"/projects/{test_project.id}/functions/names")
    assert response.status_code == 200
    assert response.json() == []


def test_get_function_names(
    client: TestClient, test_project: ProjectTable, test_function: FunctionTable
):
    """Test getting function names returns expected names."""
    response = client.get(f"/projects/{test_project.id}/functions/names")
    assert response.status_code == 200
    names = response.json()
    assert len(names) == 1
    assert names[0] == test_function.name
