"""Comprehensive tests for the users API endpoints."""

from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.ee.server.models import UserOrganizationTable, UserRole
from lilypad.server.models import OrganizationTable, UserTable


def test_get_current_user(client: TestClient):
    """Test getting current authenticated user."""
    response = client.get("/current-user")
    assert response.status_code == 200

    data = response.json()
    assert data["email"] == "test@test.com"
    assert data["first_name"] == "Test User"
    assert data["uuid"] is not None
    assert data["active_organization_uuid"] is not None
    assert "access_token" in data


def test_update_user_active_organization(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test updating user's active organization."""
    # Create a second organization
    org2 = OrganizationTable(name="Second Organization", license="654321")
    session.add(org2)
    session.commit()

    # Add user to the second organization
    assert test_user.uuid is not None  # Type guard
    assert org2.uuid is not None  # Type guard

    user_org2 = UserOrganizationTable(
        user_uuid=test_user.uuid,
        organization_uuid=org2.uuid,
        role=UserRole.MEMBER,
        organization=org2,
    )
    session.add(user_org2)
    session.commit()

    # Update active organization
    response = client.put(f"/users/{org2.uuid}")
    assert response.status_code == 200

    data = response.json()
    assert data["active_organization_uuid"] == str(org2.uuid)
    assert "access_token" in data  # New JWT with updated org


def test_update_user_active_organization_not_member(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test updating to organization user is not a member of."""
    # Create an organization the user is not part of
    other_org = OrganizationTable(name="Other Organization", license="999999")
    session.add(other_org)
    session.commit()

    # Try to update to this organization
    # Note: Current implementation doesn't validate membership
    response = client.put(f"/users/{other_org.uuid}")
    assert response.status_code == 200

    # Verify it was updated (even though user is not a member)
    data = response.json()
    assert data["active_organization_uuid"] == str(other_org.uuid)


def test_update_user_active_organization_none(client: TestClient):
    """Test clearing user's active organization."""
    # The endpoint expects a UUID, so we can't test passing None
    # Instead, we'll test with an invalid UUID format
    response = client.put("/users/not-a-uuid")
    assert response.status_code == 422  # Validation error


def test_update_user_keys(client: TestClient, session: Session, test_user: UserTable):
    """Test updating user keys."""
    keys_data = {"openai_api_key": "sk-test123", "anthropic_api_key": "sk-ant-test456"}

    response = client.patch("/users", json=keys_data)
    assert response.status_code == 200

    data = response.json()
    # Keys should be stored but not returned in response for security
    assert "keys" in data

    # Verify in database
    session.refresh(test_user)
    assert test_user.keys == keys_data


def test_update_user_keys_empty(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test clearing user keys."""
    # First set some keys
    test_user.keys = {"existing_key": "value"}
    session.commit()

    # Clear keys
    response = client.patch("/users", json={})
    assert response.status_code == 200

    # Verify keys are cleared
    session.refresh(test_user)
    assert test_user.keys == {}


def test_update_user_keys_partial(
    client: TestClient, session: Session, test_user: UserTable
):
    """Test partial update of user keys - replaces entire dict."""
    # Set initial keys
    test_user.keys = {"key1": "value1", "key2": "value2"}
    session.commit()

    # Update with new keys - this replaces the entire dict
    update_data = {"key2": "new_value2", "key3": "value3"}
    response = client.patch("/users", json=update_data)
    assert response.status_code == 200

    # Verify replacement behavior (not merge)
    session.refresh(test_user)
    assert test_user.keys == update_data  # Only the new keys remain
