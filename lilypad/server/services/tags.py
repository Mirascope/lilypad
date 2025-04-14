"""The `TagService` class for tags."""

from uuid import UUID

from sqlmodel import select

from ..models import TagTable
from ..schemas import TagCreate
from .base_organization import BaseOrganizationService


class TagService(BaseOrganizationService[TagTable, TagCreate]):
    """The service class for tags."""

    table: type[TagTable] = TagTable
    create_model: type[TagCreate] = TagCreate

    def find_or_create_tag(self, name: str, project_uuid: UUID) -> TagTable:
        """Find or create a tag by name and project UUID."""
        tag = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.name == name,
            )
        ).first()
        if tag:
            return tag
        else:
            new_tag_data = self.create_model(name=name, project_uuid=project_uuid)
            return self.create_record(new_tag_data)
