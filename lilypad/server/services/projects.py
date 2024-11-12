"""The `ProjectService` class for projects."""

from ..models import ProjectCreate, ProjectTable
from .base import BaseService


class ProjectService(BaseService[ProjectTable, ProjectCreate]):
    """The service class for projects."""

    table: type[ProjectTable] = ProjectTable
    create_model: type[ProjectCreate] = ProjectCreate
