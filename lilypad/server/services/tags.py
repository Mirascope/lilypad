"""The `TagService` class for tags."""

from ..models.tags import TagTable
from ..schemas.tags import TagCreate
from .base_organization import BaseOrganizationService


class TagService(BaseOrganizationService[TagTable, TagCreate]):
    """The service class for tags."""

    table: type[TagTable] = TagTable
    create_model: type[TagCreate] = TagCreate
