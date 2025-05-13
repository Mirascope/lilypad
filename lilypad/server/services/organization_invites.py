"""The EE `OrganizationInviteService` class for organization_invites."""

from sqlmodel import select

from ..models.organization_invites import OrganizationInviteTable
from ..schemas.organization_invites import OrganizationInviteCreate
from .base import BaseService


class OrganizationInviteService(
    BaseService[OrganizationInviteTable, OrganizationInviteCreate]
):
    """The service class for organization_invotes."""

    table: type[OrganizationInviteTable] = OrganizationInviteTable
    create_model: type[OrganizationInviteCreate] = OrganizationInviteCreate

    def find_record_by_token(self, token: str) -> OrganizationInviteTable | None:
        """Find record by token."""
        query = select(self.table).where(self.table.token == token)
        return self.session.exec(query).first()
