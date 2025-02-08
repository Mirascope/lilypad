"""API key schemas."""

from uuid import UUID

from pydantic import computed_field
from sqlmodel import Field

from ..models.api_keys import APIKeyBase
from .projects import ProjectPublic
from .users import UserPublic


class APIKeyPublic(APIKeyBase):
    """API key public model"""

    uuid: UUID
    key_hash: str = Field(exclude=True)
    user: "UserPublic"
    project: "ProjectPublic"

    @computed_field
    @property
    def prefix(self) -> str:
        """Return the first 8 characters of the key_hash."""
        return self.key_hash[:8]


class APIKeyCreate(APIKeyBase):
    """API key create model"""

    key_hash: str | None = None
