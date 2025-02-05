"""The `OrganizationInviteService` class for organization_invites."""

from fastapi import HTTPException, status
from sqlmodel import select

from ..models import OrganizationInviteTable
from ..schemas import OrganizationInviteCreate
from .base import BaseService


class OrganizationInviteService(
    BaseService[OrganizationInviteTable, OrganizationInviteCreate]
):
    """The service class for organization_invotes."""

    table: type[OrganizationInviteTable] = OrganizationInviteTable
    create_model: type[OrganizationInviteCreate] = OrganizationInviteCreate

    def find_record_by_token(self, token: str) -> OrganizationInviteTable:
        """Find record by token."""
        query = select(self.table).where(self.table.token == token)
        record_table = self.session.exec(query).first()
        if not record_table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record for {self.table.__tablename__} not found",
            )
        return record_table
