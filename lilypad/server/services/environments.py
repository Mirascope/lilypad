"""Service for managing environments."""

from ..models.environments import EnvironmentTable
from ..schemas.environments import EnvironmentCreate
from .base_organization import BaseOrganizationService


class EnvironmentService(BaseOrganizationService[EnvironmentTable, EnvironmentCreate]):
    """Service for managing environments."""

    table: type[EnvironmentTable] = EnvironmentTable
    create_model: type[EnvironmentCreate] = EnvironmentCreate
