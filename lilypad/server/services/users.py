"""The `UserService` class for users."""

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlmodel import Session

from .._utils import get_current_user
from ..db import get_session
from ..models import UserCreate, UserPublic, UserTable


class UserService:
    """The service class for users."""

    table: type[UserTable] = UserTable
    create_model: type[UserCreate] = UserCreate

    def update_user_active_organization_uuid(
        self, organization_uuid: UUID
    ) -> UserPublic:
        """Update the active organization UUID for a user."""
        self.user.active_organization_uuid = organization_uuid
        self.session.add(self.user)
        self.session.flush()
        self.session.refresh(self.user)
        return self.user

    def __init__(
        self,
        session: Annotated[Session, Depends(get_session)],
        user: Annotated[UserPublic, Depends(get_current_user)],
    ) -> None:
        self.session = session
        self.user = user
