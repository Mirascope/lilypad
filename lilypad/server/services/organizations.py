"""The `OrganizationService` class for organizations."""

from ..models import OrganizationCreate, OrganizationTable
from .base import BaseService


class OrganizationService(BaseService[OrganizationTable, OrganizationCreate]):
    """The service class for organizations."""

    table: type[OrganizationTable] = OrganizationTable
    create_model: type[OrganizationCreate] = OrganizationCreate
