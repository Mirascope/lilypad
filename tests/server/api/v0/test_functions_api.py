"""Tests for the functions API."""

from fastapi.testclient import TestClient

from lilypad.server.models import FunctionTable, ProjectTable, UserTable


def test_get_empty_function_names(
    client: TestClient, test_user: UserTable, test_project: ProjectTable
):
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
