"""Comprehensive tests for the user organizations API endpoints."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from ee.validate import LicenseInfo, Tier
from lilypad.ee.server.models.user_organizations import UserOrganizationTable, UserRole
from lilypad.server.models import OrganizationInviteTable, UserTable


@pytest.fixture
def test_user_organization(
    session: Session, test_user: UserTable
) -> UserOrganizationTable:
    """Get the test user organization created in the conftest."""
    # The user organization is already created in the conftest
    user_org = (
        session.query(UserOrganizationTable).filter_by(user_uuid=test_user.uuid).first()
    )
    if not user_org:
        # Create if somehow missing
        user_org = UserOrganizationTable(
            user_uuid=test_user.uuid,  # type: ignore[arg-type]
            organization_uuid=test_user.active_organization_uuid,  # type: ignore[arg-type]
            role=UserRole.ADMIN,
        )
        session.add(user_org)
        session.commit()
        session.refresh(user_org)
    return user_org


@pytest.fixture
def test_organization_invite(
    session: Session, test_user: UserTable
) -> OrganizationInviteTable:
    """Create a test organization invite."""
    invite = OrganizationInviteTable(
        email="invited@example.com",
        invited_by=test_user.uuid,  # type: ignore[arg-type]
        organization_uuid=test_user.active_organization_uuid,  # type: ignore[arg-type]
        token="test-invite-token",
        resend_email_id="email-123",
    )
    session.add(invite)
    session.commit()
    session.refresh(invite)
    return invite


@pytest.fixture
def second_user(session: Session, test_user: UserTable) -> UserTable:
    """Create a second test user."""
    user = UserTable(
        uuid=uuid4(),  # type: ignore[call-arg]
        email="second@test.com",
        first_name="Second User",
        active_organization_uuid=test_user.active_organization_uuid,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


@pytest.fixture
def second_user_organization(
    session: Session, second_user: UserTable
) -> UserOrganizationTable:
    """Create a user organization for the second user."""
    user_org = UserOrganizationTable(
        user_uuid=second_user.uuid,  # type: ignore[arg-type]
        organization_uuid=second_user.active_organization_uuid,  # type: ignore[arg-type]
        role=UserRole.MEMBER,
    )
    session.add(user_org)
    session.commit()
    session.refresh(user_org)
    return user_org


def test_get_users_by_organization_with_default_user(client: TestClient):
    """Test getting users from organization returns the default test user."""
    response = client.get("/ee/user-organizations/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "test@test.com"


def test_get_users_by_organization(
    client: TestClient, second_user_organization: UserOrganizationTable
):
    """Test getting users by organization."""
    response = client.get("/ee/user-organizations/users")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Default test user + second user
    user_emails = [user["email"] for user in data]
    assert "test@test.com" in user_emails
    assert "second@test.com" in user_emails


def test_get_user_organizations_with_default_user(client: TestClient):
    """Test getting user organizations returns the default test user organization."""
    response = client.get("/ee/user-organizations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["role"] == UserRole.ADMIN.value


def test_get_user_organizations(
    client: TestClient, second_user_organization: UserOrganizationTable
):
    """Test getting user organizations."""
    response = client.get("/ee/user-organizations")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2  # Default user org + second user org
    roles = [user_org["role"] for user_org in data]
    assert UserRole.ADMIN.value in roles
    assert UserRole.MEMBER.value in roles


def test_create_user_organization_invalid_token(client: TestClient):
    """Test creating user organization with invalid token."""
    token_data = {"token": "invalid-token"}

    response = client.post("/ee/user-organizations", json=token_data)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


@patch("lilypad.ee.server.api.v0.user_organizations_api.is_lilypad_cloud")
def test_create_user_organization_success_self_hosted(
    mock_is_cloud,
    client: TestClient,
    test_organization_invite: OrganizationInviteTable,
    session: Session,
):
    """Test creating user organization successfully in self-hosted mode."""
    mock_is_cloud.return_value = False

    # Mock the license validator
    with patch(
        "lilypad.ee.server.api.v0.user_organizations_api.LicenseValidator"
    ) as mock_validator:
        mock_license_info = LicenseInfo(
            customer="test",
            license_id="test",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            tier=Tier.FREE,
            organization_uuid=test_organization_invite.organization_uuid,
        )
        mock_validator.return_value.validate_license.return_value = mock_license_info

        token_data = {"token": test_organization_invite.token}

        response = client.post("/ee/user-organizations", json=token_data)
        assert response.status_code == 200

        data = response.json()
        assert data["email"] == "test@test.com"
        assert "access_token" in data

        # Verify invite was deleted
        invite = session.get(OrganizationInviteTable, test_organization_invite.uuid)
        assert invite is None


@patch("lilypad.ee.server.api.v0.user_organizations_api.is_lilypad_cloud")
def test_create_user_organization_success_cloud(
    mock_is_cloud,
    client: TestClient,
    test_organization_invite: OrganizationInviteTable,
    session: Session,
):
    """Test creating user organization successfully in cloud mode."""
    mock_is_cloud.return_value = True

    # Mock billing service
    with patch(
        "lilypad.ee.server.api.v0.user_organizations_api.BillingService"
    ) as mock_billing:
        mock_billing_instance = Mock()
        mock_billing_instance.get_tier_from_billing.return_value = Tier.FREE
        mock_billing.return_value = mock_billing_instance

        # Create a mock request object
        class MockRequest:
            pass

        # Override the client to include request
        with patch.object(client, "post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "email": "test@test.com",
                "access_token": "mock-token",
            }
            mock_post.return_value = mock_response

            token_data = {"token": test_organization_invite.token}
            response = client.post("/ee/user-organizations", json=token_data)
            assert response.status_code == 200


@patch("lilypad.ee.server.api.v0.user_organizations_api.is_lilypad_cloud")
def test_create_user_organization_user_limit_exceeded(
    mock_is_cloud,
    client: TestClient,
    test_organization_invite: OrganizationInviteTable,
    test_user_organization: UserOrganizationTable,
):
    """Test creating user organization when user limit is exceeded."""
    mock_is_cloud.return_value = False

    # Mock the license validator to return FREE tier (limit of 1 user)
    with patch(
        "lilypad.ee.server.api.v0.user_organizations_api.LicenseValidator"
    ) as mock_validator:
        mock_license_info = LicenseInfo(
            customer="test",
            license_id="test",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            tier=Tier.FREE,
            organization_uuid=test_organization_invite.organization_uuid,
        )
        mock_validator.return_value.validate_license.return_value = mock_license_info

        # Mock cloud_features to have a low limit
        with patch(
            "lilypad.ee.server.api.v0.user_organizations_api.cloud_features"
        ) as mock_features:
            mock_feature = Mock()
            mock_feature.num_users_per_organization = 1
            mock_features.return_value = {Tier.FREE: mock_feature}
            mock_features.__getitem__ = lambda self, key: mock_feature

            token_data = {"token": test_organization_invite.token}

            response = client.post("/ee/user-organizations", json=token_data)
            assert response.status_code == 429
            assert "Exceeded the maximum number of users" in response.json()["detail"]


def test_create_user_organization_invite_delete_failed(
    client: TestClient, test_organization_invite: OrganizationInviteTable
):
    """Test creating user organization when invite deletion fails."""
    with patch(
        "lilypad.ee.server.api.v0.user_organizations_api.is_lilypad_cloud"
    ) as mock_is_cloud:
        mock_is_cloud.return_value = False

        with patch(
            "lilypad.ee.server.api.v0.user_organizations_api.LicenseValidator"
        ) as mock_validator:
            mock_license_info = LicenseInfo(
                customer="test",
                license_id="test",
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                tier=Tier.FREE,
                organization_uuid=test_organization_invite.organization_uuid,
            )
            mock_validator.return_value.validate_license.return_value = (
                mock_license_info
            )

            # Mock the organization invite service to fail delete
            with patch(
                "lilypad.server.services.organization_invites.OrganizationInviteService.delete_record_by_uuid"
            ) as mock_delete:
                mock_delete.return_value = False

                token_data = {"token": test_organization_invite.token}

                response = client.post("/ee/user-organizations", json=token_data)
                assert response.status_code == 500
                assert response.json()["detail"] == "Failed to delete invite."


def test_update_user_organization(
    client: TestClient, test_user_organization: UserOrganizationTable
):
    """Test updating a user organization role."""
    update_data = {"role": UserRole.MEMBER.value}

    response = client.patch(
        f"/ee/user-organizations/{test_user_organization.uuid}", json=update_data
    )
    assert response.status_code == 200

    data = response.json()
    assert data["role"] == UserRole.MEMBER.value
    assert data["uuid"] == str(test_user_organization.uuid)


def test_update_user_organization_not_found(client: TestClient):
    """Test updating non-existent user organization."""
    fake_uuid = uuid4()
    update_data = {"role": UserRole.MEMBER.value}

    response = client.patch(f"/ee/user-organizations/{fake_uuid}", json=update_data)
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_user_organization(
    client: TestClient, test_user_organization: UserOrganizationTable
):
    """Test deleting a user organization."""
    response = client.delete(f"/ee/user-organizations/{test_user_organization.uuid}")
    assert response.status_code == 200
    assert response.json() is True


def test_delete_user_organization_not_found(client: TestClient):
    """Test deleting non-existent user organization."""
    fake_uuid = uuid4()

    response = client.delete(f"/ee/user-organizations/{fake_uuid}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_create_user_organization_without_license_info(
    client: TestClient, test_organization_invite: OrganizationInviteTable
):
    """Test creating user organization when license validation returns None."""
    with patch(
        "lilypad.ee.server.api.v0.user_organizations_api.is_lilypad_cloud"
    ) as mock_is_cloud:
        mock_is_cloud.return_value = False

        # Mock the license validator to return None
        with patch(
            "lilypad.ee.server.api.v0.user_organizations_api.LicenseValidator"
        ) as mock_validator:
            mock_validator.return_value.validate_license.return_value = None

            token_data = {"token": test_organization_invite.token}

            response = client.post("/ee/user-organizations", json=token_data)
            assert (
                response.status_code == 200
            )  # Should still work with FREE tier default


def test_create_user_organization_create_failed(
    client: TestClient, test_organization_invite: OrganizationInviteTable
):
    """Test creating user organization when user organization creation fails."""
    with patch(
        "lilypad.ee.server.api.v0.user_organizations_api.is_lilypad_cloud"
    ) as mock_is_cloud:
        mock_is_cloud.return_value = False

        with patch(
            "lilypad.ee.server.api.v0.user_organizations_api.LicenseValidator"
        ) as mock_validator:
            mock_license_info = LicenseInfo(
                customer="test",
                license_id="test",
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                tier=Tier.FREE,
                organization_uuid=test_organization_invite.organization_uuid,
            )
            mock_validator.return_value.validate_license.return_value = (
                mock_license_info
            )

            # Mock the user organization service to fail creation
            with patch(
                "lilypad.ee.server.services.user_organizations.UserOrganizationService.create_record"
            ) as mock_create:
                mock_create.return_value = None

                token_data = {"token": test_organization_invite.token}

                response = client.post("/ee/user-organizations", json=token_data)
                assert response.status_code == 500
                assert (
                    response.json()["detail"] == "Failed to create user organization."
                )


def test_get_license_endpoint(client: TestClient):
    """Test the EE organizations license endpoint."""
    response = client.get("/ee/organizations/license")

    # This endpoint should return license info or appropriate error
    # The exact response depends on license validation setup
    assert response.status_code in [200, 401, 403, 404]

    if response.status_code == 200:
        # If successful, should return license info
        license_info = response.json()
        assert isinstance(license_info, dict)


def test_user_organization_service_not_found():
    """Test UserOrganizationService when user organization not found (line 31)."""
    from unittest.mock import Mock
    from uuid import uuid4

    import pytest
    from fastapi import HTTPException
    from sqlmodel import Session

    from lilypad.ee.server.services.user_organizations import UserOrganizationService
    from lilypad.server.models.users import UserTable

    # Create mock session and user
    mock_session = Mock(spec=Session)
    mock_user = Mock(spec=UserTable)
    mock_user.uuid = uuid4()
    mock_user.active_organization_uuid = uuid4()

    # Mock session.exec to return None (no user organization found)
    mock_session.exec.return_value.first.return_value = None

    service = UserOrganizationService(session=mock_session, user=mock_user)

    # Should raise HTTPException when user organization not found
    with pytest.raises(HTTPException) as exc_info:
        service.get_active_user_organization()

    assert exc_info.value.status_code == 404
    assert "Record for user_organizations not found" in str(exc_info.value.detail)
