"""Test cases for authentication API endpoints."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from lilypad.server.models.users import UserTable
from lilypad.server.schemas.users import UserPublic


@pytest.fixture
def mock_posthog():
    """Mock PostHog client."""
    return Mock()


@pytest.fixture
def mock_settings():
    """Mock settings."""
    settings = Mock()
    settings.google_client_id = "test_google_client_id"
    settings.google_client_secret = "test_google_secret"
    settings.github_client_id = "test_github_client_id"
    settings.github_client_secret = "test_github_secret"
    settings.client_url = "http://localhost:3000"
    settings.api_url = "http://localhost:8000"
    return settings


@pytest.fixture
def mock_session():
    """Mock database session."""
    session = Mock(spec=Session)
    session.exec = Mock()
    session.add = Mock()
    session.commit = Mock()
    session.refresh = Mock()
    session.flush = Mock()
    return session


@pytest.fixture
def mock_request():
    """Mock request object."""
    request = Mock()
    request.client = Mock()
    request.client.host = "127.0.0.1"
    return request


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
@patch("lilypad.server.api.v0.auth.google_api.handle_user")
async def test_google_callback_success(
    mock_handle_user,
    mock_httpx_client,
    mock_posthog,
    mock_settings,
    mock_session,
    mock_request,
):
    """Test successful Google OAuth callback."""
    from lilypad.server.api.v0.auth.google_api import google_callback

    # Setup mocks
    user_uuid = uuid4()
    org_uuid = uuid4()
    mock_user = UserPublic(
        uuid=user_uuid,
        email="test@example.com",
        first_name="Test",
        last_name="User",
        active_organization_uuid=org_uuid,
    )
    mock_handle_user.return_value = mock_user

    # Mock httpx responses
    mock_client_instance = AsyncMock()
    mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

    # Mock token exchange response
    token_response = Mock()
    token_response.json.return_value = {"access_token": "test_token"}
    mock_client_instance.post.return_value = token_response

    # Mock user info response
    user_response = Mock()
    user_response.json.return_value = {
        "email": "test@example.com",
        "given_name": "Test",
        "family_name": "User",
        "verified_email": True,
    }
    mock_client_instance.get.return_value = user_response

    # Call the function
    result = await google_callback(
        code="test_code",
        posthog=mock_posthog,
        settings=mock_settings,
        session=mock_session,
        request=mock_request,
    )

    # Assertions
    assert result == mock_user
    mock_handle_user.assert_called_once_with(
        name="Test",
        email="test@example.com",
        last_name="User",
        session=mock_session,
        posthog=mock_posthog,
        request=mock_request,
    )


@pytest.mark.asyncio
async def test_google_callback_no_code(
    mock_posthog, mock_settings, mock_session, mock_request
):
    """Test Google callback with no authorization code."""
    from lilypad.server.api.v0.auth.google_api import google_callback

    with pytest.raises(HTTPException) as exc_info:
        await google_callback(
            code="",
            posthog=mock_posthog,
            settings=mock_settings,
            session=mock_session,
            request=mock_request,
        )

    assert exc_info.value.status_code == 400
    assert "No authorization code provided" in str(exc_info.value.detail)


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_google_callback_email_not_verified(
    mock_httpx_client, mock_posthog, mock_settings, mock_session, mock_request
):
    """Test Google callback when email is not verified."""
    from lilypad.server.api.v0.auth.google_api import google_callback

    # Mock httpx responses
    mock_client_instance = AsyncMock()
    mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

    # Mock token exchange response
    token_response = Mock()
    token_response.json.return_value = {"access_token": "test_token"}
    mock_client_instance.post.return_value = token_response

    # Mock user info response with unverified email
    user_response = Mock()
    user_response.json.return_value = {
        "email": "test@example.com",
        "verified_email": False,
    }
    mock_client_instance.get.return_value = user_response

    with pytest.raises(HTTPException) as exc_info:
        await google_callback(
            code="test_code",
            posthog=mock_posthog,
            settings=mock_settings,
            session=mock_session,
            request=mock_request,
        )

    assert exc_info.value.status_code == 400
    assert "Email address is not verified" in str(exc_info.value.detail)


@pytest.mark.asyncio
@patch("httpx.AsyncClient")
@patch("lilypad.server.api.v0.auth.github_api.handle_user")
async def test_github_callback_success(
    mock_handle_user,
    mock_httpx_client,
    mock_posthog,
    mock_settings,
    mock_session,
    mock_request,
):
    """Test successful GitHub OAuth callback."""
    from lilypad.server.api.v0.auth.github_api import github_callback

    # Setup mocks
    user_uuid = uuid4()
    org_uuid = uuid4()
    mock_user = UserPublic(
        uuid=user_uuid,
        email="test@example.com",
        first_name="Test",
        last_name="User",
        active_organization_uuid=org_uuid,
    )
    mock_handle_user.return_value = mock_user

    # Mock httpx responses
    mock_client_instance = AsyncMock()
    mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance

    # Mock token exchange response
    token_response = Mock()
    token_response.json.return_value = {"access_token": "test_token"}
    token_response.raise_for_status = Mock()
    mock_client_instance.post.return_value = token_response

    # Mock user info response
    user_response = Mock()
    user_response.json.return_value = {"email": "test@example.com", "name": "Test User"}
    user_response.raise_for_status = Mock()
    mock_client_instance.get.return_value = user_response

    # Call the function
    result = await github_callback(
        code="test_code",
        posthog=mock_posthog,
        settings=mock_settings,
        session=mock_session,
        request=mock_request,
    )

    # Assertions
    assert result == mock_user
    mock_handle_user.assert_called_once()


@pytest.mark.asyncio
async def test_github_callback_no_code(
    mock_posthog, mock_settings, mock_session, mock_request
):
    """Test GitHub callback with no authorization code."""
    from lilypad.server.api.v0.auth.github_api import github_callback

    with pytest.raises(HTTPException) as exc_info:
        await github_callback(
            code="",
            posthog=mock_posthog,
            settings=mock_settings,
            session=mock_session,
            request=mock_request,
        )

    assert exc_info.value.status_code == 400
    assert "No authorization code provided" in str(exc_info.value.detail)


@patch("lilypad.server.api.v0.auth.utils.create_jwt_token")
@patch("lilypad.server.api.v0.auth.utils.OrganizationService")
def test_handle_user_existing(
    mock_org_service_class, mock_create_jwt, mock_session, mock_posthog, mock_request
):
    """Test handle_user for an existing user."""
    from lilypad.server.api.v0.auth.utils import handle_user

    # Setup mocks
    mock_create_jwt.return_value = "test_jwt_token"

    # Mock existing user
    existing_user_uuid = uuid4()
    existing_org_uuid = uuid4()
    existing_user = UserTable(
        uuid=existing_user_uuid,
        email="existing@example.com",
        first_name="Existing",
        last_name="User",
        active_organization_uuid=existing_org_uuid,
    )

    # Mock session.exec to return existing user
    mock_result = Mock()
    mock_result.first.return_value = existing_user
    mock_session.exec.return_value = mock_result

    # Call handle_user
    result = handle_user(
        name="Existing",
        email="existing@example.com",
        last_name="User",
        session=mock_session,
        posthog=mock_posthog,
        request=mock_request,
    )

    # Verify result
    assert result.email == "existing@example.com"
    assert result.access_token == "test_jwt_token"
    mock_create_jwt.assert_called_once()


@patch("lilypad.server.api.v0.auth.utils.create_new_user")
def test_handle_user_new(
    mock_create_new_user, mock_session, mock_posthog, mock_request
):
    """Test handle_user for a new user."""
    from lilypad.server.api.v0.auth.utils import handle_user

    # Mock session.exec to return None (no existing user)
    mock_result = Mock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    # Mock create_new_user
    new_user_uuid = uuid4()
    new_org_uuid = uuid4()
    new_user = UserPublic(
        uuid=new_user_uuid,
        email="new@example.com",
        first_name="New",
        last_name="User",
        active_organization_uuid=new_org_uuid,
        access_token="new_jwt_token",
    )
    mock_create_new_user.return_value = new_user

    # Call handle_user
    result = handle_user(
        name="New",
        email="new@example.com",
        last_name="User",
        session=mock_session,
        posthog=mock_posthog,
        request=mock_request,
    )

    # Verify result
    assert result == new_user
    mock_create_new_user.assert_called_once_with(
        name="New",
        email="new@example.com",
        last_name="User",
        session=mock_session,
        posthog=mock_posthog,
    )
