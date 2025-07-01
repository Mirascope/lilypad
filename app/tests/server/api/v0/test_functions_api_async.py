"""Async tests for the functions API."""

from unittest.mock import MagicMock

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from lilypad.server.models import FunctionTable, ProjectTable
from lilypad.server.models.environments import EnvironmentTable
from lilypad.server.services import get_opensearch_service
from lilypad.server.services.opensearch import OpenSearchService
from tests.async_test_utils import AsyncDatabaseTestMixin, AsyncTestFactory


class TestFunctionsAPIAsync(AsyncDatabaseTestMixin):
    """Test functions API endpoints asynchronously."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_function_by_version(
        self,
        async_client: AsyncClient,
        async_test_project: ProjectTable,
        async_test_function: FunctionTable,
    ):
        """Test getting function by version."""
        response = await async_client.get(
            f"/projects/{async_test_project.uuid}/functions/name/{async_test_function.name}/version/{async_test_function.version_num}"
        )

        assert response.status_code == 200
        assert response.json()["name"] == async_test_function.name
        assert response.json()["version_num"] == async_test_function.version_num

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_functions_by_name(
        self,
        async_client: AsyncClient,
        async_test_project: ProjectTable,
        async_test_function: FunctionTable,
    ):
        """Test getting functions by name."""
        response = await async_client.get(
            f"/projects/{async_test_project.uuid}/functions/name/{async_test_function.name}"
        )

        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == async_test_function.name

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_deployed_function_by_names_no_deployment(
        self,
        async_client: AsyncClient,
        async_test_project: ProjectTable,
        async_test_function: FunctionTable,
        async_test_environment: EnvironmentTable,
    ):
        """Test getting deployed function falls back to latest when not deployed."""
        from lilypad.server._utils.environment import get_current_environment
        from lilypad.server.api.v0.main import api

        # Override the environment dependency directly
        api.dependency_overrides[get_current_environment] = (
            lambda: async_test_environment
        )

        try:
            response = await async_client.get(
                f"/projects/{async_test_project.uuid}/functions/name/{async_test_function.name}/environments"
            )

            # Should return the latest function as fallback
            assert response.status_code == 200
            assert response.json()["name"] == async_test_function.name
        finally:
            # Clean up override
            api.dependency_overrides.pop(get_current_environment, None)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_deployed_function_by_names_not_found(
        self,
        async_client: AsyncClient,
        async_test_project: ProjectTable,
        async_test_environment: EnvironmentTable,
    ):
        """Test getting deployed function returns 404 when function doesn't exist."""
        from lilypad.server._utils.environment import get_current_environment
        from lilypad.server.api.v0.main import api

        # Override the environment dependency directly
        api.dependency_overrides[get_current_environment] = (
            lambda: async_test_environment
        )

        try:
            response = await async_client.get(
                f"/projects/{async_test_project.uuid}/functions/name/nonexistent_function/environments"
            )

            assert response.status_code == 404
        finally:
            # Clean up override
            api.dependency_overrides.pop(get_current_environment, None)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_function(
        self, async_client: AsyncClient, async_test_project: ProjectTable
    ):
        """Test creating a new function."""
        function_data = {
            "name": "new_function",
            "signature": "def new_function(x: int) -> int:",
            "code": "def new_function(x: int) -> int:\n    return x * 2",
            "arg_types": {"x": "int"},
        }

        response = await async_client.post(
            f"/projects/{async_test_project.uuid}/functions/run", json=function_data
        )

        assert response.status_code == 200
        assert response.json()["name"] == "new_function"
        assert response.json()["version_num"] == 1

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_function_new_version(
        self,
        async_client: AsyncClient,
        async_test_project: ProjectTable,
        async_test_function: FunctionTable,
    ):
        """Test creating a new version of existing function."""
        function_data = {
            "name": async_test_function.name,
            "signature": "def async_test_function() -> str:",
            "code": "def async_test_function() -> str:\n    return 'updated'",
            "arg_types": {},
        }

        response = await async_client.post(
            f"/projects/{async_test_project.uuid}/functions/run", json=function_data
        )

        assert response.status_code == 200
        assert response.json()["name"] == async_test_function.name
        assert (
            response.json()["version_num"] == (async_test_function.version_num or 0) + 1
        )

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_search_functions_with_opensearch(
        self,
        async_client: AsyncClient,
        async_test_project: ProjectTable,
        async_test_function: FunctionTable,
        monkeypatch,
    ):
        """Test searching functions with OpenSearch integration."""
        from lilypad.server.api.v0.main import api

        # Mock OpenSearch service
        mock_opensearch = MagicMock(spec=OpenSearchService)
        mock_opensearch.search_functions.return_value = [async_test_function]

        api.dependency_overrides[get_opensearch_service] = lambda: mock_opensearch

        try:
            response = await async_client.get(
                f"/projects/{async_test_project.uuid}/functions/search",
                params={"query": "test"},
            )

            assert response.status_code == 200
            assert len(response.json()) == 1
            assert response.json()[0]["name"] == async_test_function.name

            # Verify OpenSearch was called
            mock_opensearch.search_functions.assert_called_once()
        finally:
            api.dependency_overrides.pop(get_opensearch_service, None)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_list_functions(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
        async_test_function: FunctionTable,
    ):
        """Test listing all functions in a project."""
        # Create additional functions
        factory = AsyncTestFactory(async_session)
        for i in range(3):
            await factory.create(
                FunctionTable,
                project_uuid=async_test_project.uuid,
                name=f"additional_function_{i}",
                signature=f"def func_{i}(): pass",
                code=f"def func_{i}(): pass",
                hash=f"hash_{i}",
                arg_types={},
                organization_uuid=async_test_project.organization_uuid,
                version_num=1,
            )

        response = await async_client.get(
            f"/projects/{async_test_project.uuid}/functions"
        )

        assert response.status_code == 200
        functions = response.json()
        assert len(functions) >= 4  # async_test_function + 3 additional
        names = [f["name"] for f in functions]
        assert async_test_function.name in names

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_function_metadata(
        self,
        async_client: AsyncClient,
        async_test_project: ProjectTable,
        async_test_function: FunctionTable,
    ):
        """Test updating function metadata."""
        update_data = {
            "metadata": {
                "description": "Updated function description",
                "tags": ["test", "async"],
            }
        }

        response = await async_client.patch(
            f"/projects/{async_test_project.uuid}/functions/{async_test_function.uuid}",
            json=update_data,
        )

        assert response.status_code == 200
        assert (
            response.json()["metadata"]["description"] == "Updated function description"
        )

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_function(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
    ):
        """Test deleting a function."""
        # Create a function to delete
        factory = AsyncTestFactory(async_session)
        function_to_delete = await factory.create(
            FunctionTable,
            project_uuid=async_test_project.uuid,
            name="function_to_delete",
            signature="def delete_me(): pass",
            code="def delete_me(): pass",
            hash="delete_hash",
            arg_types={},
            organization_uuid=async_test_project.organization_uuid,
            version_num=1,
        )

        response = await async_client.delete(
            f"/projects/{async_test_project.uuid}/functions/{function_to_delete.uuid}"
        )

        assert response.status_code == 200

        # Verify it's deleted
        response = await async_client.get(
            f"/projects/{async_test_project.uuid}/functions/name/{function_to_delete.name}/version/1"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_function_versioning(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
    ):
        """Test function versioning behavior."""
        factory = AsyncTestFactory(async_session)

        # Create multiple versions of the same function
        function_name = "versioned_function"
        for version in range(1, 4):
            await factory.create(
                FunctionTable,
                project_uuid=async_test_project.uuid,
                name=function_name,
                signature=f"def {function_name}_v{version}(): pass",
                code=f"def {function_name}_v{version}(): return {version}",
                hash=f"hash_v{version}",
                arg_types={},
                organization_uuid=async_test_project.organization_uuid,
                version_num=version,
            )

        # Get all versions
        response = await async_client.get(
            f"/projects/{async_test_project.uuid}/functions/name/{function_name}"
        )

        assert response.status_code == 200
        versions = response.json()
        assert len(versions) == 3
        assert sorted([v["version_num"] for v in versions]) == [1, 2, 3]
