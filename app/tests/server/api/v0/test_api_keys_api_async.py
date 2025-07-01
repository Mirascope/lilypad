"""Async tests for the API keys endpoints."""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select

from lilypad.server.models import (
    APIKeyTable,
    EnvironmentTable,
    ProjectTable,
    UserTable,
)
from tests.async_test_utils import (
    AsyncDatabaseTestMixin,
    AsyncTestFactory,
)


class TestAPIKeysAsync(AsyncDatabaseTestMixin):
    """Async tests for API Keys endpoints."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_list_api_keys_empty(self, async_client: AsyncClient):
        """Test listing API keys when none exist."""
        response = await async_client.get("/api-keys")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_list_api_keys(
        self, async_client: AsyncClient, async_test_api_key: APIKeyTable
    ):
        """Test listing API keys returns expected keys."""
        response = await async_client.get("/api-keys")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == async_test_api_key.name
        assert data[0]["uuid"] == str(async_test_api_key.uuid)
        # Key hash should not be exposed
        assert "key_hash" not in data[0]
        assert "key" not in data[0]

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_list_api_keys_multiple(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
        async_test_environment: EnvironmentTable,
        async_test_user: UserTable,
    ):
        """Test listing multiple API keys."""
        # Type guards
        assert async_test_user.uuid is not None
        assert async_test_project.uuid is not None
        assert async_test_environment.uuid is not None

        # Create additional API keys
        factory = AsyncTestFactory(async_session)
        for i in range(3):
            await factory.create(
                APIKeyTable,
                key_hash=f"test_key_{i}",
                user_uuid=async_test_user.uuid,
                organization_uuid=async_test_project.organization_uuid,
                name=f"Test Key {i}",
                project_uuid=async_test_project.uuid,
                environment_uuid=async_test_environment.uuid,
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            )

        response = await async_client.get("/api-keys")
        assert response.status_code == 200

        data = response.json()
        assert len(data) == 3  # Only the 3 created in this test

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_api_key(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
        async_test_environment: EnvironmentTable,
    ):
        """Test creating a new API key."""
        api_key_data = {
            "name": "New API Key",
            "project_uuid": str(async_test_project.uuid),
            "environment_uuid": str(async_test_environment.uuid),
            "description": "Test API key for automated tests",
        }

        response = await async_client.post("/api-keys", json=api_key_data)
        assert response.status_code == 200

        # The API returns the raw key as a string
        raw_key = response.text.strip('"')  # Remove quotes from JSON string
        assert raw_key  # Should have received a key

        # Verify in database
        stmt = select(APIKeyTable).where(
            APIKeyTable.name == "New API Key",
            APIKeyTable.project_uuid == async_test_project.uuid,
        )
        result = await async_session.execute(stmt)
        created_keys = result.scalars().all()
        assert len(created_keys) == 1

        db_key = created_keys[0]
        assert db_key.name == "New API Key"
        assert db_key.project_uuid == async_test_project.uuid
        assert db_key.environment_uuid == async_test_environment.uuid
        # The key_hash in DB should be the same as what was returned
        assert db_key.key_hash == raw_key

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_api_key_with_expiration(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
        async_test_environment: EnvironmentTable,
    ):
        """Test creating an API key with custom expiration."""
        expiration_date = datetime.now(timezone.utc) + timedelta(days=30)
        api_key_data = {
            "name": "Expiring API Key",
            "project_uuid": str(async_test_project.uuid),
            "environment_uuid": str(async_test_environment.uuid),
            "expires_at": expiration_date.isoformat(),
        }

        response = await async_client.post("/api-keys", json=api_key_data)
        assert response.status_code == 200

        # Verify in database
        stmt = select(APIKeyTable).where(APIKeyTable.name == "Expiring API Key")
        result = await async_session.execute(stmt)
        db_key = result.scalar_one()
        assert db_key.expires_at is not None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_api_key(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
        async_test_environment: EnvironmentTable,
        async_test_user: UserTable,
    ):
        """Test deleting an API key."""
        # Create an API key to delete
        factory = AsyncTestFactory(async_session)
        api_key_to_delete = await factory.create(
            APIKeyTable,
            key_hash="to_delete",
            user_uuid=async_test_user.uuid,
            organization_uuid=async_test_project.organization_uuid,
            name="Key to Delete",
            project_uuid=async_test_project.uuid,
            environment_uuid=async_test_environment.uuid,
        )

        response = await async_client.delete(f"/api-keys/{api_key_to_delete.uuid}")
        assert response.status_code == 200

        # Verify it's deleted
        await self.assert_not_exists(
            async_session, APIKeyTable, uuid=api_key_to_delete.uuid
        )

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_api_key_not_found(self, async_client: AsyncClient):
        """Test deleting a non-existent API key."""
        fake_uuid = uuid4()
        response = await async_client.delete(f"/api-keys/{fake_uuid}")
        assert response.status_code == 404

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_api_key_from_another_org(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_project: ProjectTable,
        async_test_environment: EnvironmentTable,
    ):
        """Test that users cannot delete API keys from other organizations."""
        # Create an API key in a different organization
        factory = AsyncTestFactory(async_session)
        other_org = await factory.create(
            type(async_test_project).__bases__[0],  # OrganizationTable
            name="Other Org",
        )

        other_user = await factory.create(
            UserTable,
            email="other@example.com",
            first_name="Other",
            last_name="User",
            active_organization_uuid=other_org.uuid,
        )

        other_api_key = await factory.create(
            APIKeyTable,
            key_hash="other_key",
            user_uuid=other_user.uuid,
            organization_uuid=other_org.uuid,
            name="Other Org Key",
            project_uuid=async_test_project.uuid,  # This might need adjustment based on business logic
            environment_uuid=async_test_environment.uuid,
        )

        # Try to delete it with our user's credentials
        response = await async_client.delete(f"/api-keys/{other_api_key.uuid}")
        assert response.status_code == 404  # Should not be able to see/delete it
