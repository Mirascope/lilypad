"""Tests for auth utils module."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from lilypad.server.api.v0.auth.utils import create_new_user, handle_user
from lilypad.server.models import UserTable
from lilypad.server.schemas.users import UserPublic


def test_handle_user_existing_user_with_organization():
    """Test handle_user with existing user that has an organization."""
    # Setup test data
    user_uuid = uuid4()
    org_uuid = uuid4()
    
    mock_user = UserTable(
        uuid=user_uuid,
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        active_organization_uuid=org_uuid,
    )
    
    # Mock session
    mock_session = Mock(spec=Session)
    mock_result = Mock()
    mock_result.first.return_value = mock_user
    mock_session.exec.return_value = mock_result
    
    # Mock posthog
    mock_posthog = Mock()
    
    # Mock request
    mock_request = Mock()
    
    with patch('lilypad.server.api.v0.auth.utils.UserPublic') as mock_user_public_cls, \
         patch('lilypad.server.api.v0.auth.utils.OrganizationService') as mock_org_service_cls, \
         patch('lilypad.server.api.v0.auth.utils.is_lilypad_cloud') as mock_is_cloud, \
         patch('lilypad.server.api.v0.auth.utils.BillingService') as mock_billing_service_cls, \
         patch('lilypad.server.api.v0.auth.utils.create_jwt_token') as mock_create_token:
        
        # Setup mocks
        mock_user_public = Mock()
        mock_user_public.active_organization_uuid = org_uuid
        mock_user_public.email = "test@example.com"
        mock_user_public.model_copy.return_value = mock_user_public
        mock_user_public_cls.model_validate.return_value = mock_user_public
        
        mock_org_service = Mock()
        mock_org_service_cls.return_value = mock_org_service
        
        mock_billing_service = Mock()
        mock_billing_service_cls.return_value = mock_billing_service
        
        mock_is_cloud.return_value = True
        mock_create_token.return_value = "mock_token"
        
        # Test cloud environment
        result = handle_user(
            name="John",
            email="test@example.com",
            last_name="Doe",
            session=mock_session,
            posthog=mock_posthog,
            request=mock_request,
        )
        
        # Assertions
        mock_org_service.create_stripe_customer.assert_called_once_with(
            mock_billing_service, org_uuid, "test@example.com"
        )
        mock_create_token.assert_called_once_with(mock_user_public)
        mock_user_public.model_copy.assert_called_once_with(update={"access_token": "mock_token"})
        assert result == mock_user_public


def test_handle_user_existing_user_self_hosted():
    """Test handle_user with existing user in self-hosted environment."""
    # Setup test data
    user_uuid = uuid4()
    org_uuid = uuid4()
    
    mock_user = UserTable(
        uuid=user_uuid,
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        active_organization_uuid=org_uuid,
    )
    
    # Mock session
    mock_session = Mock(spec=Session)
    mock_result = Mock()
    mock_result.first.return_value = mock_user
    mock_session.exec.return_value = mock_result
    
    # Mock posthog
    mock_posthog = Mock()
    
    # Mock request
    mock_request = Mock()
    
    with patch('lilypad.server.api.v0.auth.utils.UserPublic') as mock_user_public_cls, \
         patch('lilypad.server.api.v0.auth.utils.OrganizationService') as mock_org_service_cls, \
         patch('lilypad.server.api.v0.auth.utils.is_lilypad_cloud') as mock_is_cloud, \
         patch('lilypad.server.api.v0.auth.utils.get_organization_license') as mock_get_license, \
         patch('lilypad.server.api.v0.auth.utils.create_jwt_token') as mock_create_token:
        
        # Setup mocks
        mock_user_public = Mock()
        mock_user_public.active_organization_uuid = org_uuid
        mock_user_public.email = "test@example.com"
        mock_user_public.model_copy.return_value = mock_user_public
        mock_user_public_cls.model_validate.return_value = mock_user_public
        
        mock_org_service = Mock()
        mock_org_service_cls.return_value = mock_org_service
        
        mock_is_cloud.return_value = False
        mock_create_token.return_value = "mock_token"
        
        # Test self-hosted environment
        result = handle_user(
            name="John",
            email="test@example.com",
            last_name="Doe",
            session=mock_session,
            posthog=mock_posthog,
            request=mock_request,
        )
        
        # Assertions
        mock_get_license.assert_called_once_with(mock_user_public, mock_org_service)
        mock_create_token.assert_called_once_with(mock_user_public)
        assert result == mock_user_public


def test_handle_user_existing_user_without_organization():
    """Test handle_user with existing user that has no organization."""
    # Setup test data
    user_uuid = uuid4()
    
    mock_user = UserTable(
        uuid=user_uuid,
        email="test@example.com",
        first_name="John",
        last_name="Doe",
        active_organization_uuid=None,
    )
    
    # Mock session
    mock_session = Mock(spec=Session)
    mock_result = Mock()
    mock_result.first.return_value = mock_user
    mock_session.exec.return_value = mock_result
    
    # Mock posthog
    mock_posthog = Mock()
    
    # Mock request
    mock_request = Mock()
    
    with patch('lilypad.server.api.v0.auth.utils.UserPublic') as mock_user_public_cls, \
         patch('lilypad.server.api.v0.auth.utils.create_jwt_token') as mock_create_token:
        
        # Setup mocks
        mock_user_public = Mock()
        mock_user_public.active_organization_uuid = None
        mock_user_public.model_copy.return_value = mock_user_public
        mock_user_public_cls.model_validate.return_value = mock_user_public
        
        mock_create_token.return_value = "mock_token"
        
        # Test user without organization
        result = handle_user(
            name="John",
            email="test@example.com",
            last_name="Doe",
            session=mock_session,
            posthog=mock_posthog,
            request=mock_request,
        )
        
        # Assertions
        mock_create_token.assert_called_once_with(mock_user_public)
        mock_user_public.model_copy.assert_called_once_with(update={"access_token": "mock_token"})
        assert result == mock_user_public


def test_handle_user_new_user():
    """Test handle_user with new user creation."""
    # Mock session
    mock_session = Mock(spec=Session)
    mock_result = Mock()
    mock_result.first.return_value = None  # No existing user
    mock_session.exec.return_value = mock_result
    
    # Mock posthog
    mock_posthog = Mock()
    
    # Mock request
    mock_request = Mock()
    
    with patch('lilypad.server.api.v0.auth.utils.create_new_user') as mock_create_new_user:
        mock_new_user = Mock()
        mock_create_new_user.return_value = mock_new_user
        
        # Test new user creation
        result = handle_user(
            name="John",
            email="test@example.com",
            last_name="Doe",
            session=mock_session,
            posthog=mock_posthog,
            request=mock_request,
        )
        
        # Assertions
        mock_create_new_user.assert_called_once_with(
            name="John",
            email="test@example.com",
            last_name="Doe",
            session=mock_session,
            posthog=mock_posthog,
        )
        assert result == mock_new_user


def test_create_new_user_success():
    """Test successful new user creation."""
    # Mock session
    mock_session = Mock(spec=Session)
    
    # Mock posthog
    mock_posthog = Mock()
    
    # Create a mock user with uuid
    mock_user_uuid = uuid4()
    
    with patch('lilypad.server.api.v0.auth.utils.UserTable') as mock_user_table_cls, \
         patch('lilypad.server.api.v0.auth.utils.UserPublic') as mock_user_public_cls, \
         patch('lilypad.server.api.v0.auth.utils.create_jwt_token') as mock_create_token:
        
        # Setup mock user
        mock_user = Mock()
        mock_user.uuid = mock_user_uuid
        mock_user_table_cls.return_value = mock_user
        
        # Setup mock user public
        mock_user_public = Mock()
        mock_user_public.email = "test@example.com"
        mock_user_public.model_copy.return_value = mock_user_public
        mock_user_public_cls.model_validate.return_value = mock_user_public
        
        mock_create_token.return_value = "mock_token"
        
        # Test new user creation
        result = create_new_user(
            name="John",
            email="test@example.com",
            last_name="Doe",
            session=mock_session,
            posthog=mock_posthog,
        )
        
        # Assertions
        mock_user_table_cls.assert_called_once_with(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            active_organization_uuid=None,
        )
        mock_session.add.assert_called_once_with(mock_user)
        mock_session.flush.assert_called_once()
        
        mock_user_public_cls.model_validate.assert_called_once_with(mock_user)
        mock_create_token.assert_called_once_with(mock_user_public)
        mock_user_public.model_copy.assert_called_once_with(update={"access_token": "mock_token"})
        
        mock_posthog.capture.assert_called_once_with(
            distinct_id="test@example.com",
            event="sign_up",
        )
        
        assert result == mock_user_public


def test_create_new_user_failed_uuid_generation():
    """Test new user creation when UUID generation fails."""
    # Mock session
    mock_session = Mock(spec=Session)
    
    # Mock posthog
    mock_posthog = Mock()
    
    with patch('lilypad.server.api.v0.auth.utils.UserTable') as mock_user_table_cls:
        # Setup mock user without uuid
        mock_user = Mock()
        mock_user.uuid = None  # Simulate failed UUID generation
        mock_user_table_cls.return_value = mock_user
        
        # Test that HTTPException is raised
        with pytest.raises(HTTPException) as exc_info:
            create_new_user(
                name="John",
                email="test@example.com",
                last_name="Doe",
                session=mock_session,
                posthog=mock_posthog,
            )
        
        # Assertions
        assert exc_info.value.status_code == 500
        assert "User creation failed, please try again" in str(exc_info.value.detail)


def test_create_new_user_with_none_last_name():
    """Test new user creation with None last name."""
    # Mock session
    mock_session = Mock(spec=Session)
    
    # Mock posthog
    mock_posthog = Mock()
    
    # Create a mock user with uuid
    mock_user_uuid = uuid4()
    
    with patch('lilypad.server.api.v0.auth.utils.UserTable') as mock_user_table_cls, \
         patch('lilypad.server.api.v0.auth.utils.UserPublic') as mock_user_public_cls, \
         patch('lilypad.server.api.v0.auth.utils.create_jwt_token') as mock_create_token:
        
        # Setup mock user
        mock_user = Mock()
        mock_user.uuid = mock_user_uuid
        mock_user_table_cls.return_value = mock_user
        
        # Setup mock user public
        mock_user_public = Mock()
        mock_user_public.email = "test@example.com"
        mock_user_public.model_copy.return_value = mock_user_public
        mock_user_public_cls.model_validate.return_value = mock_user_public
        
        mock_create_token.return_value = "mock_token"
        
        # Test new user creation with None last name
        result = create_new_user(
            name="John",
            email="test@example.com",
            last_name=None,
            session=mock_session,
            posthog=mock_posthog,
        )
        
        # Assertions
        mock_user_table_cls.assert_called_once_with(
            email="test@example.com",
            first_name="John",
            last_name=None,
            active_organization_uuid=None,
        )
        
        assert result == mock_user_public