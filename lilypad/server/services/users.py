"""The `UserService` class for users."""

from uuid import UUID

from ..models import UserCreate, UserPublic, UserTable
from .base import BaseService


class UserService(BaseService[UserTable, UserCreate]):
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
