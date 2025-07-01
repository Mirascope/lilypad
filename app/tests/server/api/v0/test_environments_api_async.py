"""Async tests for environments and deployments API."""

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from lilypad.server.models import (
    DeploymentTable,
    EnvironmentTable,
    FunctionTable,
    ProjectTable,
)
from tests.async_test_utils import AsyncDatabaseTestMixin, AsyncTestFactory


class TestEnvironmentsAPIAsync(AsyncDatabaseTestMixin):
    """Test environments API endpoints asynchronously."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_environments_empty(
        self, async_client: AsyncClient, async_test_environment: EnvironmentTable
    ):
        """Test getting environments with default test environment."""
        response = await async_client.get("/environments")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # There's already a async_test_environment fixture that creates one
        assert len(data) == 1
        assert data[0]["name"] == async_test_environment.name

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_environments_with_data(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
    ):
        """Test getting environments with multiple environments."""
        # Add additional environment
        factory = AsyncTestFactory(async_session)
        await factory.create(
            EnvironmentTable,
            name="production",
            organization_uuid=async_test_project.organization_uuid,
        )

        response = await async_client.get("/environments")
        assert response.status_code == 200
        data = response.json()
        # Should have async_test_environment from fixture + production
        assert len(data) >= 1
        names = [env["name"] for env in data]
        assert "production" in names

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_environment(self, async_client: AsyncClient):
        """Test creating a new environment."""
        environment_data = {
            "name": "staging",
            "description": "Staging environment",
        }
        response = await async_client.post("/environments", json=environment_data)
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "staging"
        assert data["description"] == "Staging environment"
        assert "uuid" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_environment_by_uuid(
        self, async_client: AsyncClient, async_test_environment: EnvironmentTable
    ):
        """Test getting environment by UUID."""
        response = await async_client.get(
            f"/environments/{async_test_environment.uuid}"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == str(async_test_environment.uuid)
        assert data["name"] == async_test_environment.name

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_environment_not_found(self, async_client: AsyncClient):
        """Test getting environment with invalid UUID."""
        fake_uuid = uuid4()
        response = await async_client.get(f"/environments/{fake_uuid}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_environment(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
    ):
        """Test deleting an environment."""
        # Create environment to delete
        factory = AsyncTestFactory(async_session)
        env_to_delete = await factory.create(
            EnvironmentTable,
            name="to_delete",
            organization_uuid=async_test_project.organization_uuid,
        )

        response = await async_client.delete(f"/environments/{env_to_delete.uuid}")
        assert response.status_code == 200
        assert response.json() is True

        # Verify it's deleted
        response = await async_client.get(f"/environments/{env_to_delete.uuid}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_environment_not_found(self, async_client: AsyncClient):
        """Test deleting non-existent environment."""
        fake_uuid = uuid4()
        response = await async_client.delete(f"/environments/{fake_uuid}")
        assert response.status_code == 404


class TestDeploymentsAPIAsync(AsyncDatabaseTestMixin):
    """Test deployment API endpoints asynchronously."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_deploy_function(
        self,
        async_client: AsyncClient,
        async_test_project: ProjectTable,
        async_test_environment: EnvironmentTable,
        async_test_function: FunctionTable,
    ):
        """Test deploying a function to an environment."""
        response = await async_client.post(
            f"/projects/{async_test_project.uuid}/environments/{async_test_environment.uuid}/deploy",
            params={
                "function_uuid": str(async_test_function.uuid),
                "notes": "Initial deployment",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["environment_uuid"] == str(async_test_environment.uuid)
        assert data["function_uuid"] == str(async_test_function.uuid)
        assert data["is_active"] is True
        assert data["notes"] == "Initial deployment"
        assert data["version_num"] == 1

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_deploy_function_without_notes(
        self,
        async_client: AsyncClient,
        async_test_project: ProjectTable,
        async_test_environment: EnvironmentTable,
        async_test_function: FunctionTable,
    ):
        """Test deploying a function without notes."""
        response = await async_client.post(
            f"/projects/{async_test_project.uuid}/environments/{async_test_environment.uuid}/deploy",
            params={"function_uuid": str(async_test_function.uuid)},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["notes"] is None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_deploy_function_project_not_found(
        self,
        async_client: AsyncClient,
        async_test_environment: EnvironmentTable,
        async_test_function: FunctionTable,
    ):
        """Test deploying with non-existent project."""
        fake_uuid = uuid4()
        response = await async_client.post(
            f"/projects/{fake_uuid}/environments/{async_test_environment.uuid}/deploy",
            params={"function_uuid": str(async_test_function.uuid)},
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_active_deployment(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
        async_test_environment: EnvironmentTable,
        async_test_function: FunctionTable,
    ):
        """Test getting active deployment for an environment."""
        # First deploy a function
        factory = AsyncTestFactory(async_session)
        deployment = await factory.create(
            DeploymentTable,
            environment_uuid=async_test_environment.uuid,
            function_uuid=async_test_function.uuid,
            version_num=1,
            is_active=True,
            organization_uuid=async_test_project.organization_uuid,
        )

        response = await async_client.get(
            f"/projects/{async_test_project.uuid}/environments/{async_test_environment.uuid}/active-deployment"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["uuid"] == str(deployment.uuid)
        assert data["is_active"] is True

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_list_deployments(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
        async_test_environment: EnvironmentTable,
        async_test_function: FunctionTable,
    ):
        """Test listing deployments for an environment."""
        # Create multiple deployments
        factory = AsyncTestFactory(async_session)
        deployments = await factory.create_batch(
            DeploymentTable,
            count=3,
            environment_uuid=async_test_environment.uuid,
            function_uuid=async_test_function.uuid,
            version_num=1,
            is_active=False,
            organization_uuid=async_test_project.organization_uuid,
        )

        # Make one active
        deployments[0].is_active = True
        await async_session.flush()

        response = await async_client.get(
            f"/projects/{async_test_project.uuid}/environments/{async_test_environment.uuid}/deployments"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 3

        # Verify one is active
        active_deployments = [d for d in data if d["is_active"]]
        assert len(active_deployments) == 1
