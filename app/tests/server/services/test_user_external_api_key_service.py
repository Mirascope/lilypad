"""Tests for the user external API key service."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from lilypad.server.models.external_api_keys import ExternalAPIKeyTable
from lilypad.server.models.users import UserTable
from lilypad.server.schemas.users import UserPublic
from lilypad.server.services.user_external_api_key_service import (
    UserExternalAPIKeyService,
)


class TestUserExternalAPIKeyService:
    """Test UserExternalAPIKeyService class."""

    def create_mock_service(self):
        """Create a mock service instance for testing."""
        mock_session = Mock()
        mock_user = Mock(spec=UserPublic)
        mock_user.uuid = uuid4()
        mock_user.email = "test@example.com"

        with (
            patch(
                "lilypad.server.services.user_external_api_key_service.AuditLogger"
            ) as mock_audit_logger,
            patch(
                "lilypad.server.services.user_external_api_key_service.get_secret_manager"
            ) as mock_get_secret_manager,
        ):
            mock_secret_manager = Mock()
            mock_get_secret_manager.return_value = mock_secret_manager
            mock_audit_logger_instance = Mock()
            mock_audit_logger.return_value = mock_audit_logger_instance

            service = UserExternalAPIKeyService(session=mock_session, user=mock_user)
            service.audit_logger = mock_audit_logger_instance
            service.secret_manager = mock_secret_manager

            return (
                service,
                mock_session,
                mock_user,
                mock_secret_manager,
                mock_audit_logger_instance,
            )

    def test_init(self):
        """Test service initialization."""
        mock_session = Mock()
        mock_user = Mock(spec=UserPublic)
        mock_user.uuid = uuid4()

        with (
            patch(
                "lilypad.server.services.user_external_api_key_service.AuditLogger"
            ) as mock_audit_logger,
            patch(
                "lilypad.server.services.user_external_api_key_service.get_secret_manager"
            ) as mock_get_secret_manager,
        ):
            mock_secret_manager = Mock()
            mock_get_secret_manager.return_value = mock_secret_manager

            service = UserExternalAPIKeyService(session=mock_session, user=mock_user)

            assert service.session == mock_session
            assert service.user == mock_user
            mock_audit_logger.assert_called_once_with(mock_session)
            mock_get_secret_manager.assert_called_once_with(mock_session)

    def test_get_secret_name(self):
        """Test get_secret_name method."""
        service, _, mock_user, _, _ = self.create_mock_service()

        secret_name = service.get_secret_name("openai")

        assert secret_name == f"{mock_user.uuid}_openai"

    def test_store_api_key_new_key(self):
        """Test storing a new API key."""
        service, mock_session, mock_user, mock_secret_manager, mock_audit_logger = (
            self.create_mock_service()
        )

        # Mock that no existing API key exists
        mock_session.exec.return_value.first.return_value = None

        # Mock secret manager store operation
        mock_secret_manager.store_secret.return_value = "secret-id-123"

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        # Mock session add and commit
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()

        service.store_api_key("openai", "sk-test-key")

        # Verify secret manager was called
        mock_secret_manager.store_secret.assert_called_once()
        store_call_args = mock_secret_manager.store_secret.call_args
        assert store_call_args[0][0] == f"{mock_user.uuid}_openai"  # secret_name
        assert store_call_args[0][1] == "sk-test-key"  # secret_value

        # Verify database operations
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

        # Verify audit log
        mock_audit_logger.log_secret_access.assert_called_once()

    def test_store_api_key_update_existing(self):
        """Test updating an existing API key."""
        service, mock_session, mock_user, mock_secret_manager, mock_audit_logger = (
            self.create_mock_service()
        )

        # Mock existing API key record
        existing_key = Mock(spec=ExternalAPIKeyTable)
        existing_key.secret_id = "old-secret-id"
        existing_key.service_name = "openai"
        mock_session.exec.return_value.first.return_value = existing_key

        # Mock secret manager operations - update_secret returns True/False for success
        mock_secret_manager.update_secret.return_value = True

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        result = service.store_api_key("openai", "sk-new-key")

        # Verify secret manager was called to update
        mock_secret_manager.update_secret.assert_called_once()
        update_call_args = mock_secret_manager.update_secret.call_args
        assert update_call_args[0][0] == "old-secret-id"  # secret_id
        assert update_call_args[0][1] == "sk-new-key"  # new_value

        # Verify the existing key object is returned
        assert result == existing_key

    def test_store_api_key_integrity_error_retry(self):
        """Test handling IntegrityError during secret manager store operation."""
        service, mock_session, mock_user, mock_secret_manager, mock_audit_logger = (
            self.create_mock_service()
        )

        # Mock that no existing API key exists initially
        mock_session.exec.return_value.first.return_value = None

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        # Mock secret manager - first store raises IntegrityError, then succeeds
        mock_secret_manager.store_secret.side_effect = [
            IntegrityError("constraint failed", "stmt", Exception("params")),
            "secret-id-123",
        ]
        mock_secret_manager.get_secret_id_by_name.return_value = "duplicate-secret-id"
        mock_secret_manager.delete_secret = Mock()

        # Mock session operations
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()

        service.store_api_key("openai", "sk-test-key")

        # Verify secret was deleted and recreated
        mock_secret_manager.delete_secret.assert_called_once_with("duplicate-secret-id")
        assert mock_secret_manager.store_secret.call_count == 2

    def test_get_api_key_success(self):
        """Test successful API key retrieval."""
        service, mock_session, mock_user, mock_secret_manager, _ = (
            self.create_mock_service()
        )

        # Mock existing API key record
        existing_key = Mock(spec=ExternalAPIKeyTable)
        existing_key.secret_id = "secret-id-123"
        existing_key.service_name = "openai"
        mock_session.exec.return_value.first.return_value = existing_key

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        # Mock secret manager get operation
        mock_secret_manager.get_secret.return_value = "sk-retrieved-key"

        result = service.get_api_key("openai")

        assert result == "sk-retrieved-key"
        mock_secret_manager.get_secret.assert_called_once_with("secret-id-123")

    def test_get_api_key_not_found(self):
        """Test API key retrieval when key doesn't exist."""
        service, mock_session, mock_user, mock_secret_manager, _ = (
            self.create_mock_service()
        )

        # Mock no existing API key record
        mock_session.exec.return_value.first.return_value = None

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        with pytest.raises(HTTPException) as exc_info:
            service.get_api_key("openai")

        assert exc_info.value.status_code == 404
        assert "External API key for openai not found" in str(exc_info.value.detail)

    def test_get_api_key_secret_manager_error(self):
        """Test API key retrieval when secret manager fails."""
        service, mock_session, mock_user, mock_secret_manager, _ = (
            self.create_mock_service()
        )

        # Mock existing API key record
        existing_key = Mock(spec=ExternalAPIKeyTable)
        existing_key.secret_id = "secret-id-123"
        existing_key.service_name = "openai"
        mock_session.exec.return_value.first.return_value = existing_key

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        # Mock secret manager get failure (returns None)
        mock_secret_manager.get_secret.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            service.get_api_key("openai")

        assert exc_info.value.status_code == 500
        assert "Failed to retrieve external API key for openai" in str(
            exc_info.value.detail
        )

    def test_delete_api_key_success(self):
        """Test successful API key deletion."""
        service, mock_session, mock_user, mock_secret_manager, mock_audit_logger = (
            self.create_mock_service()
        )

        # Mock existing API key record
        existing_key = Mock(spec=ExternalAPIKeyTable)
        existing_key.secret_id = "secret-id-123"
        existing_key.service_name = "openai"
        mock_session.exec.return_value.first.return_value = existing_key

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        # Mock session operations
        mock_session.delete = Mock()
        mock_session.commit = Mock()

        # Mock secret manager delete operation returns True for success
        mock_secret_manager.delete_secret.return_value = True

        result = service.delete_api_key("openai")

        # Verify database operations
        mock_session.delete.assert_called_once_with(existing_key)
        mock_session.commit.assert_called_once()

        # Verify secret manager operations
        mock_secret_manager.delete_secret.assert_called_once_with("secret-id-123")

        # Verify return value
        assert result is True

        # Verify audit log
        mock_audit_logger.log_secret_access.assert_called_once()

    def test_delete_api_key_not_found(self):
        """Test API key deletion when key doesn't exist."""
        service, mock_session, mock_user, mock_secret_manager, _ = (
            self.create_mock_service()
        )

        # Mock no existing API key record
        mock_session.exec.return_value.first.return_value = None

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        with pytest.raises(HTTPException) as exc_info:
            service.delete_api_key("openai")

        assert exc_info.value.status_code == 404
        assert "External API key for openai not found" in str(exc_info.value.detail)

    def test_list_api_keys(self):
        """Test listing API keys for a user."""
        service, mock_session, mock_user, mock_secret_manager, _ = (
            self.create_mock_service()
        )

        # Mock API key records
        key1 = Mock(spec=ExternalAPIKeyTable)
        key1.service_name = "openai"
        key1.created_at = "2023-01-01"

        key2 = Mock(spec=ExternalAPIKeyTable)
        key2.service_name = "anthropic"
        key2.created_at = "2023-01-02"

        # Mock get_user method with external_api_keys relationship
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        mock_user_record.external_api_keys = [key1, key2]
        service.get_user = Mock(return_value=mock_user_record)

        result = service.list_api_keys()

        # Service returns a dict with masked values
        assert isinstance(result, dict)
        assert len(result) == 2
        assert result["openai"] == "********"
        assert result["anthropic"] == "********"

    def test_list_api_keys_empty(self):
        """Test listing API keys when user has none."""
        service, mock_session, mock_user, mock_secret_manager, _ = (
            self.create_mock_service()
        )

        # Mock get_user method with empty external_api_keys relationship
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        mock_user_record.external_api_keys = []
        service.get_user = Mock(return_value=mock_user_record)

        result = service.list_api_keys()

        # Service returns an empty dict
        assert isinstance(result, dict)
        assert result == {}

    def test_get_user(self):
        """Test get_user method."""
        service, mock_session, mock_user, mock_secret_manager, _ = (
            self.create_mock_service()
        )

        # Mock user record
        user_record = Mock(spec=UserTable)
        user_record.uuid = mock_user.uuid
        user_record.email = mock_user.email
        mock_session.exec.return_value.first.return_value = user_record

        result = service.get_user()

        assert result == user_record

    def test_get_user_not_found(self):
        """Test get_user when user doesn't exist."""
        service, mock_session, mock_user, mock_secret_manager, _ = (
            self.create_mock_service()
        )

        # Mock no user found
        mock_session.exec.return_value.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            service.get_user()

        assert exc_info.value.status_code == 404
        assert "User not found" in str(exc_info.value.detail)

    def test_audit_logging_store_action(self):
        """Test that audit logging works for store operations."""
        service, mock_session, mock_user, mock_secret_manager, mock_audit_logger = (
            self.create_mock_service()
        )

        # Mock no existing API key
        mock_session.exec.return_value.first.return_value = None
        mock_secret_manager.store_secret.return_value = "secret-id-123"

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        # Mock session operations
        mock_session.add = Mock()
        mock_session.commit = Mock()
        mock_session.refresh = Mock()

        service.store_api_key("openai", "sk-test-key")

        # Verify audit logging was called
        mock_audit_logger.log_secret_access.assert_called_once()
        # Can verify the action type and details if needed

    def test_audit_logging_delete_action(self):
        """Test that audit logging works for delete operations."""
        service, mock_session, mock_user, mock_secret_manager, mock_audit_logger = (
            self.create_mock_service()
        )

        # Mock existing API key
        existing_key = Mock(spec=ExternalAPIKeyTable)
        existing_key.secret_id = "secret-id-123"
        existing_key.service_name = "openai"
        mock_session.exec.return_value.first.return_value = existing_key

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        # Mock session operations
        mock_session.delete = Mock()
        mock_session.commit = Mock()
        mock_secret_manager.delete_secret.return_value = True

        service.delete_api_key("openai")

        # Verify audit logging was called
        mock_audit_logger.log_secret_access.assert_called_once()

    def test_error_handling_secret_manager_failure(self):
        """Test error handling when secret manager operations fail."""
        service, mock_session, mock_user, mock_secret_manager, _ = (
            self.create_mock_service()
        )

        # Mock no existing API key
        mock_session.exec.return_value.first.return_value = None

        # Mock secret manager failure - any exception except IntegrityError should propagate
        mock_secret_manager.store_secret.side_effect = Exception("SecretManager failed")

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        with pytest.raises(Exception) as exc_info:
            service.store_api_key("openai", "sk-test-key")

        assert "SecretManager failed" in str(exc_info.value)

    def test_store_api_key_update_failure(self):
        """Test handling update failure in store_api_key method."""
        service, mock_session, mock_user, mock_secret_manager, mock_audit_logger = (
            self.create_mock_service()
        )

        # Mock existing API key record
        existing_key = Mock(spec=ExternalAPIKeyTable)
        existing_key.secret_id = "old-secret-id"
        existing_key.service_name = "openai"
        mock_session.exec.return_value.first.return_value = existing_key

        # Mock secret manager update failure
        mock_secret_manager.update_secret.return_value = False

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        with pytest.raises(HTTPException) as exc_info:
            service.store_api_key("openai", "sk-new-key")

        assert exc_info.value.status_code == 500
        assert "Failed to update external API key for openai" in str(
            exc_info.value.detail
        )

        # Verify audit logging was called with failure
        mock_audit_logger.log_secret_access.assert_called_once()
        call_args = mock_audit_logger.log_secret_access.call_args
        assert call_args[1]["success"] is False
        assert "Failed to update secret in SecretManager" in str(
            call_args[1]["additional_info"]["error"]
        )

    def test_update_api_key_success(self):
        """Test successful API key update using update_api_key method."""
        service, mock_session, mock_user, mock_secret_manager, mock_audit_logger = (
            self.create_mock_service()
        )

        # Mock existing API key record
        existing_key = Mock(spec=ExternalAPIKeyTable)
        existing_key.secret_id = "existing-secret-id"
        existing_key.service_name = "openai"
        mock_session.exec.return_value.first.return_value = existing_key

        # Mock secret manager update success
        mock_secret_manager.update_secret.return_value = True

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        result = service.update_api_key("openai", "sk-updated-key")

        # Verify secret manager was called to update
        mock_secret_manager.update_secret.assert_called_once_with(
            "existing-secret-id", "sk-updated-key"
        )

        # Verify the existing key object is returned
        assert result == existing_key

        # Verify audit logging was called with success
        mock_audit_logger.log_secret_access.assert_called_once()
        call_args = mock_audit_logger.log_secret_access.call_args
        assert call_args[1]["success"] is True

    def test_update_api_key_not_found(self):
        """Test update_api_key when key doesn't exist."""
        service, mock_session, mock_user, mock_secret_manager, mock_audit_logger = (
            self.create_mock_service()
        )

        # Mock no existing API key record
        mock_session.exec.return_value.first.return_value = None

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        with pytest.raises(HTTPException) as exc_info:
            service.update_api_key("openai", "sk-new-key")

        assert exc_info.value.status_code == 404
        assert "External API key for openai not found" in str(exc_info.value.detail)

        # Verify audit logging was called with failure
        mock_audit_logger.log_secret_access.assert_called_once()
        call_args = mock_audit_logger.log_secret_access.call_args
        assert call_args[1]["success"] is False
        assert "External API key not found" in str(
            call_args[1]["additional_info"]["error"]
        )

    def test_update_api_key_update_failure(self):
        """Test update_api_key when update fails."""
        service, mock_session, mock_user, mock_secret_manager, mock_audit_logger = (
            self.create_mock_service()
        )

        # Mock existing API key record
        existing_key = Mock(spec=ExternalAPIKeyTable)
        existing_key.secret_id = "existing-secret-id"
        existing_key.service_name = "openai"
        mock_session.exec.return_value.first.return_value = existing_key

        # Mock secret manager update failure
        mock_secret_manager.update_secret.return_value = False

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        with pytest.raises(HTTPException) as exc_info:
            service.update_api_key("openai", "sk-updated-key")

        assert exc_info.value.status_code == 500
        assert "Failed to update external API key for openai" in str(
            exc_info.value.detail
        )

        # Verify audit logging was called with failure
        mock_audit_logger.log_secret_access.assert_called_once()
        call_args = mock_audit_logger.log_secret_access.call_args
        assert call_args[1]["success"] is False
        assert "Failed to update secret in SecretManager" in str(
            call_args[1]["additional_info"]["error"]
        )

    def test_delete_api_key_delete_failure(self):
        """Test delete_api_key when delete fails."""
        service, mock_session, mock_user, mock_secret_manager, mock_audit_logger = (
            self.create_mock_service()
        )

        # Mock existing API key record
        existing_key = Mock(spec=ExternalAPIKeyTable)
        existing_key.secret_id = "existing-secret-id"
        existing_key.service_name = "openai"
        mock_session.exec.return_value.first.return_value = existing_key

        # Mock secret manager delete failure
        mock_secret_manager.delete_secret.return_value = False

        # Mock get_user method
        mock_user_record = Mock()
        mock_user_record.uuid = mock_user.uuid
        mock_user_record.email = mock_user.email
        service.get_user = Mock(return_value=mock_user_record)

        with pytest.raises(HTTPException) as exc_info:
            service.delete_api_key("openai")

        assert exc_info.value.status_code == 500
        assert "Failed to delete external API key for openai from SecretManager" in str(
            exc_info.value.detail
        )

        # Verify audit logging was called with failure
        mock_audit_logger.log_secret_access.assert_called_once()
        call_args = mock_audit_logger.log_secret_access.call_args
        assert call_args[1]["success"] is False
        assert "Failed to delete secret from SecretManager" in str(
            call_args[1]["additional_info"]["error"]
        )

    def test_service_inheritance(self):
        """Test that service properly inherits from BaseOrganizationService."""
        service, _, _, _, _ = self.create_mock_service()

        from lilypad.server.services.base_organization import BaseOrganizationService

        assert isinstance(service, BaseOrganizationService)
