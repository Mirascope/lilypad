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
def mock_request():
    """Mock request object."""
    request = Mock()
    request.client = Mock()
    request.client.host = "127.0.0.1"
    return request


@pytest.fixture
def oauth_test_user():
    """Create a test user for OAuth tests."""
    return UserPublic(
        uuid=uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        active_organization_uuid=uuid4(),
    )


# ===== Parameterized OAuth Callback Tests =====

@pytest.mark.parametrize("provider,callback_module,user_info,expected_handle_call", [
    # Google OAuth Success
    ("google", "google_api", {
        "email": "test@example.com",
        "given_name": "Test",
        "family_name": "User",
        "verified_email": True,
    }, {
        "name": "Test",
        "email": "test@example.com",
        "last_name": "User",
    }),
    # GitHub OAuth Success
    ("github", "github_api", {
        "email": "test@example.com",
        "name": "Test User",
    }, {
        "email": "test@example.com",
        "name": "Test User",
    }),
])
@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_oauth_callback_success(
    mock_httpx_client,
    provider,
    callback_module,
    user_info,
    expected_handle_call,
    oauth_test_user,
    mock_posthog,
    mock_settings,
    db_session,
    mock_request,
):
    """Test successful OAuth callbacks for different providers."""
    # Dynamic import based on provider
    module = __import__(
        f"lilypad.server.api.v0.auth.{callback_module}",
        fromlist=[f"{provider}_callback"]
    )
    callback_func = getattr(module, f"{provider}_callback")
    
    # Mock handle_user
    with patch(f"lilypad.server.api.v0.auth.{callback_module}.handle_user") as mock_handle_user:
        mock_handle_user.return_value = oauth_test_user
        
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
        user_response.json.return_value = user_info
        user_response.raise_for_status = Mock()
        mock_client_instance.get.return_value = user_response
        
        # Call the function
        result = await callback_func(
            code="test_code",
            posthog=mock_posthog,
            settings=mock_settings,
            session=db_session,
            request=mock_request,
        )
        
        # Assertions
        assert result == oauth_test_user
        mock_handle_user.assert_called_once()
        
        # Verify handle_user was called with expected parameters
        call_args = mock_handle_user.call_args.kwargs
        for key, value in expected_handle_call.items():
            assert call_args.get(key) == value


# ===== Parameterized OAuth Error Tests =====

@pytest.mark.parametrize("provider,callback_module,error_scenario,expected_error", [
    # No code provided
    ("google", "google_api", "no_code", "No authorization code provided"),
    ("github", "github_api", "no_code", "No authorization code provided"),
    # Email not verified (Google only)
    ("google", "google_api", "email_not_verified", "Email address is not verified"),
])
@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_oauth_callback_errors(
    mock_httpx_client,
    provider,
    callback_module,
    error_scenario,
    expected_error,
    mock_posthog,
    mock_settings,
    db_session,
    mock_request,
):
    """Test OAuth callback error scenarios."""
    # Dynamic import
    module = __import__(
        f"lilypad.server.api.v0.auth.{callback_module}",
        fromlist=[f"{provider}_callback"]
    )
    callback_func = getattr(module, f"{provider}_callback")
    
    if error_scenario == "no_code":
        # Test with no authorization code
        with pytest.raises(HTTPException) as exc_info:
            await callback_func(
                code="",
                posthog=mock_posthog,
                settings=mock_settings,
                session=db_session,
                request=mock_request,
            )
        assert exc_info.value.status_code == 400
        assert expected_error in str(exc_info.value.detail)
        
    elif error_scenario == "email_not_verified":
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
            await callback_func(
                code="test_code",
                posthog=mock_posthog,
                settings=mock_settings,
                session=db_session,
                request=mock_request,
            )
        assert exc_info.value.status_code == 400
        assert expected_error in str(exc_info.value.detail)


# ===== Parameterized handle_user Tests =====

@pytest.mark.parametrize("user_exists,expected_action", [
    (True, "login_existing"),
    (False, "create_new"),
])
@patch("lilypad.server.api.v0.auth.utils.create_jwt_token")
@patch("lilypad.server.api.v0.auth.utils.OrganizationService")
@patch("lilypad.server.api.v0.auth.utils.create_new_user")
def test_handle_user(
    mock_create_new_user,
    mock_org_service_class,
    mock_create_jwt,
    user_exists,
    expected_action,
    db_session,
    mock_posthog,
    mock_request,
):
    """Test handle_user for existing and new users."""
    from lilypad.server.api.v0.auth.utils import handle_user
    
    mock_create_jwt.return_value = "test_jwt_token"
    
    if user_exists:
        # Mock existing user
        existing_user = UserTable(
            uuid=uuid4(),
            email="existing@example.com",
            first_name="Existing",
            last_name="User",
            active_organization_uuid=uuid4(),
        )
        mock_result = Mock()
        mock_result.first.return_value = existing_user
        db_session.exec = Mock(return_value=mock_result)
        
        # Call handle_user
        result = handle_user(
            name="Existing",
            email="existing@example.com",
            last_name="User",
            session=db_session,
            posthog=mock_posthog,
            request=mock_request,
        )
        
        # Verify login behavior
        assert result.email == "existing@example.com"
        assert result.access_token == "test_jwt_token"
        mock_create_jwt.assert_called_once()
        mock_create_new_user.assert_not_called()
        
    else:
        # Mock no existing user
        mock_result = Mock()
        mock_result.first.return_value = None
        db_session.exec = Mock(return_value=mock_result)
        
        # Mock create_new_user
        new_user = UserPublic(
            uuid=uuid4(),
            email="new@example.com",
            first_name="New",
            last_name="User",
            active_organization_uuid=uuid4(),
            access_token="new_jwt_token",
        )
        mock_create_new_user.return_value = new_user
        
        # Call handle_user
        result = handle_user(
            name="New",
            email="new@example.com",
            last_name="User",
            session=db_session,
            posthog=mock_posthog,
            request=mock_request,
        )
        
        # Verify creation behavior
        assert result == new_user
        mock_create_new_user.assert_called_once_with(
            name="New",
            email="new@example.com",
            last_name="User",
            session=db_session,
            posthog=mock_posthog,
        )


# ===== Parameterized Token Exchange Error Tests =====

@pytest.mark.parametrize("provider,error_code,error_message", [
    ("google", 401, "Invalid client credentials"),
    ("github", 403, "Bad verification code"),
    ("google", 500, "Internal server error"),
    ("github", 500, "Internal server error"),
])
@pytest.mark.asyncio
@patch("httpx.AsyncClient")
async def test_oauth_token_exchange_errors(
    mock_httpx_client,
    provider,
    error_code,
    error_message,
    mock_posthog,
    mock_settings,
    db_session,
    mock_request,
):
    """Test OAuth token exchange error handling."""
    # Dynamic import
    callback_module = f"{provider}_api"
    module = __import__(
        f"lilypad.server.api.v0.auth.{callback_module}",
        fromlist=[f"{provider}_callback"]
    )
    callback_func = getattr(module, f"{provider}_callback")
    
    # Mock httpx to raise an error during token exchange
    mock_client_instance = AsyncMock()
    mock_httpx_client.return_value.__aenter__.return_value = mock_client_instance
    
    # Mock error response
    mock_client_instance.post.side_effect = Exception(f"HTTP {error_code}: {error_message}")
    
    with pytest.raises(Exception) as exc_info:
        await callback_func(
            code="test_code",
            posthog=mock_posthog,
            settings=mock_settings,
            session=db_session,
            request=mock_request,
        )
    
    assert error_message in str(exc_info.value)


