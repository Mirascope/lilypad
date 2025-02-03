"""Users schemas."""

from uuid import UUID

from ..models.organizations import _OrganizationBase


class OrganizationPublic(_OrganizationBase):
    """Organization public model"""

    uuid: UUID


class OrganizationCreate(_OrganizationBase):
    """Organization create model"""

    ...
