"""The `OrganizationService` class for organizations."""

from uuid import UUID

from sqlmodel import select

from ..models import OrganizationTable
from ..schemas import OrganizationCreate
from .base import BaseService


class OrganizationService(BaseService[OrganizationTable, OrganizationCreate]):
    """The service class for organizations."""

    table: type[OrganizationTable] = OrganizationTable
    create_model: type[OrganizationCreate] = OrganizationCreate

    def get_organization_license(self, organization_uuid: UUID) -> str | None:
        """Get license for an organization."""
        org = self.session.exec(
            select(self.table).where(self.table.uuid == organization_uuid)
        ).first()

        return org.license if org else None
