"""The `UserOrganizationService` class for user_organizations."""

from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlmodel import select

from ..models import UserOrganizationTable
from ..schemas import UserOrganizationCreate
from .base_organization import BaseOrganizationService


class UserOrganizationService(
    BaseOrganizationService[UserOrganizationTable, UserOrganizationCreate]
):
    """The service class for user_organizations."""

    table: type[UserOrganizationTable] = UserOrganizationTable
    create_model: type[UserOrganizationCreate] = UserOrganizationCreate

    def get_active_user_organization(self) -> UserOrganizationTable:
        """Get the active organization for a user."""
        user_organization = self.session.exec(
            select(self.table).where(
                self.table.user_uuid == self.user.uuid,
                self.table.organization_uuid == self.user.active_organization_uuid,
            )
        ).first()
        if not user_organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record for {self.table.__tablename__} not found",
            )
        return user_organization

    def get_users_by_active_organization(self) -> Sequence[UserOrganizationTable]:
        """Get all users from the active organization."""
        user_organizations = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
            )
        ).all()
        return user_organizations
