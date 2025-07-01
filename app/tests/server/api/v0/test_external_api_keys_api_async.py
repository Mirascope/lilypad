"""Async tests for external API keys API."""

from unittest.mock import AsyncMock, Mock

import pytest
from httpx import AsyncClient

from lilypad.server.services.user_external_api_key_service import (
    UserExternalAPIKeyService,
)
from tests.async_test_utils import AsyncDatabaseTestMixin


class TestExternalAPIKeysAPIAsync(AsyncDatabaseTestMixin):
    """Test external API keys API endpoints asynchronously."""

    @pytest.fixture
    def mock_external_api_key_service(self):
        """Mock the external API key service."""
        mock_service = Mock(spec=UserExternalAPIKeyService)
        # Set up default return values
        mock_service.list_api_keys = AsyncMock(return_value={})
        mock_service.get_api_key = AsyncMock(return_value="test-api-key-12345")
        mock_service.delete_api_key = AsyncMock(return_value=True)
        mock_service.store_api_key = AsyncMock(return_value=None)
        mock_service.update_api_key = AsyncMock(return_value=None)
        return mock_service

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_store_external_api_key(
        self, async_client: AsyncClient, mock_external_api_key_service
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
            response = await async_client.post("/external-api-keys", json=api_key_data)
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

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_external_api_key(
        self, async_client: AsyncClient, mock_external_api_key_service
    ):
        """Test retrieving an external API key."""
        from lilypad.server.api.v0.main import api

        def get_mock_service():
            return mock_external_api_key_service

        api.dependency_overrides[UserExternalAPIKeyService] = get_mock_service

        try:
            response = await async_client.get("/external-api-keys/openai")
            assert response.status_code == 200
            data = response.json()
            assert data["service_name"] == "openai"
            assert "test" in data["masked_api_key"]  # First 4 chars visible
            assert "****" in data["masked_api_key"]  # Rest is masked

            # Verify service was called
            mock_external_api_key_service.get_api_key.assert_called_once_with("openai")
        finally:
            del api.dependency_overrides[UserExternalAPIKeyService]

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_external_api_key(
        self, async_client: AsyncClient, mock_external_api_key_service
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
            response = await async_client.patch(
                "/external-api-keys/openai", json=update_data
            )
            assert response.status_code == 200
            data = response.json()
            assert data["service_name"] == "openai"
            assert "sk-n" in data["masked_api_key"]  # Updated key prefix
            assert "****" in data["masked_api_key"]

            # Verify service was called
            mock_external_api_key_service.update_api_key.assert_called_once_with(
                "openai", "sk-new-test-key-987654321"
            )
        finally:
            del api.dependency_overrides[UserExternalAPIKeyService]

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_delete_external_api_key(
        self, async_client: AsyncClient, mock_external_api_key_service
    ):
        """Test deleting an external API key."""
        from lilypad.server.api.v0.main import api

        def get_mock_service():
            return mock_external_api_key_service

        api.dependency_overrides[UserExternalAPIKeyService] = get_mock_service

        try:
            response = await async_client.delete("/external-api-keys/openai")
            assert response.status_code == 200
            assert response.json() is True

            # Verify service was called
            mock_external_api_key_service.delete_api_key.assert_called_once_with(
                "openai"
            )
        finally:
            del api.dependency_overrides[UserExternalAPIKeyService]

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_list_external_api_keys(
        self, async_client: AsyncClient, mock_external_api_key_service
    ):
        """Test listing all external API keys."""
        from lilypad.server.api.v0.main import api

        # Set up mock return value
        mock_external_api_key_service.list_api_keys = AsyncMock(
            return_value={
                "openai": "sk-test-****",
                "anthropic": "sk-ant-****",
            }
        )

        def get_mock_service():
            return mock_external_api_key_service

        api.dependency_overrides[UserExternalAPIKeyService] = get_mock_service

        try:
            response = await async_client.get("/external-api-keys")
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert any(key["service_name"] == "openai" for key in data)
            assert any(key["service_name"] == "anthropic" for key in data)

            # Verify service was called
            mock_external_api_key_service.list_api_keys.assert_called_once()
        finally:
            del api.dependency_overrides[UserExternalAPIKeyService]

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_nonexistent_api_key(
        self, async_client: AsyncClient, mock_external_api_key_service
    ):
        """Test getting a non-existent API key."""
        from lilypad.server.api.v0.main import api

        # Mock service returns None for non-existent keys
        mock_external_api_key_service.get_api_key = AsyncMock(return_value=None)

        def get_mock_service():
            return mock_external_api_key_service

        api.dependency_overrides[UserExternalAPIKeyService] = get_mock_service

        try:
            response = await async_client.get("/external-api-keys/nonexistent")
            assert response.status_code == 404
        finally:
            del api.dependency_overrides[UserExternalAPIKeyService]

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_store_api_key_validation(
        self, async_client: AsyncClient, mock_external_api_key_service
    ):
        """Test API key validation when storing."""
        from lilypad.server.api.v0.main import api

        def get_mock_service():
            return mock_external_api_key_service

        api.dependency_overrides[UserExternalAPIKeyService] = get_mock_service

        try:
            # Test with empty service name
            response = await async_client.post(
                "/external-api-keys",
                json={"service_name": "", "api_key": "test-key"},
            )
            assert response.status_code == 422  # Validation error

            # Test with empty API key
            response = await async_client.post(
                "/external-api-keys",
                json={"service_name": "openai", "api_key": ""},
            )
            assert response.status_code == 422  # Validation error
        finally:
            del api.dependency_overrides[UserExternalAPIKeyService]

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_supported_services(
        self, async_client: AsyncClient, mock_external_api_key_service
    ):
        """Test storing keys for various supported services."""
        from lilypad.server.api.v0.main import api

        def get_mock_service():
            return mock_external_api_key_service

        api.dependency_overrides[UserExternalAPIKeyService] = get_mock_service

        supported_services = ["openai", "anthropic", "cohere", "mistral", "groq"]

        try:
            for service in supported_services:
                response = await async_client.post(
                    "/external-api-keys",
                    json={"service_name": service, "api_key": f"{service}-key-123"},
                )
                assert response.status_code == 200
                assert response.json()["service_name"] == service
        finally:
            del api.dependency_overrides[UserExternalAPIKeyService]
