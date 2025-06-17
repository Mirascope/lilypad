"""Comprehensive tests for the organizations API endpoints."""

from unittest.mock import MagicMock, patch
from uuid import UUID

from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.ee.server.models import UserOrganizationTable, UserRole
from lilypad.server.models import BillingTable, OrganizationTable, UserTable


def test_create_organization(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test creating a new organization."""
    org_data = {"name": "New Organization"}

    response = client.post("/organizations", json=org_data)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "New Organization"
    assert data["uuid"] is not None

    # Verify in database
    db_org = session.get(OrganizationTable, UUID(data["uuid"]))
    assert db_org is not None
    assert db_org.name == "New Organization"

    # Verify user is added as OWNER
    user_org = (
        session.query(UserOrganizationTable)
        .filter_by(organization_uuid=db_org.uuid)
        .first()
    )
    assert user_org is not None
    assert user_org.role == UserRole.OWNER

    # Verify user's active org was updated
    session.refresh(test_user)
    assert test_user.active_organization_uuid == db_org.uuid


def test_create_organization_duplicate_name(client: TestClient):
    """Test creating organization with duplicate name fails."""
    # First organization already exists from fixtures
    org_data = {
        "name": "Test Organization"  # Same as fixture
    }

    response = client.post("/organizations", json=org_data)
    assert response.status_code == 409
    detail = response.json().get("detail", "")
    assert "already exists" in detail.lower()


def test_create_organization_invalid_data(client: TestClient):
    """Test creating organization with invalid data."""
    # Missing required field
    org_data = {}

    response = client.post("/organizations", json=org_data)
    assert response.status_code == 422


def test_update_organization(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test updating an organization."""
    # Type guard
    assert test_user.uuid is not None

    # Change user role to OWNER
    user_org = (
        session.query(UserOrganizationTable)
        .filter_by(
            user_uuid=test_user.uuid,
            organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        )
        .first()
    )
    assert user_org is not None
    user_org.role = UserRole.OWNER
    session.commit()

    update_data = {"name": "Updated Organization Name"}

    response = client.patch("/organizations", json=update_data)
    assert response.status_code == 200

    data = response.json()
    assert data["name"] == "Updated Organization Name"

    # Verify in database
    org_uuid = UUID("12345678-1234-1234-1234-123456789abc")
    db_org = session.get(OrganizationTable, org_uuid)
    assert db_org is not None
    assert db_org.name == "Updated Organization Name"


def test_update_organization_not_owner(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test that non-owner users cannot update organization."""
    # Type guard
    assert test_user.uuid is not None

    # Change user role to MEMBER
    user_org = (
        session.query(UserOrganizationTable)
        .filter_by(
            user_uuid=test_user.uuid,
            organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        )
        .first()
    )
    assert user_org is not None
    user_org.role = UserRole.MEMBER
    session.commit()

    update_data = {"name": "Should Not Update"}
    response = client.patch("/organizations", json=update_data)

    assert response.status_code == 403
    detail = response.json().get("detail", "")
    assert "owner" in detail.lower()


def test_update_organization_no_active_org(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test updating when user has no active organization."""
    # Clear user's active organization
    test_user.active_organization_uuid = None
    session.commit()

    update_data = {"name": "Should Not Work"}
    response = client.patch("/organizations", json=update_data)

    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "does not have an active organization" in detail


def test_update_organization_with_license(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test updating organization with license key."""
    # Type guard
    assert test_user.uuid is not None

    # Change user role to OWNER
    user_org = (
        session.query(UserOrganizationTable)
        .filter_by(
            user_uuid=test_user.uuid,
            organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        )
        .first()
    )
    assert user_org is not None
    user_org.role = UserRole.OWNER
    session.commit()

    # Note: This will fail with invalid license in test environment
    update_data = {"license": "invalid-license-key"}

    response = client.patch("/organizations", json=update_data)
    # Should fail with invalid license
    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "invalid license" in detail.lower()


def test_delete_organization(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test deleting an organization."""
    # Create a second organization to switch to after deletion
    org2 = OrganizationTable(name="Second Org", license="license2")
    session.add(org2)
    session.commit()

    # Create billing entry for the org2
    assert org2.uuid is not None
    assert test_user.uuid is not None  # Type guard

    billing2 = BillingTable(
        organization_uuid=org2.uuid, stripe_customer_id="cus_test_org2"
    )
    session.add(billing2)
    session.commit()

    # Add user to second org
    user_org2 = UserOrganizationTable(
        user_uuid=test_user.uuid,
        organization_uuid=org2.uuid,
        role=UserRole.MEMBER,
        organization=org2,
    )
    session.add(user_org2)
    session.commit()

    # Switch to org2 and make user owner
    test_user.active_organization_uuid = org2.uuid
    user_org2.role = UserRole.OWNER
    session.commit()

    # Delete the active organization
    response = client.delete("/organizations")
    assert response.status_code == 200

    # Response should be UserPublic with updated JWT
    data = response.json()
    assert "access_token" in data
    # User should be switched to the first org
    assert data["active_organization_uuid"] == str(
        UUID("12345678-1234-1234-1234-123456789abc")
    )

    # Verify org2 is deleted
    db_org = session.get(OrganizationTable, org2.uuid)
    assert db_org is None


def test_delete_organization_not_owner(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test that non-owner users cannot delete organization."""
    # Type guard
    assert test_user.uuid is not None

    # Change user role to MEMBER
    user_org = (
        session.query(UserOrganizationTable)
        .filter_by(
            user_uuid=test_user.uuid,
            organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        )
        .first()
    )
    assert user_org is not None
    user_org.role = UserRole.MEMBER
    session.commit()

    response = client.delete("/organizations")
    assert response.status_code == 403
    detail = response.json().get("detail", "")
    assert "owner" in detail.lower()


def test_delete_organization_no_active_org(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test deleting when user has no active organization."""
    # Clear user's active organization
    test_user.active_organization_uuid = None
    session.commit()

    response = client.delete("/organizations")
    assert response.status_code == 400
    detail = response.json().get("detail", "")
    assert "does not have an active organization" in detail


def test_delete_last_organization(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test deleting the last organization user belongs to."""
    # Type guard
    assert test_user.uuid is not None

    # Make sure user is owner
    user_org = (
        session.query(UserOrganizationTable)
        .filter_by(
            user_uuid=test_user.uuid,
            organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        )
        .first()
    )
    assert user_org is not None
    user_org.role = UserRole.OWNER
    session.commit()

    # Delete the only organization
    response = client.delete("/organizations")
    assert response.status_code == 200

    # Response should be UserPublic with no active org
    data = response.json()
    assert "access_token" in data
    assert data["active_organization_uuid"] is None


def test_delete_organization_not_found(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test deleting organization that doesn't exist or user doesn't have access to."""
    # Type guard
    assert test_user.uuid is not None

    # Make sure user is owner
    user_org = (
        session.query(UserOrganizationTable)
        .filter_by(
            user_uuid=test_user.uuid,
            organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        )
        .first()
    )
    assert user_org is not None
    user_org.role = UserRole.OWNER
    session.commit()

    # Mock the organization service to return False for delete
    with patch(
        "lilypad.server.services.organizations.OrganizationService.delete_record_by_uuid"
    ) as mock_delete:
        mock_delete.return_value = False

        response = client.delete("/organizations")
        assert response.status_code == 400
        assert "Organization not found" in response.json()["detail"]


def test_create_organization_with_stripe(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test creating organization with Stripe customer creation in cloud environment."""
    org_data = {"name": "Stripe Test Organization"}

    # Mock cloud environment and billing service
    from lilypad.ee.server.require_license import is_lilypad_cloud
    from lilypad.server.api.v0.main import api
    from lilypad.server.services.billing import BillingService

    # Create mock billing service
    mock_billing_service = MagicMock(spec=BillingService)
    mock_billing_service.create_customer = MagicMock()

    # Override dependencies
    api.dependency_overrides[BillingService] = lambda: mock_billing_service
    api.dependency_overrides[is_lilypad_cloud] = lambda: True

    try:
        response = client.post("/organizations", json=org_data)
        assert response.status_code == 200

        data = response.json()
        assert data["name"] == "Stripe Test Organization"

        # Verify Stripe customer was created
        mock_billing_service.create_customer.assert_called_once()
        call_args = mock_billing_service.create_customer.call_args[0]
        assert call_args[0].name == "Stripe Test Organization"
        assert call_args[1] == test_user.email
    finally:
        # Clean up overrides
        api.dependency_overrides.pop(BillingService, None)
        api.dependency_overrides.pop(is_lilypad_cloud, None)


def test_delete_organization_with_stripe(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test deleting organization with Stripe customer deletion in cloud environment."""
    # Type guard
    assert test_user.uuid is not None

    # Make sure user is owner
    user_org = (
        session.query(UserOrganizationTable)
        .filter_by(
            user_uuid=test_user.uuid,
            organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        )
        .first()
    )
    assert user_org is not None
    user_org.role = UserRole.OWNER
    session.commit()

    # Mock cloud environment and billing service
    from lilypad.server.api.v0.main import api
    from lilypad.server.services.billing import BillingService

    # Create mock billing service
    mock_billing_service = MagicMock(spec=BillingService)
    mock_billing_service.delete_customer_and_billing = MagicMock()

    # Override dependencies
    api.dependency_overrides[BillingService] = lambda: mock_billing_service

    # Mock is_lilypad_cloud to return True
    with patch(
        "lilypad.server.api.v0.organizations_api.is_lilypad_cloud"
    ) as mock_is_cloud:
        mock_is_cloud.return_value = True

        try:
            response = client.delete("/organizations")
            assert response.status_code == 200

            # Verify Stripe customer was deleted
            mock_billing_service.delete_customer_and_billing.assert_called_once_with(
                UUID("12345678-1234-1234-1234-123456789abc")
            )
        finally:
            # Clean up overrides
            api.dependency_overrides.pop(BillingService, None)


def test_update_organization_with_stripe(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test updating organization with Stripe customer update in cloud environment."""
    # Type guard
    assert test_user.uuid is not None

    # Make sure user is owner
    user_org = (
        session.query(UserOrganizationTable)
        .filter_by(
            user_uuid=test_user.uuid,
            organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        )
        .first()
    )
    assert user_org is not None
    user_org.role = UserRole.OWNER
    session.commit()

    # Get organization and ensure it has billing
    org = session.get(OrganizationTable, UUID("12345678-1234-1234-1234-123456789abc"))
    assert org is not None

    # Create billing entry for the organization
    billing = BillingTable(
        organization_uuid=org.uuid,  # type: ignore[arg-type]
        stripe_customer_id="cus_test_update",
    )
    session.add(billing)
    session.commit()

    # Mock cloud environment and billing service
    from lilypad.server.api.v0.main import api
    from lilypad.server.services.billing import BillingService

    # Create mock billing service
    mock_billing_service = MagicMock(spec=BillingService)
    mock_billing_service.update_customer = MagicMock()

    # Override dependencies
    api.dependency_overrides[BillingService] = lambda: mock_billing_service

    update_data = {"name": "Updated Stripe Organization"}

    # Mock is_lilypad_cloud to return True
    with patch(
        "lilypad.server.api.v0.organizations_api.is_lilypad_cloud"
    ) as mock_is_cloud:
        mock_is_cloud.return_value = True

        try:
            response = client.patch("/organizations", json=update_data)
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
