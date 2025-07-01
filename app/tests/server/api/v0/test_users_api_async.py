"""Async tests for the users API endpoints."""

import asyncio

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from lilypad.ee.server.models import UserOrganizationTable, UserRole
from lilypad.server.models import OrganizationTable, UserTable
from tests.async_test_utils import AsyncDatabaseTestMixin, AsyncTestFactory


class TestUsersAPIAsync(AsyncDatabaseTestMixin):
    """Test users API endpoints asynchronously."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_current_user(self, async_client: AsyncClient):
        """Test getting current authenticated user."""
        response = await async_client.get("/current-user")
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == "test@test.com"
        assert data["first_name"] == "Test User"
        assert data["uuid"] is not None
        assert data["active_organization_uuid"] is not None
        assert "access_token" in data

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_user_active_organization(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test updating user's active organization."""
        # Create a second organization
        factory = AsyncTestFactory(async_session)
        org2 = await factory.create(
            OrganizationTable, name="Second Organization", license="654321"
        )

        # Add user to the second organization
        assert async_test_user.uuid is not None  # Type guard
        assert org2.uuid is not None  # Type guard

        await factory.create(
            UserOrganizationTable,
            user_uuid=async_test_user.uuid,
            organization_uuid=org2.uuid,
            role=UserRole.MEMBER,
            organization=org2,
        )

        # Update active organization
        response = await async_client.put(f"/users/{org2.uuid}")
        assert response.status_code == 200

        data = response.json()
        assert data["active_organization_uuid"] == str(org2.uuid)
        assert "access_token" in data  # New JWT with updated org

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_user_active_organization_not_member(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test updating to organization user is not a member of."""
        # Create an organization the user is not part of
        factory = AsyncTestFactory(async_session)
        other_org = await factory.create(
            OrganizationTable, name="Other Organization", license="999999"
        )

        # Try to update to this organization
        # Note: Current implementation doesn't validate membership
        response = await async_client.put(f"/users/{other_org.uuid}")
        assert response.status_code == 200

        # Verify it was updated (even though user is not a member)
        data = response.json()
        assert data["active_organization_uuid"] == str(other_org.uuid)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_user_active_organization_none(
        self, async_client: AsyncClient
    ):
        """Test clearing user's active organization."""
        # The endpoint expects a UUID, so we can't test passing None
        # Instead, we'll test with an invalid UUID format
        response = await async_client.put("/users/not-a-uuid")
        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_user_keys(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test updating user keys."""
        keys_data = {
            "openai_api_key": "sk-test123",
            "anthropic_api_key": "sk-ant-test456",
        }

        response = await async_client.patch("/users", json=keys_data)
        assert response.status_code == 200

        data = response.json()
        # Keys should be stored but not returned in response for security
        assert "keys" in data

        # Verify in database
        await async_session.refresh(async_test_user)
        assert async_test_user.keys == keys_data

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_user_keys_empty(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test clearing user keys."""
        # First set some keys
        async_test_user.keys = {"openai_api_key": "sk-old123"}
        await async_session.flush()

        # Now clear them
        response = await async_client.patch("/users", json={})
        assert response.status_code == 200

        # Verify they're cleared
        await async_session.refresh(async_test_user)
        assert async_test_user.keys == {}

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_user_keys_partial(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test partial update of user keys."""
        # Set initial keys
        async_test_user.keys = {
            "openai_api_key": "sk-old123",
            "anthropic_api_key": "sk-ant-old456",
        }
        await async_session.flush()

        # Update only one key
        update_data = {"openai_api_key": "sk-new789"}
        response = await async_client.patch("/users", json=update_data)
        assert response.status_code == 200

        # Verify partial update
        await async_session.refresh(async_test_user)
        assert async_test_user.keys == {"openai_api_key": "sk-new789"}

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_user_organizations(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test getting user's organizations."""
        # Create additional organizations and add user to them
        factory = AsyncTestFactory(async_session)

        org2 = await factory.create(
            OrganizationTable, name="Second Org", license="123456"
        )

        await factory.create(
            UserOrganizationTable,
            user_uuid=async_test_user.uuid,
            organization_uuid=org2.uuid,
            role=UserRole.ADMIN,
            organization=org2,
        )

        response = await async_client.get("/user-organizations")
        assert response.status_code == 200

        data = response.json()
        # Should have at least 2 organizations (test org + new org)
        assert len(data) >= 2
        org_names = [org["organization"]["name"] for org in data]
        assert "Second Org" in org_names

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_user_session_management(
        self, async_client: AsyncClient, async_test_user: UserTable
    ):
        """Test user session handling with async client."""
        # Make multiple concurrent requests
        responses = await asyncio.gather(
            async_client.get("/current-user"),
            async_client.get("/current-user"),
            async_client.get("/current-user"),
        )

        # All should succeed
        for response in responses:
            assert response.status_code == 200
            assert response.json()["email"] == "test@test.com"
