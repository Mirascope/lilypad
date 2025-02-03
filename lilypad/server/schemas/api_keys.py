"""API key schemas."""

from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import computed_field
from sqlmodel import Field

from ..models.api_keys import _APIKeyBase

if TYPE_CHECKING:
    from . import ProjectPublic, UserPublic


class APIKeyPublic(_APIKeyBase):
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


class APIKeyCreate(_APIKeyBase):
    """API key create model"""

    key_hash: str | None = None
