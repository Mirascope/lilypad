"""The `UserOrganizationService` class for user_organizations."""

from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import func, select

from ....server.services.base_organization import BaseOrganizationService
from ...server.models.user_organizations import UserOrganizationTable
from ...server.schemas.user_organizations import UserOrganizationCreate


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

    def find_user_organizations(self) -> Sequence[UserOrganizationTable]:
        """Find all user organizations."""
        user_organizations = self.session.exec(
            select(self.table).where(
                self.table.user_uuid == self.user.uuid,
            )
        ).all()
        return user_organizations

    def get_users_by_active_organization(self) -> Sequence[UserOrganizationTable]:
        """Get all users from the active organization."""
        user_organizations = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
            )
        ).all()
        return user_organizations

    def count_users_in_organization(self, organization_uuid: UUID) -> int:
        """Count the number of users in the active organization."""
        query = (
            select(func.count())
            .select_from(self.table)
            .where(
                self.table.organization_uuid == organization_uuid,
            )
        )

        count = self.session.exec(query).one()
        return count
