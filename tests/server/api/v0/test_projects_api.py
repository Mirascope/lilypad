"""Tests for the projects API."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.server.models import ProjectTable


def test_get_empty_projects(client: TestClient):
    """Test getting projects when no projects exist."""
    response = client.get("/projects")
    assert response.status_code == 200
    assert response.json() == []


def test_get_projects(client: TestClient, test_project: ProjectTable):
    """Test getting project list returns expected project."""
    response = client.get("/projects")
    assert response.status_code == 200
    projects = response.json()
    assert len(projects) == 1
    assert projects[0]["name"] == test_project.name


def test_get_project(client: TestClient, test_project: ProjectTable):
    """Test getting single project returns expected project."""
    response = client.get(f"/projects/{test_project.id}")
    assert response.status_code == 200
    assert response.json()["name"] == test_project.name


def test_create_project(client: TestClient, session: Session):
    """Test project creation works correctly."""
    project_data = {"name": "new_project"}
    response = client.post("/projects/", json=project_data)
    assert response.status_code == 200
    created_project = response.json()
    assert created_project["name"] == "new_project"
    assert created_project["id"] is not None

    # Verify in database
    db_project = session.get(ProjectTable, created_project["id"])
    assert db_project is not None
    assert db_project.name == "new_project"


def test_delete_project(
    client: TestClient, test_project: ProjectTable, session: Session
):
    """Test project deletion removes the project."""
    response = client.delete(f"/projects/{test_project.id}")
    assert response.status_code == 200

    response = client.get(f"/projects/{test_project.id}")
    assert response.status_code == 404

    # Verify in database
    db_project = session.get(ProjectTable, test_project.id)
    assert db_project is None


def test_get_nonexistent_project(client: TestClient):
    """Test getting nonexistent project returns 404."""
    response = client.get("/projects/999")
    assert response.status_code == 404
