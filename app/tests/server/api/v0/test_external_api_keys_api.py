"""Tests for external API keys API."""

from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from lilypad.server.services.user_external_api_key_service import (
    UserExternalAPIKeyService,
)


class TestExternalAPIKeysAPI:
    """Test external API keys API endpoints."""

    @pytest.fixture
    def mock_external_api_key_service(self):
        """Mock the external API key service."""
        mock_service = Mock(spec=UserExternalAPIKeyService)
        # Set up default return values
        mock_service.list_api_keys.return_value = {}
        mock_service.get_api_key.return_value = "test-api-key-12345"
        mock_service.delete_api_key.return_value = True
        return mock_service

    def test_store_external_api_key(
        self, client: TestClient, mock_external_api_key_service
    ):
        """Test storing a new external API key."""
        # Override the dependency
        from lilypad.server.api.v0.main import api

        def get_mock_service():
            return mock_external_api_key_service

        api.dependency_overrides[UserExternalAPIKeyService] = get_mock_service

        try:
            api_key_data = {
                "service_name": "openai",
                "api_key": "sk-test-key-123456789",
            }
            response = client.post("/external-api-keys", json=api_key_data)
            assert response.status_code == 200
            data = response.json()
            assert data["service_name"] == "openai"
            assert "sk-t" in data["masked_api_key"]  # First 4 chars visible
            assert "****" in data["masked_api_key"]  # Rest is masked

            # Verify service was called
            mock_external_api_key_service.store_api_key.assert_called_once_with(
                "openai", "sk-test-key-123456789"
            )
        finally:
            # Clean up the override
            del api.dependency_overrides[UserExternalAPIKeyService]

    def test_get_external_api_key(
        self, client: TestClient, mock_external_api_key_service
    ):
        """Test retrieving an external API key."""
        from lilypad.server.api.v0.main import api

        def get_mock_service():
            return mock_external_api_key_service

        api.dependency_overrides[UserExternalAPIKeyService] = get_mock_service

        try:
            response = client.get("/external-api-keys/openai")
            assert response.status_code == 200
            data = response.json()
            assert data["service_name"] == "openai"
            assert "test" in data["masked_api_key"]  # First 4 chars visible
            assert "****" in data["masked_api_key"]  # Rest is masked

            # Verify service was called
            mock_external_api_key_service.get_api_key.assert_called_once_with("openai")
        finally:
            del api.dependency_overrides[UserExternalAPIKeyService]

    def test_update_external_api_key(
        self, client: TestClient, mock_external_api_key_service
    ):
        """Test updating an external API key."""
        from lilypad.server.api.v0.main import api

        def get_mock_service():
            return mock_external_api_key_service

        api.dependency_overrides[UserExternalAPIKeyService] = get_mock_service

        try:
            update_data = {
                "api_key": "sk-new-test-key-987654321",
            }
            response = client.patch("/external-api-keys/openai", json=update_data)
            assert response.status_code == 200
            data = response.json()
            assert data["service_name"] == "openai"
            assert "sk-n" in data["masked_api_key"]  # First 4 chars visible
            assert "****" in data["masked_api_key"]  # Rest is masked

            # Verify service was called
            mock_external_api_key_service.update_api_key.assert_called_once_with(
                "openai", "sk-new-test-key-987654321"
            )
        finally:
            del api.dependency_overrides[UserExternalAPIKeyService]

    def test_delete_external_api_key(
        self, client: TestClient, mock_external_api_key_service
    ):
        """Test deleting an external API key."""
        from lilypad.server.api.v0.main import api

        def get_mock_service():
            return mock_external_api_key_service

        api.dependency_overrides[UserExternalAPIKeyService] = get_mock_service

        try:
            response = client.delete("/external-api-keys/openai")
            assert response.status_code == 200
            assert response.json() is True

            # Verify service was called
            mock_external_api_key_service.delete_api_key.assert_called_once_with(
                "openai"
            )
        finally:
            del api.dependency_overrides[UserExternalAPIKeyService]

    def test_delete_external_api_key_not_found(
        self, client: TestClient, mock_external_api_key_service
    ):
        """Test deleting a non-existent API key."""
        from lilypad.server.api.v0.main import api

        mock_external_api_key_service.delete_api_key.return_value = False

        def get_mock_service():
            return mock_external_api_key_service

        api.dependency_overrides[UserExternalAPIKeyService] = get_mock_service

        try:
            response = client.delete("/external-api-keys/nonexistent")
            assert response.status_code == 200
            assert response.json() is False

            # Verify service was called
            mock_external_api_key_service.delete_api_key.assert_called_once_with(
                "nonexistent"
            )
        finally:
            del api.dependency_overrides[UserExternalAPIKeyService]

    def test_list_external_api_keys_empty(
        self, client: TestClient, mock_external_api_key_service
    ):
        """Test listing API keys when none exist."""
        from lilypad.server.api.v0.main import api

        def get_mock_service():
            return mock_external_api_key_service

        api.dependency_overrides[UserExternalAPIKeyService] = get_mock_service

        try:
            response = client.get("/external-api-keys")
            assert response.status_code == 200
            data = response.json()
            assert data == []

            # Verify service was called
            mock_external_api_key_service.list_api_keys.assert_called_once()
        finally:
            del api.dependency_overrides[UserExternalAPIKeyService]

    def test_list_external_api_keys_with_data(
        self, client: TestClient, mock_external_api_key_service
    ):
        """Test listing API keys with existing data."""
        from lilypad.server.api.v0.main import api

        mock_external_api_key_service.list_api_keys.return_value = {
            "openai": "sk-test-123456789",
            "anthropic": "ant-test-987654321",
        }

        def get_mock_service():
            return mock_external_api_key_service

        api.dependency_overrides[UserExternalAPIKeyService] = get_mock_service

        try:
            response = client.get("/external-api-keys")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2

            # Check openai key
            openai_key = next(k for k in data if k["service_name"] == "openai")
            assert "sk-t" in openai_key["masked_api_key"]
            assert "****" in openai_key["masked_api_key"]

            # Check anthropic key
            anthropic_key = next(k for k in data if k["service_name"] == "anthropic")
            assert "ant-" in anthropic_key["masked_api_key"]
            assert "****" in anthropic_key["masked_api_key"]

            # Verify service was called
            mock_external_api_key_service.list_api_keys.assert_called_once()
        finally:
            del api.dependency_overrides[UserExternalAPIKeyService]

    def test_store_api_key_empty_string(self, client: TestClient):
        """Test storing an API key with empty string fails validation."""
        api_key_data = {
            "service_name": "openai",
            "api_key": "",  # Empty string should fail
        }
        response = client.post("/external-api-keys", json=api_key_data)
        assert response.status_code == 422  # Validation error

    def test_update_api_key_empty_string(self, client: TestClient):
        """Test updating an API key with empty string fails validation."""
        update_data = {
            "api_key": "",  # Empty string should fail
        }
        response = client.patch("/external-api-keys/openai", json=update_data)
        assert response.status_code == 422  # Validation error
