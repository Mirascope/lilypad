"""The `ProjectService` class for projects."""

from ..models.projects import ProjectTable
from ..schemas.projects import ProjectCreate
from .base_organization import BaseOrganizationService


class ProjectService(BaseOrganizationService[ProjectTable, ProjectCreate]):
    """The service class for projects."""

    table: type[ProjectTable] = ProjectTable
    create_model: type[ProjectCreate] = ProjectCreate
