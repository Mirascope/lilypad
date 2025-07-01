"""Async tests for the organizations API endpoints."""

# pyright: reportArgumentType=false
# SQLAlchemy's where() and and_() have complex type annotations that pyright
# struggles with. These tests are skipped pending Task 3 async migration.

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from lilypad.ee.server.models import UserOrganizationTable, UserRole
from lilypad.server.models import BillingTable, OrganizationTable, UserTable
from tests.async_test_utils import AsyncDatabaseTestMixin, AsyncTestFactory


class TestOrganizationsAPIAsync(AsyncDatabaseTestMixin):
    """Test organizations API endpoints asynchronously."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_organization(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test creating a new organization."""
        org_data = {"name": "New Organization"}

        response = await async_client.post("/organizations", json=org_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "New Organization"
        assert data["uuid"] is not None

        # Verify in database
        result = await async_session.execute(
            select(OrganizationTable).where(
                OrganizationTable.uuid == UUID(data["uuid"])
            )
        )
        db_org = result.scalar_one_or_none()
        assert db_org is not None
        assert db_org.name == "New Organization"

        # Verify user is added as OWNER
        result = await async_session.execute(
            select(UserOrganizationTable).where(
                UserOrganizationTable.organization_uuid == db_org.uuid
            )
        )
        user_org = result.scalar_one_or_none()
        assert user_org is not None
        assert user_org.role == UserRole.OWNER

        # Verify user's active org was updated
        await async_session.refresh(async_test_user)
        assert async_test_user.active_organization_uuid == db_org.uuid

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_organization_duplicate_name(self, async_client: AsyncClient):
        """Test creating organization with duplicate name fails."""
        # First organization already exists from fixtures
        org_data = {
            "name": "Test Organization"  # Same as fixture
        }

        response = await async_client.post("/organizations", json=org_data)
        assert response.status_code == 409
        detail = response.json().get("detail", "")
        assert "already exists" in detail.lower()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_organization_invalid_data(self, async_client: AsyncClient):
        """Test creating organization with invalid data."""
        # Missing required field
        org_data = {}

        response = await async_client.post("/organizations", json=org_data)
        assert response.status_code == 422

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_organization(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test updating an organization."""
        # Type guard
        assert async_test_user.uuid is not None

        # Change user role to OWNER
        result = await async_session.execute(
            select(UserOrganizationTable).where(
                and_(
                    UserOrganizationTable.user_uuid == async_test_user.uuid,
                    UserOrganizationTable.organization_uuid
                    == UUID("12345678-1234-1234-1234-123456789abc"),
                )
            )
        )
        user_org = result.scalar_one_or_none()
        assert user_org is not None
        user_org.role = UserRole.OWNER
        await async_session.commit()

        update_data = {"name": "Updated Organization Name"}

        response = await async_client.patch("/organizations", json=update_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Updated Organization Name"

        # Verify in database
        org_uuid = UUID("12345678-1234-1234-1234-123456789abc")
        result = await async_session.execute(
            select(OrganizationTable).where(OrganizationTable.uuid == org_uuid)
        )
        db_org = result.scalar_one_or_none()
        assert db_org is not None
        assert db_org.name == "Updated Organization Name"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_organization_not_owner(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test that non-owner users cannot update organization."""
        # Type guard
        assert async_test_user.uuid is not None

        # Change user role to MEMBER
        result = await async_session.execute(
            select(UserOrganizationTable).where(
                and_(
                    UserOrganizationTable.user_uuid == async_test_user.uuid,
                    UserOrganizationTable.organization_uuid
                    == UUID("12345678-1234-1234-1234-123456789abc"),
                )
            )
        )
        user_org = result.scalar_one_or_none()
        assert user_org is not None
        user_org.role = UserRole.MEMBER
        await async_session.commit()

        update_data = {"name": "Should Not Update"}
        response = await async_client.patch("/organizations", json=update_data)

        assert response.status_code == 403
        detail = response.json().get("detail", "")
        assert "owner" in detail.lower()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_organization_no_active_org(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test updating when user has no active organization."""
        # Clear user's active organization
        async_test_user.active_organization_uuid = None
        await async_session.commit()

        update_data = {"name": "Should Not Work"}
        response = await async_client.patch("/organizations", json=update_data)

        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "does not have an active organization" in detail

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_organization_with_license(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test updating organization with license key."""
        # Type guard
        assert async_test_user.uuid is not None

        # Change user role to OWNER
        result = await async_session.execute(
            select(UserOrganizationTable).where(
                and_(
                    UserOrganizationTable.user_uuid == async_test_user.uuid,
                    UserOrganizationTable.organization_uuid
                    == UUID("12345678-1234-1234-1234-123456789abc"),
                )
            )
        )
        user_org = result.scalar_one_or_none()
        assert user_org is not None
        user_org.role = UserRole.OWNER
        await async_session.commit()

        # Note: This will fail with invalid license in test environment
        update_data = {"license": "invalid-license-key"}

        response = await async_client.patch("/organizations", json=update_data)
        # Should fail with invalid license
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "invalid license" in detail.lower()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_organization(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test deleting an organization."""
        factory = AsyncTestFactory(async_session)

        # Create a second organization to switch to after deletion
        org2 = await factory.create(
            OrganizationTable, name="Second Org", license="license2"
        )

        # Create billing entry for the org2
        assert org2.uuid is not None
        assert async_test_user.uuid is not None  # Type guard

        await factory.create(
            BillingTable,
            organization_uuid=org2.uuid,
            stripe_customer_id="cus_test_org2",
        )

        # Add user to second org
        user_org2 = await factory.create(
            UserOrganizationTable,
            user_uuid=async_test_user.uuid,
            organization_uuid=org2.uuid,
            role=UserRole.MEMBER,
            organization=org2,
        )

        # Switch to org2 and make user owner
        async_test_user.active_organization_uuid = org2.uuid
        user_org2.role = UserRole.OWNER
        await async_session.commit()

        # Delete the active organization
        response = await async_client.delete("/organizations")
        assert response.status_code == 200

        # Response should be UserPublic with updated JWT
        data = response.json()
        assert "access_token" in data
        # User should be switched to the first org
        assert data["active_organization_uuid"] == str(
            UUID("12345678-1234-1234-1234-123456789abc")
        )

        # Verify org2 is deleted
        result = await async_session.execute(
            select(OrganizationTable).where(OrganizationTable.uuid == org2.uuid)
        )
        db_org = result.scalar_one_or_none()
        assert db_org is None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_organization_not_owner(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test that non-owner users cannot delete organization."""
        # Type guard
        assert async_test_user.uuid is not None

        # Change user role to MEMBER
        result = await async_session.execute(
            select(UserOrganizationTable).where(
                and_(
                    UserOrganizationTable.user_uuid == async_test_user.uuid,
                    UserOrganizationTable.organization_uuid
                    == UUID("12345678-1234-1234-1234-123456789abc"),
                )
            )
        )
        user_org = result.scalar_one_or_none()
        assert user_org is not None
        user_org.role = UserRole.MEMBER
        await async_session.commit()

        response = await async_client.delete("/organizations")
        assert response.status_code == 403
        detail = response.json().get("detail", "")
        assert "owner" in detail.lower()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_organization_no_active_org(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test deleting when user has no active organization."""
        # Clear user's active organization
        async_test_user.active_organization_uuid = None
        await async_session.commit()

        response = await async_client.delete("/organizations")
        assert response.status_code == 400
        detail = response.json().get("detail", "")
        assert "does not have an active organization" in detail

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_last_organization(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test deleting the last organization user belongs to."""
        # Type guard
        assert async_test_user.uuid is not None

        # Make sure user is owner
        result = await async_session.execute(
            select(UserOrganizationTable).where(
                and_(
                    UserOrganizationTable.user_uuid == async_test_user.uuid,
                    UserOrganizationTable.organization_uuid
                    == UUID("12345678-1234-1234-1234-123456789abc"),
                )
            )
        )
        user_org = result.scalar_one_or_none()
        assert user_org is not None
        user_org.role = UserRole.OWNER
        await async_session.commit()

        # Delete the only organization
        response = await async_client.delete("/organizations")
        assert response.status_code == 200

        # Response should be UserPublic with no active org
        data = response.json()
        assert "access_token" in data
        assert data["active_organization_uuid"] is None

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_organization_not_found(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test deleting organization that doesn't exist or user doesn't have access to."""
        # Type guard
        assert async_test_user.uuid is not None

        # Make sure user is owner
        result = await async_session.execute(
            select(UserOrganizationTable).where(
                and_(
                    UserOrganizationTable.user_uuid == async_test_user.uuid,
                    UserOrganizationTable.organization_uuid
                    == UUID("12345678-1234-1234-1234-123456789abc"),
                )
            )
        )
        user_org = result.scalar_one_or_none()
        assert user_org is not None
        user_org.role = UserRole.OWNER
        await async_session.commit()

        # Mock the organization service to return False for delete
        with patch(
            "lilypad.server.services.organizations.OrganizationService.delete_record_by_uuid"
        ) as mock_delete:
            mock_delete.return_value = False

            response = await async_client.delete("/organizations")
            assert response.status_code == 400
            assert "Organization not found" in response.json()["detail"]

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_organization_with_stripe(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test creating organization with Stripe customer creation in cloud environment."""
        org_data = {"name": "Stripe Test Organization"}

        # Mock cloud environment and billing service
        from lilypad.ee.server.require_license import is_lilypad_cloud
        from lilypad.server.api.v0.main import api
        from lilypad.server.services.billing import BillingService

        # Create mock billing service
        mock_billing_service = MagicMock(spec=BillingService)
        mock_billing_service.create_customer = AsyncMock()

        # Override dependencies
        api.dependency_overrides[BillingService] = lambda: mock_billing_service
        api.dependency_overrides[is_lilypad_cloud] = lambda: True

        try:
            response = await async_client.post("/organizations", json=org_data)
            assert response.status_code == 200

            data = response.json()
            assert data["name"] == "Stripe Test Organization"

            # Verify Stripe customer was created
            mock_billing_service.create_customer.assert_called_once()
            call_args = mock_billing_service.create_customer.call_args[0]
            assert call_args[0].name == "Stripe Test Organization"
            assert call_args[1] == async_test_user.email
        finally:
            # Clean up overrides
            api.dependency_overrides.pop(BillingService, None)
            api.dependency_overrides.pop(is_lilypad_cloud, None)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_organization_with_stripe(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test deleting organization with Stripe customer deletion in cloud environment."""
        # Type guard
        assert async_test_user.uuid is not None

        # Make sure user is owner
        result = await async_session.execute(
            select(UserOrganizationTable).where(
                and_(
                    UserOrganizationTable.user_uuid == async_test_user.uuid,
                    UserOrganizationTable.organization_uuid
                    == UUID("12345678-1234-1234-1234-123456789abc"),
                )
            )
        )
        user_org = result.scalar_one_or_none()
        assert user_org is not None
        user_org.role = UserRole.OWNER
        await async_session.commit()

        # Mock cloud environment and billing service
        from lilypad.server.api.v0.main import api
        from lilypad.server.services.billing import BillingService

        # Create mock billing service
        mock_billing_service = MagicMock(spec=BillingService)
        mock_billing_service.delete_customer_and_billing = AsyncMock()

        # Override dependencies
        api.dependency_overrides[BillingService] = lambda: mock_billing_service

        # Mock is_lilypad_cloud to return True
        with patch(
            "lilypad.server.api.v0.organizations_api.is_lilypad_cloud"
        ) as mock_is_cloud:
            mock_is_cloud.return_value = True

            try:
                response = await async_client.delete("/organizations")
                assert response.status_code == 200

                # Verify Stripe customer was deleted
                mock_billing_service.delete_customer_and_billing.assert_called_once_with(
                    UUID("12345678-1234-1234-1234-123456789abc")
                )
            finally:
                # Clean up overrides
                api.dependency_overrides.pop(BillingService, None)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_organization_with_stripe(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test updating organization with Stripe customer update in cloud environment."""
        factory = AsyncTestFactory(async_session)

        # Type guard
        assert async_test_user.uuid is not None

        # Make sure user is owner
        result = await async_session.execute(
            select(UserOrganizationTable).where(
                and_(
                    UserOrganizationTable.user_uuid == async_test_user.uuid,
                    UserOrganizationTable.organization_uuid
                    == UUID("12345678-1234-1234-1234-123456789abc"),
                )
            )
        )
        user_org = result.scalar_one_or_none()
        assert user_org is not None
        user_org.role = UserRole.OWNER
        await async_session.commit()

        # Get organization and ensure it has billing
        result = await async_session.execute(
            select(OrganizationTable).where(
                OrganizationTable.uuid == UUID("12345678-1234-1234-1234-123456789abc")
            )
        )
        org = result.scalar_one_or_none()
        assert org is not None

        # Create billing entry for the organization
        await factory.create(
            BillingTable,
            organization_uuid=org.uuid,
            stripe_customer_id="cus_test_update",
        )

        # Mock cloud environment and billing service
        from lilypad.server.api.v0.main import api
        from lilypad.server.services.billing import BillingService

        # Create mock billing service
        mock_billing_service = MagicMock(spec=BillingService)
        mock_billing_service.update_customer = AsyncMock()

        # Override dependencies
        api.dependency_overrides[BillingService] = lambda: mock_billing_service

        update_data = {"name": "Updated Stripe Organization"}

        # Mock is_lilypad_cloud to return True
        with patch(
            "lilypad.server.api.v0.organizations_api.is_lilypad_cloud"
        ) as mock_is_cloud:
            mock_is_cloud.return_value = True

            try:
                response = await async_client.patch("/organizations", json=update_data)
                assert response.status_code == 200

                data = response.json()
                assert data["name"] == "Updated Stripe Organization"

                # Verify Stripe customer was updated
                mock_billing_service.update_customer.assert_called_once_with(
                    "cus_test_update", "Updated Stripe Organization"
                )
            finally:
                # Clean up overrides
                api.dependency_overrides.pop(BillingService, None)
