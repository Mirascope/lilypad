from fastapi.testclient import TestClient
import pytest

from lilypad.server.api.v0.main import api, get_settings


class _DummySettings:  # noqa: D401 (simple stub object)
    """Minimal stand-in for the real Settings object."""

    remote_client_url = "https://client.example.com"
    remote_api_url = "https://api.example.com"
    github_client_id = "dummy-github-id"
    google_client_id = "dummy-google-id"
    environment = "production"
    experimental = False


@pytest.fixture(name="client")
def fixture_client() -> TestClient:
    """Create a TestClient with the settings dependency overridden."""
    api.dependency_overrides[get_settings] = lambda: _DummySettings()  # type: ignore[arg-type]
    yield TestClient(api)
    api.dependency_overrides.clear()


def test_settings_endpoint_returns_expected_payload(client: TestClient) -> None:
    """`/settings` should return all fields from SettingsPublic with correct values."""
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
    }
    assert payload == expected


def test_settings_endpoint_respects_dependency_override(client: TestClient) -> None:
    """Changing the override should change the response immediately."""
    class AltSettings(_DummySettings):
        experimental = True  # flip the flag

    # Override again for this specific call
    api.dependency_overrides[get_settings] = lambda: AltSettings()  # type: ignore[arg-type]
    alt_client = TestClient(api)

    response = alt_client.get("/settings")
    assert response.status_code == 200
    assert response.json()["experimental"] is True
