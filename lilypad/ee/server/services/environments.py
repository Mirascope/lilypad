"""Service for managing environments."""

from ....server.services.base_organization import BaseOrganizationService
from ..models.environments import EnvironmentTable
from ..schemas.environments import EnvironmentCreate


class EnvironmentService(BaseOrganizationService[EnvironmentTable, EnvironmentCreate]):
    """Service for managing environments."""

    table: type[EnvironmentTable] = EnvironmentTable
    create_model: type[EnvironmentCreate] = EnvironmentCreate
