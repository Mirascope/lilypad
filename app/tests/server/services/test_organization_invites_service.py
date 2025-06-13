"""Tests for the organization invites service."""

import pytest
from sqlmodel import Session
from uuid import uuid4

from lilypad.server.models.organization_invites import OrganizationInviteTable
from lilypad.server.schemas.organization_invites import OrganizationInviteCreate
from lilypad.server.schemas.users import UserPublic
from lilypad.server.services.organization_invites import OrganizationInviteService


@pytest.fixture
def organization_invite_service(db_session: Session, test_user: UserPublic) -> OrganizationInviteService:
    """Create an OrganizationInviteService instance."""
    return OrganizationInviteService(session=db_session, user=test_user)


@pytest.fixture
def test_organization_invite(
    organization_invite_service: OrganizationInviteService, 
    db_session: Session
) -> OrganizationInviteTable:
    """Create a test organization invite."""
    invite_data = OrganizationInviteCreate(
        email="test@example.com",
        organization_uuid=uuid4(),
        token="test_token_123",
        invited_by=organization_invite_service.user.uuid
    )
    invite = organization_invite_service.create_record(invite_data, resend_email_id="test_resend_id")
    db_session.commit()
    db_session.refresh(invite)
    return invite


def test_find_record_by_token_found(
    organization_invite_service: OrganizationInviteService,
    test_organization_invite: OrganizationInviteTable
):
    """Test finding organization invite by token when it exists."""
    found_invite = organization_invite_service.find_record_by_token("test_token_123")
    
    assert found_invite is not None
    assert found_invite.uuid == test_organization_invite.uuid
    assert found_invite.token == "test_token_123"
    assert found_invite.email == "test@example.com"


def test_find_record_by_token_not_found(
    organization_invite_service: OrganizationInviteService
):
    """Test finding organization invite by token when it doesn't exist."""
    found_invite = organization_invite_service.find_record_by_token("nonexistent_token")
    
    assert found_invite is None


def test_find_record_by_token_multiple_invites(
    organization_invite_service: OrganizationInviteService,
    db_session: Session
):
    """Test finding specific invite when multiple invites exist."""
    # Create multiple invites with different tokens
    invite1_data = OrganizationInviteCreate(
        email="user1@example.com",
        organization_uuid=uuid4(),
        token="token_1",
        invited_by=organization_invite_service.user.uuid
    )
    invite1 = organization_invite_service.create_record(invite1_data, resend_email_id="resend_id_1")
    
    invite2_data = OrganizationInviteCreate(
        email="user2@example.com",
        organization_uuid=uuid4(),
        token="token_2",
        invited_by=organization_invite_service.user.uuid
    )
    invite2 = organization_invite_service.create_record(invite2_data, resend_email_id="resend_id_2")
    
    invite3_data = OrganizationInviteCreate(
        email="user3@example.com",
        organization_uuid=uuid4(),
        token="token_3",
        invited_by=organization_invite_service.user.uuid
    )
    invite3 = organization_invite_service.create_record(invite3_data, resend_email_id="resend_id_3")
    
    db_session.commit()
    
    # Should find the correct invite for each token
    found_invite1 = organization_invite_service.find_record_by_token("token_1")
    assert found_invite1 is not None
    assert found_invite1.uuid == invite1.uuid
    assert found_invite1.email == "user1@example.com"
    
    found_invite2 = organization_invite_service.find_record_by_token("token_2")
    assert found_invite2 is not None
    assert found_invite2.uuid == invite2.uuid
    assert found_invite2.email == "user2@example.com"
    
    found_invite3 = organization_invite_service.find_record_by_token("token_3")
    assert found_invite3 is not None
    assert found_invite3.uuid == invite3.uuid
    assert found_invite3.email == "user3@example.com"


def test_find_record_by_token_empty_string(
    organization_invite_service: OrganizationInviteService
):
    """Test finding organization invite with empty token string."""
    found_invite = organization_invite_service.find_record_by_token("")
    
    assert found_invite is None


def test_find_record_by_token_with_similar_tokens(
    organization_invite_service: OrganizationInviteService,
    db_session: Session
):
    """Test finding invite when similar tokens exist."""
    # Create invites with similar but different tokens
    invite1_data = OrganizationInviteCreate(
        email="user1@example.com",
        organization_uuid=uuid4(),
        token="abc123",
        invited_by=organization_invite_service.user.uuid
    )
    invite1 = organization_invite_service.create_record(invite1_data, resend_email_id="resend_abc_1")
    
    invite2_data = OrganizationInviteCreate(
        email="user2@example.com",
        organization_uuid=uuid4(),
        token="abc1234",  # Similar but different
        invited_by=organization_invite_service.user.uuid
    )
    invite2 = organization_invite_service.create_record(invite2_data, resend_email_id="resend_abc_2")
    
    db_session.commit()
    
    # Should find exact matches only
    found_invite1 = organization_invite_service.find_record_by_token("abc123")
    assert found_invite1 is not None
    assert found_invite1.uuid == invite1.uuid
    assert found_invite1.email == "user1@example.com"
    
    found_invite2 = organization_invite_service.find_record_by_token("abc1234")
    assert found_invite2 is not None
    assert found_invite2.uuid == invite2.uuid
    assert found_invite2.email == "user2@example.com"
    
    # Partial match should not be found
    found_partial = organization_invite_service.find_record_by_token("abc12")
    assert found_partial is None


def test_create_record_adds_all_fields(
    organization_invite_service: OrganizationInviteService,
    db_session: Session
):
    """Test that create_record properly creates invite with all fields."""
    organization_uuid = uuid4()
    invite_data = OrganizationInviteCreate(
        email="newuser@example.com",
        organization_uuid=organization_uuid,
        token="unique_token_456",
        invited_by=organization_invite_service.user.uuid
    )
    
    created_invite = organization_invite_service.create_record(invite_data, resend_email_id="unique_resend_id")
    
    assert created_invite.email == "newuser@example.com"
    assert created_invite.organization_uuid == organization_uuid
    assert created_invite.token == "unique_token_456"
    assert created_invite.uuid is not None
    
    # Verify it can be found by token
    found_invite = organization_invite_service.find_record_by_token("unique_token_456")
    assert found_invite is not None
    assert found_invite.uuid == created_invite.uuid


def test_organization_invite_service_inheritance(
    organization_invite_service: OrganizationInviteService
):
    """Test that OrganizationInviteService properly inherits from BaseService."""
    # Should have all BaseService attributes
    assert hasattr(organization_invite_service, 'session')
    assert hasattr(organization_invite_service, 'user')
    assert hasattr(organization_invite_service, 'table')
    assert hasattr(organization_invite_service, 'create_model')
    
    # Should have inherited methods
    assert hasattr(organization_invite_service, 'find_record')
    assert hasattr(organization_invite_service, 'find_record_by_uuid')
    assert hasattr(organization_invite_service, 'find_all_records')
    assert hasattr(organization_invite_service, 'delete_record_by_uuid')
    assert hasattr(organization_invite_service, 'update_record_by_uuid')
    
    # Check service configuration
    assert organization_invite_service.table == OrganizationInviteTable
    assert organization_invite_service.create_model == OrganizationInviteCreate


def test_find_all_records_returns_invites(
    organization_invite_service: OrganizationInviteService,
    test_organization_invite: OrganizationInviteTable
):
    """Test that find_all_records returns organization invites."""
    all_invites = organization_invite_service.find_all_records()
    
    # Should find at least our test invite
    assert len(all_invites) >= 1
    invite_uuids = {invite.uuid for invite in all_invites}
    assert test_organization_invite.uuid in invite_uuids


def test_find_record_by_uuid_works(
    organization_invite_service: OrganizationInviteService,
    test_organization_invite: OrganizationInviteTable
):
    """Test that inherited find_record_by_uuid method works."""
    found_invite = organization_invite_service.find_record_by_uuid(test_organization_invite.uuid)
    
    assert found_invite.uuid == test_organization_invite.uuid
    assert found_invite.token == "test_token_123"
    assert found_invite.email == "test@example.com"


def test_find_record_by_uuid_not_found(
    organization_invite_service: OrganizationInviteService
):
    """Test that find_record_by_uuid raises 404 for non-existent invite."""
    from fastapi import HTTPException
    
    fake_uuid = uuid4()
    with pytest.raises(HTTPException) as exc_info:
        organization_invite_service.find_record_by_uuid(fake_uuid)
    assert exc_info.value.status_code == 404