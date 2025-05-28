"""The `ProjectService` class for projects."""

from typing import Any
from uuid import UUID

from ..models.projects import ProjectTable
from ..schemas.projects import ProjectCreate
from .base_organization import BaseOrganizationService


class ProjectService(BaseOrganizationService[ProjectTable, ProjectCreate]):
    """The service class for projects."""

    table: type[ProjectTable] = ProjectTable
    create_model: type[ProjectCreate] = ProjectCreate

    def find_record_no_organization(
        self,
        uuid: UUID,
        **filters: Any,
    ) -> ProjectTable:
        """Find a project by uuid without organization."""
        return super().find_record_by_uuid(uuid, **filters)
