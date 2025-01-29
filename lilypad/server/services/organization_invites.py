"""The `OrganizationInviteService` class for organization_invites."""

from uuid import UUID

from sqlmodel import select

from ..models import OrganizationInviteCreate, OrganizationInviteTable
from .base import BaseService
from .base_organization import BaseOrganizationService


class OrganizationInviteService(
    BaseOrganizationService[OrganizationInviteTable, OrganizationInviteCreate]
):
    """The service class for organization_invotes."""

    table: type[OrganizationInviteTable] = OrganizationInviteTable
    create_model: type[OrganizationInviteCreate] = OrganizationInviteCreate

    def delete_record_by_email(self, organization_uuid: UUID) -> bool:
        """Delete record by email."""
        record_table = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == organization_uuid,
                self.table.email == self.user.email,
            )
        ).first()
        try:
            self.session.delete(record_table)
        except Exception:
            return False
        return True
