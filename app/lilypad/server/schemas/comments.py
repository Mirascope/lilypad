"""Comments schemas."""

from datetime import datetime, timezone
from uuid import UUID

from pydantic import BaseModel, ConfigDict, field_validator

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

    model_config = ConfigDict(from_attributes=True)  # type: ignore[assignment]

    uuid: UUID
    created_at: datetime

    @field_validator("updated_at", "created_at", mode="before")
    def add_timezone_if_missing(cls, value: datetime | None) -> datetime | None:
        """Add UTC timezone to naive datetimes from SQLite."""
        if value and not value.tzinfo:
            return value.replace(tzinfo=timezone.utc)
        return value
