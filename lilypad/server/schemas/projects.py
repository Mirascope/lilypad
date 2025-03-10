"""Projects schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from .generations import GenerationPublic


class ProjectCreate(BaseModel):
    """Project Create Model."""

    name: str


class ProjectPublic(BaseModel):
    """Project Public Model."""

    uuid: UUID
    name: str
    organization_uuid: UUID
    generations: list[GenerationPublic] = Field(default_factory=list)
    created_at: datetime
