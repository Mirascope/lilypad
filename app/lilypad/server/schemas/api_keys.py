"""API key schemas."""

from datetime import datetime, timedelta, timezone
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, computed_field
from pydantic.types import AwareDatetime
from sqlmodel import DateTime, Field

from ..models.api_keys import APIKeyBase
from .environments import EnvironmentPublic
from .projects import ProjectPublic
from .users import UserPublic


class APIKeyPublic(APIKeyBase):
    """API key public model"""

    uuid: UUID
    key_hash: str = Field(exclude=True)
    user: "UserPublic"
    project: "ProjectPublic"
    environment: "EnvironmentPublic"

    @computed_field
    @property
    def prefix(self) -> str:
        """Return the first 8 characters of the key_hash."""
        return self.key_hash[:8]


class APIKeyCreate(BaseModel):
    """API key create model"""

    name: str = Field(nullable=False, min_length=1)
    expires_at: Annotated[datetime, AwareDatetime] = Field(
        sa_type=DateTime(timezone=True),  # pyright: ignore [reportArgumentType]
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=365),
        nullable=False,
        schema_extra={"format": "date-time"},
    )
    project_uuid: UUID
    environment_uuid: UUID
    key_hash: str | None = None
