"""Comprehensive tests for the organization invites API endpoints."""

import secrets
from unittest.mock import Mock, patch
from uuid import UUID

import pytest
import resend.exceptions
from fastapi.testclient import TestClient
from sqlmodel import Session

from lilypad.server.models import OrganizationInviteTable, UserTable
from lilypad.server.schemas.organization_invites import OrganizationInviteCreate
from lilypad.server.services import OrganizationInviteService, OrganizationService


@pytest.fixture
def organization_invite_data():
    """Sample organization invite data."""
    return {
        "email": "invitee@example.com",
        "invited_by": "550e8400-e29b-41d4-a716-446655440000",
    }


@pytest.fixture
def organization_invite_create_data(organization_invite_data):
    """Organization invite create data."""
    return OrganizationInviteCreate(
        email=organization_invite_data["email"],
        invited_by=UUID(organization_invite_data["invited_by"]),
        organization_uuid=UUID("550e8400-e29b-41d4-a716-446655440001"),
        resend_email_id="email-123",
    )


@pytest.fixture
def test_organization_invite(
    session: Session, test_user: UserTable
) -> OrganizationInviteTable:
    """Create a test organization invite."""
    invite = OrganizationInviteTable(
        email="test@example.com",
        invited_by=test_user.uuid,
        organization_uuid=test_user.active_organization_uuid,
        token="test-invite-token",
        resend_email_id="email-123",
    )
    session.add(invite)
    session.commit()
    session.refresh(invite)
    return invite


def test_get_organization_invites_empty(client: TestClient):
    """Test getting organization invites when none exist."""
    response = client.get("/organizations-invites/")
    assert response.status_code == 200
    assert response.json() == []


def test_get_organization_invites(client: TestClient, test_organization_invite):
    """Test getting organization invites."""
    response = client.get("/organizations-invites/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["email"] == "test@example.com"
    # Note: token field is not exposed in public API for security reasons


def test_get_organization_invite_by_token(client: TestClient, test_organization_invite):
    """Test getting a specific organization invite by token."""
    response = client.get(f"/organizations-invites/{test_organization_invite.token}")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "test@example.com"
    # Note: token field is not exposed in public API for security reasons


def test_get_organization_invite_by_token_not_found(client: TestClient):
    """Test getting organization invite with non-existent token."""
    response = client.get("/organizations-invites/nonexistent-token")
    assert response.status_code == 404
    assert response.json()["detail"] == "Organization invite not found."


def test_create_organization_invite_no_active_organization(client: TestClient, session: Session, test_user: UserTable):
    """Test creating organization invite when user has no active organization."""
    # Clear active organization
    test_user.active_organization_uuid = None
    session.add(test_user)
    session.commit()
    
    invite_data = {
        "email": "newuser@example.com",
        "invited_by": str(test_user.uuid),
    }
    
    response = client.post("/organizations-invites", json=invite_data)
    assert response.status_code == 400
    assert response.json()["detail"] == "User does not have an active organization."


@patch("lilypad.server.api.v0.organization_invites_api.resend.Emails.send")
@patch("lilypad.server.api.v0.organization_invites_api.get_settings")
def test_create_organization_invite_with_resend(
    mock_get_settings, mock_resend_send, client: TestClient, test_user: UserTable
):
    """Test creating organization invite with resend email."""
    # Mock settings
    mock_settings = Mock()
    mock_settings.resend_api_key = "test-api-key"
    mock_settings.client_url = "https://app.lilypad.so"
    mock_get_settings.return_value = mock_settings
    
    # Mock resend response
    mock_resend_send.return_value = {"id": "email-123"}
    
    invite_data = {
        "email": "newuser@example.com",
        "invited_by": str(test_user.uuid),
    }
    
    response = client.post("/organizations-invites", json=invite_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["resend_email_id"] == "email-123"
    assert "invite_link" in data
    
    # Verify resend.Emails.send was called
    mock_resend_send.assert_called_once()
    call_args = mock_resend_send.call_args[0][0]
    assert call_args["to"] == ["newuser@example.com"]
    assert call_args["from"] == "Lilypad Team <team@lilypad.so>"
    assert "Test Organization" in call_args["subject"]


@patch("lilypad.server.api.v0.organization_invites_api.get_settings")
def test_create_organization_invite_without_resend(
    mock_get_settings, client: TestClient, test_user: UserTable
):
    """Test creating organization invite without resend API key."""
    # Mock settings without resend key
    mock_settings = Mock()
    mock_settings.resend_api_key = None
    mock_settings.client_url = "https://app.lilypad.so"
    mock_get_settings.return_value = mock_settings
    
    invite_data = {
        "email": "newuser@example.com",
        "invited_by": str(test_user.uuid),
    }
    
    response = client.post("/organizations-invites", json=invite_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["resend_email_id"] == "n/a"


@patch("lilypad.server.api.v0.organization_invites_api.resend.Emails.send")
@patch("lilypad.server.api.v0.organization_invites_api.get_settings")
def test_create_organization_invite_resend_error(
    mock_get_settings, mock_resend_send, client: TestClient, test_user: UserTable
):
    """Test creating organization invite when resend fails."""
    # Mock settings
    mock_settings = Mock()
    mock_settings.resend_api_key = "test-api-key"
    mock_settings.client_url = "https://app.lilypad.so"
    mock_get_settings.return_value = mock_settings
    
    # Mock resend error
    mock_resend_send.side_effect = resend.exceptions.ResendError(
        error_type="invalid_request", 
        message="Email failed", 
        suggested_action="Check your request",
        code=400
    )
    
    invite_data = {
        "email": "newuser@example.com",
        "invited_by": str(test_user.uuid),
    }
    
    response = client.post("/organizations-invites", json=invite_data)
    assert response.status_code == 500
    assert response.json()["detail"] == "Failed to send email."


@patch("lilypad.server.api.v0.organization_invites_api.get_settings")
def test_create_organization_invite_replaces_existing(
    mock_get_settings, client: TestClient, test_organization_invite: OrganizationInviteTable, session: Session
):
    """Test creating organization invite replaces existing invite for same email."""
    # Mock settings
    mock_settings = Mock()
    mock_settings.resend_api_key = None
    mock_settings.client_url = "https://app.lilypad.so"
    mock_get_settings.return_value = mock_settings
    
    # Use same email as existing invite
    invite_data = {
        "email": test_organization_invite.email,
        "invited_by": str(test_organization_invite.invited_by),
    }
    
    # Get original invite UUID
    original_uuid = test_organization_invite.uuid
    
    response = client.post("/organizations-invites", json=invite_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["email"] == test_organization_invite.email
    assert data["uuid"] != str(original_uuid)  # New UUID means new invite created
    
    # Verify old invite was deleted
    old_invite = session.get(OrganizationInviteTable, original_uuid)
    assert old_invite is None


def test_remove_organization_invite(client: TestClient, test_organization_invite: OrganizationInviteTable):
    """Test removing an organization invite."""
    invite_uuid = test_organization_invite.uuid
    
    response = client.delete(f"/organizations-invites/{invite_uuid}")
    assert response.status_code == 200
    assert response.json() is True
    
    # Verify invite was deleted by trying to get it again
    get_response = client.get(f"/organizations-invites/{test_organization_invite.token}")
    assert get_response.status_code == 404


def test_remove_organization_invite_not_found(client: TestClient):
    """Test removing non-existent organization invite."""
    fake_uuid = "550e8400-e29b-41d4-a716-446655440000"
    
    response = client.delete(f"/organizations-invites/{fake_uuid}")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


@patch("secrets.token_urlsafe")
def test_create_organization_invite_token_generation(mock_token_urlsafe, client: TestClient, test_user: UserTable):
    """Test that organization invite generates proper token."""
    mock_token_urlsafe.return_value = "generated-secure-token"
    
    with patch("lilypad.server.api.v0.organization_invites_api.get_settings") as mock_get_settings:
        mock_settings = Mock()
        mock_settings.resend_api_key = None
        mock_settings.client_url = "https://app.lilypad.so"
        mock_get_settings.return_value = mock_settings
        
        invite_data = {
            "email": "newuser@example.com",
            "invited_by": str(test_user.uuid),
        }
        
        response = client.post("/organizations-invites", json=invite_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["email"] == "newuser@example.com"
        # Note: token field is not exposed in public API for security reasons
        
        # Verify token was generated with correct length
        mock_token_urlsafe.assert_called_once_with(32)