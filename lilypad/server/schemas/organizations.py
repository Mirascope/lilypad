"""Organizations schemas."""

from uuid import UUID

from pydantic import BaseModel

from ..models.organizations import OrganizationBase


class OrganizationPublic(OrganizationBase):
    """Organization public model"""

    uuid: UUID


class OrganizationCreate(OrganizationBase):
    """Organization create model"""

    ...


class OrganizationUpdate(BaseModel):
    """Organization update model"""

    name: str | None = None
    license: str | None = None
