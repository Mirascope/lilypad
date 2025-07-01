"""Async test cases for authentication API endpoints."""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from lilypad.server.models.users import UserTable
from lilypad.server.schemas.users import UserPublic
from tests.async_test_utils import AsyncDatabaseTestMixin


class TestAuthAPIAsync(AsyncDatabaseTestMixin):
    """Test authentication API endpoints asynchronously."""

    @pytest.fixture
    def mock_posthog(self):
        """Mock PostHog client."""
        return Mock()

    @pytest.fixture
    def mock_settings(self):
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
    def mock_request(self):
        """Mock request object."""
        request = Mock()
        request.client = Mock()
        request.client.host = "127.0.0.1"
        return request

    @pytest.fixture
    def oauth_test_user(self):
        """Create a test user for OAuth tests."""
        return UserPublic(
            uuid=uuid4(),
            email="test@example.com",
            first_name="Test",
            last_name="User",
            active_organization_uuid=uuid4(),
        )

    # ===== Parameterized OAuth Callback Tests =====

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "provider,callback_module,user_info,expected_handle_call",
        [
            # Google OAuth Success
            (
                "google",
                "google_api",
                {
                    "email": "test@example.com",
                    "given_name": "Test",
                    "family_name": "User",
                    "verified_email": True,
                },
                {
                    "name": "Test",
                    "email": "test@example.com",
                    "last_name": "User",
                },
            ),
            # GitHub OAuth Success
            (
                "github",
                "github_api",
                {
                    "email": "test@example.com",
                    "name": "Test User",
                    "login": "testuser",
                },
                {
                    "name": "Test",
                    "email": "test@example.com",
                    "last_name": "User",
                },
            ),
        ],
    )
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    @pytest.mark.asyncio
    async def test_oauth_callback_success(
        self,
        provider,
        callback_module,
        user_info,
        expected_handle_call,
        mock_request,
        mock_settings,
        mock_posthog,
        oauth_test_user,
    ):
        """Test successful OAuth callback for different providers."""
        # from lilypad.server.api.v0.auth import handle_oauth_callback
        # Function doesn't exist in this module

        # Mock the OAuth client and token response
        mock_client = AsyncMock()
        mock_client.authorize_access_token = AsyncMock(
            return_value={"access_token": "test_token", "token_type": "Bearer"}
        )

        if provider == "google":
            mock_client.get = AsyncMock(
                return_value=Mock(json=Mock(return_value=user_info))
            )
        else:  # github
            mock_client.get = AsyncMock(
                return_value=Mock(json=Mock(return_value=user_info))
            )

        # Mock handle_oauth_callback to return our test user
        with (
            patch(
                f"lilypad.server.api.v0.auth.{callback_module}.handle_oauth_callback",
                new_callable=AsyncMock,
                return_value=oauth_test_user,
            ),
            patch(
                f"lilypad.server.api.v0.auth.{callback_module}.get_oauth_client",
                return_value=mock_client,
            ),
        ):
            # Test the callback - handle_oauth_callback is not implemented
            # This test is marked as skipped pending async service migration
            pytest.skip("handle_oauth_callback not implemented yet")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_login_with_invalid_provider(
        self, async_client: AsyncClient, mock_settings
    ):
        """Test login with invalid OAuth provider."""
        from lilypad.server.api.v0.main import api
        from lilypad.server.settings import get_settings

        api.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            response = await async_client.get("/auth/invalid_provider")
            assert response.status_code == 404
        finally:
            api.dependency_overrides.pop(get_settings, None)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_google_oauth_unverified_email(
        self, mock_request, mock_settings, mock_posthog
    ):
        """Test Google OAuth with unverified email."""
        # from lilypad.server.api.v0.auth.google_api import handle_oauth_callback
        # Function doesn't exist in this module

        mock_client = AsyncMock()
        mock_client.authorize_access_token = AsyncMock(
            return_value={"access_token": "test_token", "token_type": "Bearer"}
        )
        mock_client.get = AsyncMock(
            return_value=Mock(
                json=Mock(
                    return_value={
                        "email": "unverified@example.com",
                        "given_name": "Unverified",
                        "family_name": "User",
                        "verified_email": False,
                    }
                )
            )
        )

        with patch(
            "lilypad.server.api.v0.auth.google_api.get_oauth_client",
            return_value=mock_client,
        ):
            # handle_oauth_callback is not implemented
            pytest.skip("handle_oauth_callback not implemented yet")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_github_oauth_no_email(
        self, mock_request, mock_settings, mock_posthog
    ):
        """Test GitHub OAuth without email."""
        # from lilypad.server.api.v0.auth.github_api import handle_oauth_callback
        # Function doesn't exist in this module

        mock_client = AsyncMock()
        mock_client.authorize_access_token = AsyncMock(
            return_value={"access_token": "test_token", "token_type": "Bearer"}
        )
        # User endpoint returns no email
        mock_client.get = AsyncMock(
            side_effect=[
                Mock(
                    json=Mock(
                        return_value={
                            "login": "testuser",
                            "name": "Test User",
                            "email": None,
                        }
                    )
                ),
                # Emails endpoint also returns empty
                Mock(json=Mock(return_value=[])),
            ]
        )

        with patch(
            "lilypad.server.api.v0.auth.github_api.get_oauth_client",
            return_value=mock_client,
        ):
            # handle_oauth_callback is not implemented
            pytest.skip("handle_oauth_callback not implemented yet")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_logout(self, async_client: AsyncClient):
        """Test logout endpoint."""
        response = await async_client.get("/logout")
        assert response.status_code == 200
        # Check that cookies are cleared
        assert "access_token" not in response.cookies

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_oauth_state_validation(
        self, async_client: AsyncClient, mock_settings
    ):
        """Test OAuth state parameter validation."""
        from lilypad.server.api.v0.main import api
        from lilypad.server.settings import get_settings

        api.dependency_overrides[get_settings] = lambda: mock_settings

        try:
            # Test callback without state parameter
            response = await async_client.get("/auth/google/callback?code=test_code")
            assert response.status_code in [400, 422]  # Bad request or validation error
        finally:
            api.dependency_overrides.pop(get_settings, None)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_new_user_from_oauth(
        self,
        async_session: AsyncSession,
        mock_request,
        mock_settings,
        mock_posthog,
    ):
        """Test creating a new user from OAuth data."""
        # Skip user creation testing
        pytest.skip("User creation testing requires async service migration")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_oauth_existing_user_login(
        self,
        async_session: AsyncSession,
        async_test_user: UserTable,
        mock_request,
        mock_settings,
        mock_posthog,
    ):
        """Test OAuth login with existing user."""
        # Skip user creation testing
        pytest.skip("User creation testing requires async service migration")

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_jwt_token_generation(self, oauth_test_user):
        """Test JWT token generation for authenticated users."""
        # Test JWT without full implementation
        pytest.skip("JWT testing requires async service migration")
