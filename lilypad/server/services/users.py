"""The `UserService` class for users."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select

from ..models import UserTable
from ..schemas import UserCreate
from .base import BaseService


class UserService(BaseService[UserTable, UserCreate]):
    """The service class for users."""

    table: type[UserTable] = UserTable
    create_model: type[UserCreate] = UserCreate

    def get_user(self) -> UserTable:
        """Get the user table."""
        user = self.session.exec(
            select(self.table).where(
                self.table.uuid == self.user.uuid,
            )
        ).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record for {self.table.__tablename__} not found",
            )
        return user

    def update_user_active_organization_uuid(
        self, organization_uuid: UUID
    ) -> UserTable:
        """Update the active organization UUID for a user."""
        user = self.get_user()
        user.active_organization_uuid = organization_uuid
        self.session.add(user)
        self.session.flush()
        self.session.refresh(user)
        return user

    def update_user_keys(self, data: dict) -> UserTable:
        """Update the keys for a user."""
        user = self.get_user()
        user.sqlmodel_update({"keys": data})
        self.session.add(user)
        self.session.flush()
        self.session.refresh(user)
        return user
