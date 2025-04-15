"""Comments schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from ..models.comments import _CommentBase


class CommentCreate(BaseModel):
    """Comment Create Model."""

    text: str
    span_uuid: UUID
    parent_comment_uuid: UUID | None = None


class CommentUpdate(BaseModel):
    """Comment Update Model."""

    text: str | None = None
    is_edited: bool | None = None


class CommentPublic(_CommentBase):
    """Comment Public Model."""

    uuid: UUID
    created_at: datetime
