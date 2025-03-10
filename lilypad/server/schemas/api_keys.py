"""API key schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, computed_field

from .projects import ProjectPublic
from .users import UserPublic


class APIKeyPublic(BaseModel):
    """API key public model"""

    uuid: UUID
    name: str
    expires_at: datetime
    project_uuid: UUID
    organization_uuid: UUID
    key_hash: str
    user: UserPublic
    project: ProjectPublic

    @computed_field
    @property
    def prefix(self) -> str:
        """Return the first 8 characters of the key_hash."""
        return self.key_hash[:8]


class APIKeyCreate(BaseModel):
    """API key create model"""

    name: str
    expires_at: datetime
    project_uuid: UUID
    organization_uuid: UUID
    key_hash: str | None = None
