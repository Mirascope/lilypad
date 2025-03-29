"""Service for managing external API keys stored in a separate table using SecretManager."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from .._utils import get_current_user
from .._utils.audit_logger import AuditAction, AuditLogger
from ..db import get_session
from ..models import UserTable
from ..models.external_api_keys import ExternalAPIKeyTable
from ..schemas import UserPublic
from ..secret_manager.secret_manager_factory import get_secret_manager
from ..services.base_organization import BaseOrganizationService


class UserExternalAPIKeyService(BaseOrganizationService):
    """Service for managing external API keys stored in a separate table using SecretManager."""

    def __init__(
        self,
        session: Annotated[Session, Depends(get_session)],
        user: Annotated[UserPublic, Depends(get_current_user)],
    ) -> None:
        """Initialize the service."""
        super().__init__(session=session, user=user)
        self.audit_logger = AuditLogger(session)
        # Initialize SecretManager instance (e.g., SupabaseVaultManager)
        self.secret_manager = get_secret_manager(self.session)
        self.uuid = user.uuid

    def get_secret_name(self, service_name: str) -> str:
        """Generate a unique secret name for the user and service."""
        return f"{self.uuid}_{service_name}"

    def store_api_key(self, service_name: str, api_key: str) -> ExternalAPIKeyTable:
        """Store an external API key for a given service using SecretManager.

        If an API key record for the service already exists, update it.
        Otherwise, store a new secret in SecretManager and save its secret_id in the table.
        In case an IntegrityError occurs (e.g. duplicate key), delete the existing secret and retry.
        """
        user = self.get_user()
        user_id = str(user.uuid)
        description = f"External API key for {service_name} for user {user.email}"
        # Check if an API key record already exists for the service
        statement = select(ExternalAPIKeyTable).where(
            ExternalAPIKeyTable.user_id == user.uuid,
            ExternalAPIKeyTable.service_name == service_name,
        )
        existing = self.session.exec(statement).first()
        if existing:
            # Update the secret in SecretManager using the stored secret_id
            update_success = self.secret_manager.update_secret(
                existing.secret_id, api_key
            )
            if not update_success:
                self.audit_logger.log_secret_access(
                    user_id=user_id,
                    action=AuditAction.UPDATE,
                    service_name=service_name,
                    secret_id=existing.secret_id,
                    success=False,
                    additional_info={
                        "error": "Failed to update secret in SecretManager"
                    },
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to update external API key for {service_name}",
                )
            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.UPDATE,
                service_name=service_name,
                secret_id=existing.secret_id,
                success=True,
            )
            return existing

        name = self.get_secret_name(service_name)
        # Create a new secret in SecretManager and store its secret_id in the DB
        try:
            secret_id = self.secret_manager.store_secret(
                name, api_key, description
            )
        except IntegrityError:
            # If a duplicate key error occurs, delete the existing secret and retry storing
            duplicate_secret_id = self.secret_manager.get_secret_id_by_name(
                name
            )
            if duplicate_secret_id:
                self.secret_manager.delete_secret(duplicate_secret_id)
            secret_id = self.secret_manager.store_secret(
                name, api_key, description
            )

        new_key = ExternalAPIKeyTable(
            user_id=user.uuid,  # pyright: ignore [reportArgumentType]
            service_name=service_name,
            secret_id=secret_id,  # Save secret manager's key instead of the plain API key
            description=description,
        )
        self.session.add(new_key)
        self.session.commit()
        self.session.refresh(new_key)
        self.audit_logger.log_secret_access(
            user_id=user_id,
            action=AuditAction.CREATE,
            service_name=service_name,
            secret_id=secret_id,
            success=True,
        )
        return new_key

    def update_api_key(self, service_name: str, api_key: str) -> ExternalAPIKeyTable:
        """Update an external API key for a given service using SecretManager.

        Retrieves the existing record and updates the stored secret via SecretManager.
        """
        user = self.get_user()
        user_id = str(user.uuid)
        statement = select(ExternalAPIKeyTable).where(
            ExternalAPIKeyTable.user_id == user.uuid,
            ExternalAPIKeyTable.service_name == service_name,
        )
        key_record = self.session.exec(statement).first()
        if not key_record:
            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.UPDATE,
                service_name=service_name,
                secret_id="",
                success=False,
                additional_info={"error": "External API key not found"},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External API key for {service_name} not found",
            )
        update_success = self.secret_manager.update_secret(
            key_record.secret_id, api_key
        )
        if not update_success:
            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.UPDATE,
                service_name=service_name,
                secret_id=key_record.secret_id,
                success=False,
                additional_info={"error": "Failed to update secret in SecretManager"},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update external API key for {service_name}",
            )
        self.audit_logger.log_secret_access(
            user_id=user_id,
            action=AuditAction.UPDATE,
            service_name=service_name,
            secret_id=key_record.secret_id,
            success=True,
        )
        return key_record

    def get_api_key(self, service_name: str) -> str:
        """Retrieve the external API key for a given service using SecretManager.

        The method fetches the record from the database and then retrieves the actual API key
        from SecretManager using the stored secret_id.
        """
        user = self.get_user()
        user_id = str(user.uuid)
        statement = select(ExternalAPIKeyTable).where(
            ExternalAPIKeyTable.user_id == user.uuid,
            ExternalAPIKeyTable.service_name == service_name,
        )
        key_record = self.session.exec(statement).first()
        if not key_record:
            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.READ,
                service_name=service_name,
                secret_id="",
                success=False,
                additional_info={"error": "External API key not found"},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External API key for {service_name} not found",
            )
        api_key = self.secret_manager.get_secret(key_record.secret_id)
        if api_key is None:
            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.READ,
                service_name=service_name,
                secret_id=key_record.secret_id,
                success=False,
                additional_info={
                    "error": "Failed to retrieve secret from SecretManager"
                },
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to retrieve external API key for {service_name}",
            )
        self.audit_logger.log_secret_access(
            user_id=user_id,
            action=AuditAction.READ,
            service_name=service_name,
            secret_id=key_record.secret_id,
            success=True,
        )
        return api_key

    def delete_api_key(self, service_name: str) -> bool:
        """Delete an external API key for a given service using SecretManager.

        The method deletes the secret via SecretManager and then removes the corresponding record from the database.
        """
        user = self.get_user()
        user_id = str(user.uuid)
        statement = select(ExternalAPIKeyTable).where(
            ExternalAPIKeyTable.user_id == user.uuid,
            ExternalAPIKeyTable.service_name == service_name,
        )
        key_record = self.session.exec(statement).first()
        if not key_record:
            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.DELETE,
                service_name=service_name,
                secret_id="",
                success=False,
                additional_info={"error": "External API key not found"},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"External API key for {service_name} not found",
            )
        delete_success = self.secret_manager.delete_secret(key_record.secret_id)
        if not delete_success:
            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.DELETE,
                service_name=service_name,
                secret_id=key_record.secret_id,
                success=False,
                additional_info={"error": "Failed to delete secret from SecretManager"},
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete external API key for {service_name} from SecretManager",
            )
        self.session.delete(key_record)
        self.session.commit()
        self.audit_logger.log_secret_access(
            user_id=user_id,
            action=AuditAction.DELETE,
            service_name=service_name,
            secret_id=key_record.secret_id,
            success=True,
        )
        return True

    def list_api_keys(self) -> dict[str, str]:
        """List all external API keys for the user with masked values.

        For security reasons, the actual API key is not retrieved. Instead, a fixed masked value is returned.
        """
        return {
            key_record.service_name: "********"
            for key_record in self.get_user().external_api_keys
        }

    def get_user(self) -> UserTable:
        """Retrieve the user record."""
        statement = select(UserTable).where(UserTable.uuid == self.user.uuid)
        user = self.session.exec(statement).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found",
            )
        return user
