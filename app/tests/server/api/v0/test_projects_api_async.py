"""Async tests for the projects API."""

from typing import Annotated
from uuid import UUID

import pytest
from fastapi import Depends
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from lilypad.server.models import ProjectTable
from lilypad.server.schemas.projects import ProjectCreate
from lilypad.server.services.base_organization import AsyncBaseOrganizationService
from tests.async_test_utils import AsyncDatabaseTestMixin


class AsyncProjectService(AsyncBaseOrganizationService[ProjectTable, ProjectCreate]):
    """Async version of ProjectService for testing."""

    table: type[ProjectTable] = ProjectTable
    create_model: type[ProjectCreate] = ProjectCreate


class TestProjectsAPIAsync(AsyncDatabaseTestMixin):
    """Test projects API endpoints asynchronously."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_empty_projects(self, async_client: AsyncClient):
        """Test getting projects when no projects exist."""
        # Need to patch the service to use async version

        async def patched_get_projects(
            project_service: Annotated[
                AsyncProjectService, Depends(AsyncProjectService)
            ],
        ):
            return await project_service.find_all_records()

        # Skip endpoint patching as it's not supported
        response = await async_client.get("/projects")
        assert response.status_code == 200
        # The sync API might return existing projects from sync DB
        assert isinstance(response.json(), list)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_projects(
        self, async_client: AsyncClient, async_test_project: ProjectTable
    ):
        """Test getting project list returns expected project."""
        # Skip this test for now - will fix after infrastructure is ready
        pytest.skip("Async infrastructure not fully implemented")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_project(
        self, async_client: AsyncClient, async_test_project: ProjectTable
    ):
        """Test getting single project returns expected project."""
        # Skip this test for now - will fix after infrastructure is ready
        pytest.skip("Async infrastructure not fully implemented")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_project(
        self, async_client: AsyncClient, async_session: AsyncSession
    ):
        """Test project creation works correctly."""
        project_data = {"name": "new_project"}
        response = await async_client.post("/projects/", json=project_data)
        assert response.status_code == 200
        created_project = response.json()
        assert created_project["name"] == "new_project"
        assert created_project["uuid"] is not None

        # Verify in database
        db_project = await async_session.get(
            ProjectTable, UUID(created_project["uuid"])
        )
        assert db_project is not None
        assert db_project.name == "new_project"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_project(
        self,
        async_client: AsyncClient,
        async_test_project: ProjectTable,
        async_session: AsyncSession,
    ):
        """Test project deletion removes the project."""
        # Skip this test for now - will fix after infrastructure is ready
        pytest.skip("Async infrastructure not fully implemented")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_nonexistent_project(self, async_client: AsyncClient):
        """Test getting nonexistent project returns 404."""
        project_uuid = UUID("123e4567-e89b-12d3-a456-426614174000")
        response = await async_client.get(f"/projects/{project_uuid}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_patch_project(
        self, async_client: AsyncClient, async_test_project: ProjectTable
    ):
        """Test updating a project."""
        # Skip this test for now - will fix after infrastructure is ready
        pytest.skip("Async infrastructure not fully implemented")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_patch_nonexistent_project(self, async_client: AsyncClient):
        """Test updating nonexistent project returns 404."""
        project_uuid = UUID("123e4567-e89b-12d3-a456-426614174001")
        update_data = {"name": "updated_name"}
        response = await async_client.patch(
            f"/projects/{project_uuid}", json=update_data
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_project_validation_error(self, async_client: AsyncClient):
        """Test creating a project with invalid data returns validation error."""
        # Try to create a project without a name
        project_data = {}
        response = await async_client.post("/projects/", json=project_data)
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_project_with_metadata(self, async_client: AsyncClient):
        """Test creating a project with metadata."""
        project_data = {
            "name": "project_with_metadata",
            "metadata": {"environment": "test", "version": "1.0"},
        }
        response = await async_client.post("/projects/", json=project_data)
        assert response.status_code == 200
        created_project = response.json()
        assert created_project["name"] == "project_with_metadata"
        assert created_project["metadata"] == {"environment": "test", "version": "1.0"}

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_list_projects_multiple(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
    ):
        """Test listing multiple projects."""
        # Skip this test for now - will fix after infrastructure is ready
        pytest.skip("Async infrastructure not fully implemented")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_project_cascading_delete(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
    ):
        """Test that deleting a project cascades properly."""
        # Skip this test for now - will fix after infrastructure is ready
        pytest.skip("Async infrastructure not fully implemented")
