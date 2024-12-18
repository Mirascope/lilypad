"""The `UserService` class for users."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select

from .._utils import get_current_user
from ..db import get_session
from ..models import UserCreate, UserPublic, UserTable


class UserService:
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

    def __init__(
        self,
        session: Annotated[Session, Depends(get_session)],
        user: Annotated[UserPublic, Depends(get_current_user)],
    ) -> None:
        self.session = session
        self.user = user
