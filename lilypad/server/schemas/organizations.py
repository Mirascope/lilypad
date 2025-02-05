"""Users schemas."""

from uuid import UUID

from ..models.organizations import OrganizationBase


class OrganizationPublic(OrganizationBase):
    """Organization public model"""

    uuid: UUID


class OrganizationCreate(OrganizationBase):
    """Organization create model"""

    ...
