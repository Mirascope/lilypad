"""Tags schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from ..models.tags import _TagBase


class TagCreate(_TagBase):
    """Tag Create Model."""

    ...


class TagUpdate(BaseModel):
    """Tag Update Model."""

    project_uuid: UUID | None = None


class TagPublic(_TagBase):
    """Tag Public Model."""

    uuid: UUID
    created_at: datetime
