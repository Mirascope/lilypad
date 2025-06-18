"""Tests for the settings API endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from fastapi.testclient import TestClient

from lilypad.server.api.v0.main import api
from lilypad.server.api.v0.settings_api import fetch_policy_versions, policy_cache
from lilypad.server.settings import get_settings


class _DummySettings:  # noqa: D401 (simple stub object)
    """Minimal stand-in for the real Settings object."""

    remote_client_url = "https://client.example.com"
    remote_api_url = "https://api.example.com"
    github_client_id = "dummy-github-id"
    google_client_id = "dummy-google-id"
    environment = "production"
    experimental = False
    privacy_version = "06-18-2025"
    tos_version = "06-18-2025"


@pytest.fixture(name="client")
def fixture_client() -> TestClient:  # type: ignore[misc]
    """Create a TestClient with the settings dependency overridden."""
    api.dependency_overrides[get_settings] = lambda: _DummySettings()  # type: ignore[arg-type]
    yield TestClient(api)  # type: ignore[misc]
    api.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def clear_policy_cache() -> None:
    """Clear the policy cache before each test."""
    policy_cache.clear()


@patch("lilypad.server.api.v0.settings_api.fetch_policy_versions")
def test_settings_endpoint_returns_expected_payload(
    mock_fetch_policy_versions: AsyncMock, client: TestClient
) -> None:
    """`/settings` should return all fields from SettingsPublic with correct values."""
    mock_fetch_policy_versions.return_value = {
        "privacyVersion": _DummySettings.privacy_version,
        "termsVersion": _DummySettings.tos_version,
    }

    response = client.get("/settings")
    assert response.status_code == 200

    payload = response.json()
    expected = {
        "remote_client_url": _DummySettings.remote_client_url,
        "remote_api_url": _DummySettings.remote_api_url,
        "github_client_id": _DummySettings.github_client_id,
        "google_client_id": _DummySettings.google_client_id,
        "environment": _DummySettings.environment,
        "experimental": _DummySettings.experimental,
        "privacy_version": _DummySettings.privacy_version,
        "terms_version": _DummySettings.tos_version,
    }
    assert payload == expected


@patch("lilypad.server.api.v0.settings_api.fetch_policy_versions")
def test_settings_endpoint_respects_dependency_override(
    mock_fetch_policy_versions: AsyncMock, client: TestClient
) -> None:
    """Changing the override should change the response immediately."""
    mock_fetch_policy_versions.return_value = {
        "privacyVersion": _DummySettings.privacy_version,
        "termsVersion": _DummySettings.tos_version,
    }

    class AltSettings(_DummySettings):
        experimental = True  # flip the flag

    # Override again for this specific call
    api.dependency_overrides[get_settings] = lambda: AltSettings()  # type: ignore[arg-type]
    alt_client = TestClient(api)

    response = alt_client.get("/settings")
    assert response.status_code == 200
    assert response.json()["experimental"] is True


@pytest.mark.asyncio
@patch("lilypad.server.api.v0.settings_api.httpx.AsyncClient")
async def test_fetch_policy_versions_success(mock_client_class: MagicMock) -> None:
    """Test fetch_policy_versions returns correct data on successful API response."""
    # Mock the response data
    mock_response_data = [
        {
            "type": "policy",
            "path": "/privacy",
            "route": "/privacy",
            "title": "Privacy Policy",
            "description": "Our privacy policy",
            "slug": "privacy",
            "lastUpdated": "2024-01-15T10:30:00Z",
        },
        {
            "type": "policy",
            "path": "/terms",
            "route": "/terms",
            "title": "Terms of Service",
            "description": "Our terms of service",
            "slug": "service",
            "lastUpdated": "2024-01-10T14:20:00Z",
        },
        {
            "type": "policy",
            "path": "/other",
            "route": "/other",
            "title": "Other Policy",
            "description": "Other policy",
            "slug": "other",
            "lastUpdated": "2024-01-01T00:00:00Z",
        },
    ]

    # Set up the mock client and response
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_client.get.return_value = mock_response

    # Mock the async context manager
    mock_client_class.return_value.__aenter__.return_value = mock_client
    mock_client_class.return_value.__aexit__.return_value = None

    # Call the function
    result = await fetch_policy_versions()

    # Verify the result
    expected = {
        "privacyVersion": "2024-01-15T10:30:00Z",
        "termsVersion": "2024-01-10T14:20:00Z",
    }
    assert result == expected

    # Verify the HTTP call was made correctly
    mock_client.get.assert_called_once_with(
        "https://mirascope.com/static/content-meta/policy/index.json"
    )
    mock_response.raise_for_status.assert_called_once()


@pytest.mark.asyncio
@patch("lilypad.server.api.v0.settings_api.httpx.AsyncClient")
async def test_fetch_policy_versions_http_error(mock_client_class: MagicMock) -> None:
    """Test fetch_policy_versions returns defaults on HTTP error."""
    # Set up the mock client to raise an HTTP error
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found", request=MagicMock(), response=MagicMock()
    )
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__aenter__.return_value = mock_client
    mock_client_class.return_value.__aexit__.return_value = None

    # Call the function
    result = await fetch_policy_versions()

    # Verify it returns the default values
    expected = {"privacyVersion": None, "termsVersion": None}
    assert result == expected


@pytest.mark.asyncio
@patch("lilypad.server.api.v0.settings_api.httpx.AsyncClient")
async def test_fetch_policy_versions_missing_policies(
    mock_client_class: MagicMock,
) -> None:
    """Test fetch_policy_versions handles missing policy types gracefully."""
    # Mock response with only privacy policy
    mock_response_data = [
        {
            "type": "policy",
            "path": "/privacy",
            "route": "/privacy",
            "title": "Privacy Policy",
            "description": "Our privacy policy",
            "slug": "privacy",
            "lastUpdated": "2024-01-15T10:30:00Z",
        },
        {
            "type": "policy",
            "path": "/other",
            "route": "/other",
            "title": "Other Policy",
            "description": "Other policy",
            "slug": "other",
            "lastUpdated": "2024-01-01T00:00:00Z",
        },
    ]

    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.return_value = mock_response_data
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__aenter__.return_value = mock_client
    mock_client_class.return_value.__aexit__.return_value = None

    # Call the function
    result = await fetch_policy_versions()

    # Verify it returns defaults because the function requires BOTH policies
    expected = {"privacyVersion": None, "termsVersion": None}
    assert result == expected


@pytest.mark.asyncio
@patch("lilypad.server.api.v0.settings_api.httpx.AsyncClient")
async def test_fetch_policy_versions_network_error(
    mock_client_class: MagicMock,
) -> None:
    """Test fetch_policy_versions returns defaults on network error."""
    # Set up the mock client to raise a general exception
    mock_client = AsyncMock()
    mock_client.get.side_effect = Exception("Network error")
    mock_client_class.return_value.__aenter__.return_value = mock_client
    mock_client_class.return_value.__aexit__.return_value = None

    # Call the function
    result = await fetch_policy_versions()

    # Verify it returns the default values
    expected = {"privacyVersion": None, "termsVersion": None}
    assert result == expected


@pytest.mark.asyncio
@patch("lilypad.server.api.v0.settings_api.httpx.AsyncClient")
async def test_fetch_policy_versions_invalid_json(mock_client_class: MagicMock) -> None:
    """Test fetch_policy_versions handles invalid JSON response."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("Invalid JSON")
    mock_client.get.return_value = mock_response
    mock_client_class.return_value.__aenter__.return_value = mock_client
    mock_client_class.return_value.__aexit__.return_value = None

    # Call the function
    result = await fetch_policy_versions()

    # Verify it returns the default values
    expected = {"privacyVersion": None, "termsVersion": None}
    assert result == expected
