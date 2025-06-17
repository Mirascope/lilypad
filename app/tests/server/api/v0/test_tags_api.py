"""Tests for tags API."""

from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.server.models import ProjectTable, TagTable


class TestTagsAPI:
    """Test tags API endpoints."""

    @pytest.fixture
    def test_tag(self, session: Session, test_project: ProjectTable) -> TagTable:
        """Create a test tag."""
        tag = TagTable(
            name="test-tag",
            project_uuid=test_project.uuid,
            organization_uuid=test_project.organization_uuid,
        )
        session.add(tag)
        session.commit()
        session.refresh(tag)
        return tag

    def test_get_tags_empty(self, client: TestClient):
        """Test getting tags when none exist."""
        response = client.get("/tags")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_get_tags_with_data(self, client: TestClient, test_tag: TagTable):
        """Test getting tags with existing data."""
        response = client.get("/tags")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        # Find our test tag
        found = False
        for tag in data:
            if tag["uuid"] == str(test_tag.uuid):
                found = True
                assert tag["name"] == "test-tag"
                assert tag["project_uuid"] == str(test_tag.project_uuid)
                break
        assert found

    def test_get_tags_by_project(
        self, client: TestClient, test_project: ProjectTable, test_tag: TagTable
    ):
        """Test getting tags by project UUID."""
        response = client.get(f"/projects/{test_project.uuid}/tags")
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["name"] == "test-tag"
        assert data[0]["project_uuid"] == str(test_project.uuid)

    def test_get_tags_by_project_empty(
        self, client: TestClient, test_project: ProjectTable, session: Session
    ):
        """Test getting tags by project when none exist for that project."""
        # Create another project without tags
        new_project = ProjectTable(
            name="project-without-tags",
            organization_uuid=test_project.organization_uuid,
        )
        session.add(new_project)
        session.commit()
        session.refresh(new_project)

        response = client.get(f"/projects/{new_project.uuid}/tags")
        assert response.status_code == 200
        data = response.json()
        assert data == []

    def test_get_tag_by_uuid(self, client: TestClient, test_tag: TagTable):
        """Test getting a specific tag by UUID."""
        response = client.get(f"/tags/{test_tag.uuid}")
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == str(test_tag.uuid)
        assert data["name"] == "test-tag"

    def test_get_tag_not_found(self, client: TestClient):
        """Test getting a tag with invalid UUID."""
        fake_uuid = uuid4()
        response = client.get(f"/tags/{fake_uuid}")
        assert response.status_code == 404

    def test_create_tag(self, client: TestClient, test_project: ProjectTable):
        """Test creating a new tag."""
        tag_data = {
            "name": "new-tag",
            "project_uuid": str(test_project.uuid),
        }
        response = client.post("/tags", json=tag_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "new-tag"
        assert data["project_uuid"] == str(test_project.uuid)
        assert "uuid" in data
        assert "created_at" in data

    def test_create_tag_without_project(self, client: TestClient):
        """Test creating a tag without project UUID."""
        tag_data = {
            "name": "org-level-tag",
        }
        response = client.post("/tags", json=tag_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "org-level-tag"
        assert data["project_uuid"] is None

    def test_create_tag_with_validation_error(self, client: TestClient):
        """Test creating a tag with validation error."""
        # Empty name should fail validation
        tag_data = {
            "name": "",  # Empty name not allowed
        }
        response = client.post("/tags", json=tag_data)
        assert response.status_code == 422  # Validation error

    def test_update_tag(self, client: TestClient, test_tag: TagTable):
        """Test updating a tag."""
        update_data = {
            "name": "updated-tag",
        }
        response = client.patch(f"/tags/{test_tag.uuid}", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "updated-tag"
        assert data["uuid"] == str(test_tag.uuid)

    def test_update_tag_not_found(self, client: TestClient):
        """Test updating a non-existent tag."""
        fake_uuid = uuid4()
        update_data = {"name": "updated-tag"}
        response = client.patch(f"/tags/{fake_uuid}", json=update_data)
        assert response.status_code == 404

    def test_delete_tag(
        self, client: TestClient, session: Session, test_project: ProjectTable
    ):
        """Test deleting a tag."""
        # Create a tag to delete
        tag_to_delete = TagTable(
            name="to-delete",
            project_uuid=test_project.uuid,
            organization_uuid=test_project.organization_uuid,
        )
        session.add(tag_to_delete)
        session.commit()
        session.refresh(tag_to_delete)

        response = client.delete(f"/tags/{tag_to_delete.uuid}")
        assert response.status_code == 200
        assert response.json() is True

        # Verify it's deleted
        response = client.get(f"/tags/{tag_to_delete.uuid}")
        assert response.status_code == 404

    def test_delete_tag_not_found(self, client: TestClient):
        """Test deleting a non-existent tag."""
        fake_uuid = uuid4()
        response = client.delete(f"/tags/{fake_uuid}")
        assert response.status_code == 404
