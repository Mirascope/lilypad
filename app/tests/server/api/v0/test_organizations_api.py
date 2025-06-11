"""Comprehensive tests for the organizations API endpoints."""

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
    billing2 = BillingTable(organization_uuid=org2.uuid)  # type: ignore[call-arg]
    session.add(billing2)
    session.commit()

    # Add user to second org
    user_org2 = UserOrganizationTable(
        user_uuid=test_user.uuid,  # type: ignore[arg-type]
        organization_uuid=org2.uuid,  # type: ignore[arg-type]
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
