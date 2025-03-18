"""Service for managing user secrets."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select

from .._utils import get_current_user
from .._utils.audit_logger import AuditAction, AuditLogger
from ..db import get_session
from ..models import UserTable
from ..schemas import UserPublic
from ..secret_manager.secret_manager import SecretManager
from ..secret_manager.secret_manager_factory import get_secret_manager
from ..services.base_organization import BaseOrganizationService


class UserSecretService(BaseOrganizationService):
    """Service for managing user API keys as encrypted secrets."""

    def __init__(
        self,
        session: Annotated[Session | None, Depends(get_session)] = None,
        user: Annotated[UserPublic | None, Depends(get_current_user)] = None,
        secret_manager: SecretManager | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        """Initialize the service."""
        super().__init__(session=session, user=user)  # pyright: ignore [reportArgumentType]
        self.secret_manager = secret_manager or get_secret_manager(session)  # pyright: ignore [reportArgumentType]
        self.audit_logger = audit_logger or AuditLogger(session)

    def store_api_key(self, service_name: str, api_key: str) -> str:
        """Store an API key for a service."""
        user_id = str(self.user.uuid)
        org_id = (
            str(self.user.active_organization_uuid)
            if self.user.active_organization_uuid
            else "personal"
        )

        name = f"user_{user_id}_org_{org_id}_{service_name}_key"
        description = f"API key for {service_name} for user {self.user.email}"

        try:
            secret_id = self.secret_manager.store_secret(name, api_key, description)

            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.CREATE,
                service_name=service_name,
                secret_id=secret_id,
                success=True,
                additional_info={"organization_id": org_id},
            )

            return secret_id
        except Exception as e:
            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.CREATE,
                service_name=service_name,
                secret_id="",
                success=False,
                additional_info={"error": str(e), "organization_id": org_id},
            )
            raise

    def get_api_key(self, service_name: str) -> str:
        """Get an API key for a service."""
        user = self.get_user()
        user_id = str(self.user.uuid)

        if service_name not in user.keys:
            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.READ,
                service_name=service_name,
                secret_id="",
                success=False,
                additional_info={"error": "API key not found"},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key for {service_name} not found",
            )

        secret_id = user.keys[service_name]

        try:
            api_key = self.secret_manager.get_secret(secret_id)

            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.READ,
                service_name=service_name,
                secret_id=secret_id,
                success=True,
            )

            return api_key
        except Exception as e:
            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.READ,
                service_name=service_name,
                secret_id=secret_id,
                success=False,
                additional_info={"error": str(e)},
            )
            raise

    def update_api_key(self, service_name: str, api_key: str) -> bool:
        """Update an API key for a service."""
        user = self.get_user()
        user_id = str(self.user.uuid)

        if service_name not in user.keys:
            # Store new key
            try:
                secret_id = self.store_api_key(service_name, api_key)

                # Update user.keys
                if not user.keys:
                    user.keys = {}
                user.keys[service_name] = secret_id
                self.session.add(user)
                self.session.commit()
                self.session.refresh(user)

                return True
            except Exception as e:
                self.audit_logger.log_secret_access(
                    user_id=user_id,
                    action=AuditAction.CREATE,
                    service_name=service_name,
                    secret_id="",
                    success=False,
                    additional_info={"error": str(e)},
                )
                raise
        else:
            # Update existing key
            secret_id = user.keys[service_name]
            try:
                result = self.secret_manager.update_secret(secret_id, api_key)

                self.audit_logger.log_secret_access(
                    user_id=user_id,
                    action=AuditAction.UPDATE,
                    service_name=service_name,
                    secret_id=secret_id,
                    success=result,
                )

                return result
            except Exception as e:
                self.audit_logger.log_secret_access(
                    user_id=user_id,
                    action=AuditAction.UPDATE,
                    service_name=service_name,
                    secret_id=secret_id,
                    success=False,
                    additional_info={"error": str(e)},
                )
                raise

    def delete_api_key(self, service_name: str) -> bool:
        """Delete an API key for a service."""
        user = self.get_user()
        user_id = str(self.user.uuid)

        if service_name not in user.keys:
            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.DELETE,
                service_name=service_name,
                secret_id="",
                success=False,
                additional_info={"error": "API key not found"},
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"API key for {service_name} not found",
            )

        secret_id = user.keys[service_name]

        try:
            result = self.secret_manager.delete_secret(secret_id)

            if result:
                del user.keys[service_name]
                self.session.add(user)
                self.session.commit()
                self.session.refresh(user)

            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.DELETE,
                service_name=service_name,
                secret_id=secret_id,
                success=result,
            )

            return result
        except Exception as e:
            self.session.rollback()

            self.audit_logger.log_secret_access(
                user_id=user_id,
                action=AuditAction.DELETE,
                service_name=service_name,
                secret_id=secret_id,
                success=False,
                additional_info={"error": str(e)},
            )
            raise

    def get_user(self) -> UserTable:
        """Get the user table."""
        user = self.session.exec(
            select(UserTable).where(
                UserTable.uuid == self.user.uuid,
            )
        ).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        return user
