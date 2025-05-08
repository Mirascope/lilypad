"""The `OrganizationService` class for organizations."""

from collections.abc import Sequence
from typing import Any
from uuid import UUID

from sqlmodel import select

from ..models.organizations import OrganizationTable
from ..schemas.organizations import OrganizationCreate
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

    def update_record(
        self, uuid: UUID, data: dict, **filters: Any
    ) -> OrganizationTable:
        """Update a record by UUID."""
        return self.update_record_by_uuid(uuid, data, **filters)

    def find_records_by_filter(self, filters: dict) -> Sequence[OrganizationTable]:
        """Find records by filter."""
        return self.find_all_records(**filters)
