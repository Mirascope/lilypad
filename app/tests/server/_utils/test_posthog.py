"""Tests for PostHog utility functions and middleware."""

from unittest.mock import AsyncMock, Mock, patch

import pytest
from fastapi import FastAPI
from fastapi.routing import APIRoute

from lilypad.server._utils.posthog import (
    PosthogMiddleware,
    get_posthog_client,
    setup_posthog_middleware,
)


def test_get_posthog_client():
    """Test getting PostHog client with settings."""
    # Clear the cache first
    get_posthog_client.cache_clear()

    with patch("lilypad.server._utils.posthog.get_settings") as mock_get_settings:
        mock_settings = Mock()
        mock_settings.posthog_api_key = "test-api-key"
        mock_settings.posthog_host = "https://app.posthog.com"
        mock_get_settings.return_value = mock_settings

        with patch(
            "lilypad.server._utils.posthog.posthog.Posthog"
        ) as mock_posthog_class:
            mock_client = Mock()
            mock_posthog_class.return_value = mock_client

            client = get_posthog_client()

            mock_posthog_class.assert_called_once_with(
                api_key="",
                project_api_key="test-api-key",
                host="https://app.posthog.com",
                disabled=False,
            )
            assert client == mock_client


def test_get_posthog_client_disabled():
    """Test PostHog client is disabled when no API key or host."""
    # Clear the cache first
    get_posthog_client.cache_clear()

    with patch("lilypad.server._utils.posthog.get_settings") as mock_get_settings:
        mock_settings = Mock()
        mock_settings.posthog_api_key = None
        mock_settings.posthog_host = None
        mock_get_settings.return_value = mock_settings

        with patch(
            "lilypad.server._utils.posthog.posthog.Posthog"
        ) as mock_posthog_class:
            get_posthog_client()

            mock_posthog_class.assert_called_once_with(
                api_key="",
                project_api_key=None,
                host=None,
                disabled=True,
            )


def test_get_posthog_client_cached():
    """Test that PostHog client is cached."""
    # Clear the cache first
    get_posthog_client.cache_clear()

    with patch("lilypad.server._utils.posthog.get_settings") as mock_get_settings:
        mock_settings = Mock()
        mock_settings.posthog_api_key = "test-key"
        mock_settings.posthog_host = "https://app.posthog.com"
        mock_get_settings.return_value = mock_settings

        with patch(
            "lilypad.server._utils.posthog.posthog.Posthog"
        ) as mock_posthog_class:
            # Call twice
            client1 = get_posthog_client()
            client2 = get_posthog_client()

            # Should only create client once due to caching
            assert mock_posthog_class.call_count == 1
            assert client1 == client2


def test_posthog_middleware_init():
    """Test PostHog middleware initialization."""
    exclude_paths = ["/health", "/metrics"]

    def should_capture(req):
        return True

    with patch("lilypad.server._utils.posthog.get_posthog_client") as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        middleware = PosthogMiddleware(
            exclude_paths=exclude_paths, should_capture=should_capture
        )

        assert middleware.exclude_paths == exclude_paths
        assert middleware.should_capture == should_capture
        assert middleware.posthog == mock_client


def test_posthog_middleware_get_base_properties():
    """Test getting base properties for PostHog events."""
    with patch("lilypad.server._utils.posthog.get_posthog_client"):
        middleware = PosthogMiddleware([], lambda req: True)

        # Create mock request
        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.__str__ = Mock(return_value="https://example.com/api/test")
        mock_request.method = "POST"
        mock_request.headers = {
            "user-agent": "TestAgent/1.0",
            "referer": "https://example.com/dashboard",
        }

        properties = middleware.get_base_properties(mock_request)

        assert properties == {
            "path": "https://example.com/api/test",
            "method": "POST",
            "user_agent": "TestAgent/1.0",
            "referer": "https://example.com/dashboard",
        }


def test_posthog_middleware_get_base_properties_missing_headers():
    """Test getting base properties when headers are missing."""
    with patch("lilypad.server._utils.posthog.get_posthog_client"):
        middleware = PosthogMiddleware([], lambda req: True)

        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.__str__ = Mock(return_value="https://example.com/api/test")
        mock_request.method = "GET"
        mock_request.headers = {}  # No headers

        properties = middleware.get_base_properties(mock_request)

        assert properties == {
            "path": "https://example.com/api/test",
            "method": "GET",
            "user_agent": None,
            "referer": None,
        }


@pytest.mark.asyncio
async def test_posthog_middleware_excluded_path():
    """Test middleware skips excluded paths."""
    exclude_paths = ["/health", "/metrics"]

    with patch("lilypad.server._utils.posthog.get_posthog_client"):
        middleware = PosthogMiddleware(exclude_paths, lambda req: True)

        # Mock request to excluded path
        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.path = "/health"

        # Mock call_next
        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)

        result = await middleware(mock_request, call_next)

        assert result == mock_response
        call_next.assert_called_once_with(mock_request)


@pytest.mark.asyncio
async def test_posthog_middleware_should_not_capture():
    """Test middleware skips when should_capture returns False."""
    with patch("lilypad.server._utils.posthog.get_posthog_client"):
        middleware = PosthogMiddleware([], lambda req: False)  # Always False

        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.method = "POST"

        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)

        result = await middleware(mock_request, call_next)

        assert result == mock_response
        call_next.assert_called_once_with(mock_request)


@pytest.mark.asyncio
async def test_posthog_middleware_options_method():
    """Test middleware skips OPTIONS requests."""
    with patch("lilypad.server._utils.posthog.get_posthog_client"):
        middleware = PosthogMiddleware([], lambda req: True)

        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.method = "OPTIONS"

        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)

        result = await middleware(mock_request, call_next)

        assert result == mock_response
        call_next.assert_called_once_with(mock_request)


@pytest.mark.asyncio
async def test_posthog_middleware_get_method():
    """Test middleware skips GET requests."""
    with patch("lilypad.server._utils.posthog.get_posthog_client"):
        middleware = PosthogMiddleware([], lambda req: True)

        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.method = "GET"

        mock_response = Mock()
        call_next = AsyncMock(return_value=mock_response)

        result = await middleware(mock_request, call_next)

        assert result == mock_response
        call_next.assert_called_once_with(mock_request)


@pytest.mark.asyncio
async def test_posthog_middleware_capture_with_user():
    """Test middleware captures events with authenticated user."""
    with patch("lilypad.server._utils.posthog.get_posthog_client") as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        middleware = PosthogMiddleware([], lambda req: True)

        # Mock user
        mock_user = Mock()
        mock_user.email = "test@example.com"

        # Mock request
        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.method = "POST"
        mock_request.state = Mock()
        mock_request.state.user = mock_user
        mock_request.headers = {"user-agent": "TestAgent"}

        # Mock route
        mock_endpoint = Mock()
        mock_endpoint.__name__ = "test_endpoint"
        mock_route = Mock(spec=APIRoute)
        mock_route.endpoint = mock_endpoint
        mock_request.scope = {"route": mock_route}

        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        call_next = AsyncMock(return_value=mock_response)

        with patch("time.time", side_effect=[100.0, 100.5]):  # 0.5 second duration
            result = await middleware(mock_request, call_next)

        assert result == mock_response

        # Verify PostHog capture was called
        mock_client.capture.assert_called_once()
        call_args = mock_client.capture.call_args

        assert call_args[1]["distinct_id"] == "test@example.com"
        assert call_args[1]["event"] == "test_endpoint"
        assert call_args[1]["properties"]["status_code"] == 200
        assert call_args[1]["properties"]["duration"] == 0.5


@pytest.mark.asyncio
async def test_posthog_middleware_capture_anonymous_user():
    """Test middleware captures events with anonymous user."""
    with patch("lilypad.server._utils.posthog.get_posthog_client") as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        middleware = PosthogMiddleware([], lambda req: True)

        # Mock request with state that raises AttributeError when accessing user
        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.method = "POST"

        # Create state mock that raises AttributeError
        mock_state = Mock()
        del mock_state.user  # Remove user attribute to cause AttributeError
        mock_request.state = mock_state

        mock_request.headers = {}

        # Mock route
        mock_endpoint = Mock()
        mock_endpoint.__name__ = "test_endpoint"
        mock_route = Mock(spec=APIRoute)
        mock_route.endpoint = mock_endpoint
        mock_request.scope = {"route": mock_route}

        mock_response = Mock()
        mock_response.status_code = 200
        call_next = AsyncMock(return_value=mock_response)

        await middleware(mock_request, call_next)

        # Verify anonymous user is used
        call_args = mock_client.capture.call_args
        assert call_args[1]["distinct_id"] == "anonymous"


@pytest.mark.asyncio
async def test_posthog_middleware_capture_user_without_email():
    """Test middleware captures events with user that has no email."""
    with patch("lilypad.server._utils.posthog.get_posthog_client") as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        middleware = PosthogMiddleware([], lambda req: True)

        # Mock user without email
        mock_user = Mock()
        mock_user.email = None

        # Mock request
        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.method = "POST"
        mock_request.state = Mock()
        mock_request.state.user = mock_user
        mock_request.headers = {}

        # Mock route
        mock_endpoint = Mock()
        mock_endpoint.__name__ = "test_endpoint"
        mock_route = Mock(spec=APIRoute)
        mock_route.endpoint = mock_endpoint
        mock_request.scope = {"route": mock_route}

        mock_response = Mock()
        mock_response.status_code = 200
        call_next = AsyncMock(return_value=mock_response)

        await middleware(mock_request, call_next)

        # Verify user.email is used as distinct_id (None in this case, but that's how the code works)
        call_args = mock_client.capture.call_args
        assert call_args[1]["distinct_id"] is None


@pytest.mark.asyncio
async def test_posthog_middleware_capture_non_api_route():
    """Test middleware captures events for non-APIRoute routes."""
    with patch("lilypad.server._utils.posthog.get_posthog_client") as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        middleware = PosthogMiddleware([], lambda req: True)

        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.method = "POST"
        mock_request.state = Mock()
        mock_request.state.user = None
        mock_request.headers = {}

        # Mock non-APIRoute
        mock_route = Mock()  # Not APIRoute
        mock_request.scope = {"route": mock_route}

        mock_response = Mock()
        mock_response.status_code = 200
        call_next = AsyncMock(return_value=mock_response)

        await middleware(mock_request, call_next)

        # Verify generic event name is used
        call_args = mock_client.capture.call_args
        assert call_args[1]["event"] == "api_request"


@pytest.mark.asyncio
async def test_posthog_middleware_capture_no_route():
    """Test middleware captures events when no route in scope."""
    with patch("lilypad.server._utils.posthog.get_posthog_client") as mock_get_client:
        mock_client = Mock()
        mock_get_client.return_value = mock_client

        middleware = PosthogMiddleware([], lambda req: True)

        mock_request = Mock()
        mock_request.url = Mock()
        mock_request.url.path = "/api/test"
        mock_request.method = "POST"
        mock_request.state = Mock()
        mock_request.state.user = None
        mock_request.headers = {}
        mock_request.scope = {}  # No route

        mock_response = Mock()
        mock_response.status_code = 200
        call_next = AsyncMock(return_value=mock_response)

        await middleware(mock_request, call_next)

        # Verify generic event name is used
        call_args = mock_client.capture.call_args
        assert call_args[1]["event"] == "api_request"


def test_setup_posthog_middleware():
    """Test setting up PostHog middleware on FastAPI app."""
    app = FastAPI()
    exclude_paths = ["/health"]

    def should_capture(req):
        return True

    with patch(
        "lilypad.server._utils.posthog.PosthogMiddleware"
    ) as mock_middleware_class:
        mock_middleware = Mock()
        mock_middleware_class.return_value = mock_middleware

        # Mock the middleware method
        app.middleware = Mock()
        mock_middleware_decorator = Mock()
        app.middleware.return_value = mock_middleware_decorator

        setup_posthog_middleware(app, exclude_paths, should_capture)

        # Verify middleware was created with correct parameters
        mock_middleware_class.assert_called_once_with(
            exclude_paths=exclude_paths, should_capture=should_capture
        )

        # Verify middleware was added to app
        app.middleware.assert_called_once_with("http")
        mock_middleware_decorator.assert_called_once_with(mock_middleware)
