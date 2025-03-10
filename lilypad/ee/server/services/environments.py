"""Service for managing environments."""

from lilypad.ee.server.models.environments import EnvironmentTable
from lilypad.ee.server.schemas.environments import EnvironmentCreate
from lilypad.server.services.base_organization import BaseOrganizationService


class EnvironmentService(BaseOrganizationService[EnvironmentTable, EnvironmentCreate]):
    """Service for managing environments."""

    table: type[EnvironmentTable] = EnvironmentTable
    create_model: type[EnvironmentCreate] = EnvironmentCreate
