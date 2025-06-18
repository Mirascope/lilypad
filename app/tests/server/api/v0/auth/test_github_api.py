"""Tests for GitHub OAuth API endpoints."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import HTTPException
from httpx import RequestError

from lilypad.server.api.v0.auth.github_api import github_callback


@pytest.mark.asyncio
async def test_github_callback_success_with_email_in_profile():
    """Test successful GitHub callback with email in user profile."""
    # Mock dependencies
    mock_posthog = Mock()
    mock_settings = Mock()
    mock_settings.github_client_id = "test_client_id"
    mock_settings.github_client_secret = "test_client_secret"
    mock_settings.client_url = "http://localhost:3000"

    mock_session = Mock()
    mock_request = Mock()

    # Mock httpx responses
    token_response_data = {"access_token": "test_access_token"}
    user_response_data = {
        "email": "test@example.com",
        "name": "John Doe",
        "login": "johndoe",
    }

    mock_token_response = Mock()
    mock_token_response.json.return_value = token_response_data

    mock_user_response = Mock()
    mock_user_response.json.return_value = user_response_data

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_token_response
    mock_client.get.return_value = mock_user_response

    with (
        patch(
            "lilypad.server.api.v0.auth.github_api.httpx.AsyncClient"
        ) as mock_httpx_client,
        patch("lilypad.server.api.v0.auth.github_api.handle_user") as mock_handle_user,
    ):
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        mock_expected_user = Mock()
        mock_handle_user.return_value = mock_expected_user

        # Test the callback
        result = await github_callback(
            code="test_code",
            posthog=mock_posthog,
            settings=mock_settings,
            session=mock_session,
            request=mock_request,
        )

        # Assertions
        mock_client.post.assert_called_once_with(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": "test_client_id",
                "client_secret": "test_client_secret",
                "code": "test_code",
                "redirect_uri": "http://localhost:3000/auth/callback",
            },
            headers={"Accept": "application/json"},
        )

        mock_client.get.assert_called_once_with(
            "https://api.github.com/user",
            headers={
                "Authorization": "Bearer test_access_token",
                "Accept": "application/json",
            },
        )

        mock_handle_user.assert_called_once_with(
            name="John Doe",
            email="test@example.com",
            last_name=None,
            session=mock_session,
            posthog=mock_posthog,
            request=mock_request,
        )

        assert result == mock_expected_user


@pytest.mark.asyncio
async def test_github_callback_success_with_primary_email_from_emails_api():
    """Test successful GitHub callback when email comes from emails API with primary email."""
    # Mock dependencies
    mock_posthog = Mock()
    mock_settings = Mock()
    mock_settings.github_client_id = "test_client_id"
    mock_settings.github_client_secret = "test_client_secret"
    mock_settings.client_url = "http://localhost:3000"

    mock_session = Mock()
    mock_request = Mock()

    # Mock httpx responses
    token_response_data = {"access_token": "test_access_token"}
    user_response_data = {
        "email": None,  # No email in profile
        "name": "John Doe",
        "login": "johndoe",
    }
    user_emails_data = [
        {"email": "secondary@example.com", "primary": False},
        {"email": "primary@example.com", "primary": True},
    ]

    mock_token_response = Mock()
    mock_token_response.json.return_value = token_response_data

    mock_user_response = Mock()
    mock_user_response.json.return_value = user_response_data

    mock_emails_response = Mock()
    mock_emails_response.json.return_value = user_emails_data

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_token_response
    # First call returns user data, second call returns emails
    mock_client.get.side_effect = [mock_user_response, mock_emails_response]

    with (
        patch(
            "lilypad.server.api.v0.auth.github_api.httpx.AsyncClient"
        ) as mock_httpx_client,
        patch("lilypad.server.api.v0.auth.github_api.handle_user") as mock_handle_user,
    ):
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        mock_expected_user = Mock()
        mock_handle_user.return_value = mock_expected_user

        # Test the callback
        result = await github_callback(
            code="test_code",
            posthog=mock_posthog,
            settings=mock_settings,
            session=mock_session,
            request=mock_request,
        )

        # Assertions
        assert mock_client.get.call_count == 2
        # Second call should be for emails
        mock_client.get.assert_any_call(
            "https://api.github.com/user/emails",
            headers={
                "Authorization": "Bearer test_access_token",
                "Accept": "application/json",
            },
        )

        mock_handle_user.assert_called_once_with(
            name="John Doe",
            email="primary@example.com",  # Should use primary email
            last_name=None,
            session=mock_session,
            posthog=mock_posthog,
            request=mock_request,
        )

        assert result == mock_expected_user


@pytest.mark.asyncio
async def test_github_callback_success_with_first_email_when_no_primary():
    """Test successful GitHub callback when no primary email, uses first email."""
    # Mock dependencies
    mock_posthog = Mock()
    mock_settings = Mock()
    mock_settings.github_client_id = "test_client_id"
    mock_settings.github_client_secret = "test_client_secret"
    mock_settings.client_url = "http://localhost:3000"

    mock_session = Mock()
    mock_request = Mock()

    # Mock httpx responses
    token_response_data = {"access_token": "test_access_token"}
    user_response_data = {
        "email": None,  # No email in profile
        "name": "John Doe",
        "login": "johndoe",
    }
    user_emails_data = [
        {"email": "first@example.com", "primary": False},
        {"email": "second@example.com", "primary": False},
    ]

    mock_token_response = Mock()
    mock_token_response.json.return_value = token_response_data

    mock_user_response = Mock()
    mock_user_response.json.return_value = user_response_data

    mock_emails_response = Mock()
    mock_emails_response.json.return_value = user_emails_data

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_token_response
    mock_client.get.side_effect = [mock_user_response, mock_emails_response]

    with (
        patch(
            "lilypad.server.api.v0.auth.github_api.httpx.AsyncClient"
        ) as mock_httpx_client,
        patch("lilypad.server.api.v0.auth.github_api.handle_user") as mock_handle_user,
    ):
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        mock_expected_user = Mock()
        mock_handle_user.return_value = mock_expected_user

        # Test the callback
        result = await github_callback(
            code="test_code",
            posthog=mock_posthog,
            settings=mock_settings,
            session=mock_session,
            request=mock_request,
        )

        # Assertions
        mock_handle_user.assert_called_once_with(
            name="John Doe",
            email="first@example.com",  # Should use first email
            last_name=None,
            session=mock_session,
            posthog=mock_posthog,
            request=mock_request,
        )

        assert result == mock_expected_user


@pytest.mark.asyncio
async def test_github_callback_success_with_fallback_name():
    """Test successful GitHub callback with fallback name logic."""
    # Mock dependencies
    mock_posthog = Mock()
    mock_settings = Mock()
    mock_settings.github_client_id = "test_client_id"
    mock_settings.github_client_secret = "test_client_secret"
    mock_settings.client_url = "http://localhost:3000"

    mock_session = Mock()
    mock_request = Mock()

    # Mock httpx responses - no name, fall back to login
    token_response_data = {"access_token": "test_access_token"}
    user_response_data = {
        "email": "test@example.com",
        "first_name": None,
        "name": None,
        "login": "johndoe123",
    }

    mock_token_response = Mock()
    mock_token_response.json.return_value = token_response_data

    mock_user_response = Mock()
    mock_user_response.json.return_value = user_response_data

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_token_response
    mock_client.get.return_value = mock_user_response

    with (
        patch(
            "lilypad.server.api.v0.auth.github_api.httpx.AsyncClient"
        ) as mock_httpx_client,
        patch("lilypad.server.api.v0.auth.github_api.handle_user") as mock_handle_user,
    ):
        mock_httpx_client.return_value.__aenter__.return_value = mock_client
        mock_expected_user = Mock()
        mock_handle_user.return_value = mock_expected_user

        # Test the callback
        result = await github_callback(
            code="test_code",
            posthog=mock_posthog,
            settings=mock_settings,
            session=mock_session,
            request=mock_request,
        )

        # Assertions
        mock_handle_user.assert_called_once_with(
            name="johndoe123",  # Should use login as fallback
            email="test@example.com",
            last_name=None,
            session=mock_session,
            posthog=mock_posthog,
            request=mock_request,
        )

        assert result == mock_expected_user


@pytest.mark.asyncio
async def test_github_callback_no_code():
    """Test GitHub callback with no authorization code."""
    mock_posthog = Mock()
    mock_settings = Mock()
    mock_session = Mock()
    mock_request = Mock()

    # Test with empty code
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


@pytest.mark.asyncio
async def test_github_callback_oauth_error():
    """Test GitHub callback with OAuth error from GitHub."""
    # Mock dependencies
    mock_posthog = Mock()
    mock_settings = Mock()
    mock_settings.github_client_id = "test_client_id"
    mock_settings.github_client_secret = "test_client_secret"
    mock_settings.client_url = "http://localhost:3000"

    mock_session = Mock()
    mock_request = Mock()

    # Mock error response from GitHub
    token_response_data = {
        "error": "invalid_request",
        "error_description": "Bad request",
    }

    mock_token_response = Mock()
    mock_token_response.json.return_value = token_response_data

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_token_response

    with patch(
        "lilypad.server.api.v0.auth.github_api.httpx.AsyncClient"
    ) as mock_httpx_client:
        mock_httpx_client.return_value.__aenter__.return_value = mock_client

        # Test the callback
        with pytest.raises(HTTPException) as exc_info:
            await github_callback(
                code="test_code",
                posthog=mock_posthog,
                settings=mock_settings,
                session=mock_session,
                request=mock_request,
            )

        assert exc_info.value.status_code == 400
        assert "GitHub OAuth error: invalid_request" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_github_callback_no_email_found():
    """Test GitHub callback when no email can be found."""
    # Mock dependencies
    mock_posthog = Mock()
    mock_settings = Mock()
    mock_settings.github_client_id = "test_client_id"
    mock_settings.github_client_secret = "test_client_secret"
    mock_settings.client_url = "http://localhost:3000"

    mock_session = Mock()
    mock_request = Mock()

    # Mock httpx responses
    token_response_data = {"access_token": "test_access_token"}
    user_response_data = {
        "email": None,  # No email in profile
        "name": "John Doe",
        "login": "johndoe",
    }
    user_emails_data = []  # No emails returned

    mock_token_response = Mock()
    mock_token_response.json.return_value = token_response_data

    mock_user_response = Mock()
    mock_user_response.json.return_value = user_response_data

    mock_emails_response = Mock()
    mock_emails_response.json.return_value = user_emails_data

    mock_client = AsyncMock()
    mock_client.post.return_value = mock_token_response
    mock_client.get.side_effect = [mock_user_response, mock_emails_response]

    with patch(
        "lilypad.server.api.v0.auth.github_api.httpx.AsyncClient"
    ) as mock_httpx_client:
        mock_httpx_client.return_value.__aenter__.return_value = mock_client

        # Test the callback
        with pytest.raises(HTTPException) as exc_info:
            await github_callback(
                code="test_code",
                posthog=mock_posthog,
                settings=mock_settings,
                session=mock_session,
                request=mock_request,
            )

        assert exc_info.value.status_code == 400
        assert "No email address found in GitHub account" in str(exc_info.value.detail)


@pytest.mark.asyncio
async def test_github_callback_request_error():
    """Test GitHub callback with HTTP request error."""
    # Mock dependencies
    mock_posthog = Mock()
    mock_settings = Mock()
    mock_settings.github_client_id = "test_client_id"
    mock_settings.github_client_secret = "test_client_secret"
    mock_settings.client_url = "http://localhost:3000"

    mock_session = Mock()
    mock_request = Mock()

    mock_client = AsyncMock()
    mock_client.post.side_effect = RequestError("Connection failed")

    with patch(
        "lilypad.server.api.v0.auth.github_api.httpx.AsyncClient"
    ) as mock_httpx_client:
        mock_httpx_client.return_value.__aenter__.return_value = mock_client

        # Test the callback
        with pytest.raises(HTTPException) as exc_info:
            await github_callback(
                code="test_code",
                posthog=mock_posthog,
                settings=mock_settings,
                session=mock_session,
                request=mock_request,
            )

        assert exc_info.value.status_code == 500
        assert "Error communicating with GitHub" in str(exc_info.value.detail)
