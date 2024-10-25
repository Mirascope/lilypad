"""ProjectService class"""

from lilypad.models.projects import ProjectCreate
from lilypad.server.models import ProjectTable

from . import BaseService


class ProjectService(BaseService[ProjectTable, ProjectCreate]):
    """ProjectService class"""

    table: type[ProjectTable] = ProjectTable
    create_model: type[ProjectCreate] = ProjectCreate
