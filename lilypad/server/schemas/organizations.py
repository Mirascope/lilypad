"""Organizations schemas."""

from uuid import UUID

from pydantic import BaseModel


class OrganizationPublic(BaseModel):
    """Organization public model"""

    uuid: UUID
    name: str
    license: str | None = None


class OrganizationCreate(BaseModel):
    """Organization create model"""

    name: str


class OrganizationUpdate(BaseModel):
    """Organization update model"""

    name: str
    license: str | None = None
