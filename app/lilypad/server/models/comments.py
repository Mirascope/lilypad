"""Comments models."""

from datetime import datetime
from typing import TYPE_CHECKING, Annotated, Optional
from uuid import UUID

from pydantic import AwareDatetime
from sqlalchemy import func
from sqlmodel import DateTime, Field, Relationship, SQLModel

from .base_organization_sql_model import BaseOrganizationSQLModel
from .table_names import COMMENT_TABLE_NAME, SPAN_TABLE_NAME, USER_TABLE_NAME

if TYPE_CHECKING:
    from .spans import SpanTable
    from .users import UserTable


class _CommentBase(SQLModel):
    """Base Comment Model."""

    text: str = Field(nullable=False)
    user_uuid: UUID = Field(
        index=True, foreign_key=f"{USER_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    span_uuid: UUID = Field(
        index=True, foreign_key=f"{SPAN_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    parent_comment_uuid: UUID | None = Field(
        default=None,
        index=True,
        foreign_key=f"{COMMENT_TABLE_NAME}.uuid",
        ondelete="CASCADE",
    )
    updated_at: Annotated[datetime, AwareDatetime] | None = Field(
        sa_type=DateTime(timezone=True),  # pyright: ignore [reportArgumentType]
        sa_column_kwargs={
            "onupdate": func.now(kwargs={"timezone": True}),
            "server_default": func.now(kwargs={"timezone": True}),
        },
        default=None,
        index=True,
        schema_extra={"format": "date-time"},
    )
    is_edited: bool = Field(default=False)


class CommentTable(_CommentBase, BaseOrganizationSQLModel, table=True):
    """Comment Table Model."""

    __tablename__ = COMMENT_TABLE_NAME  # type: ignore
    user: "UserTable" = Relationship(back_populates="comments")
    span: "SpanTable" = Relationship(back_populates="comments")
    child_comments: list["CommentTable"] = Relationship(
        back_populates="parent_comment",
        sa_relationship_kwargs={
            "lazy": "selectin",  # codespell:ignore selectin
            "order_by": "CommentTable.created_at.desc()",
        },
        cascade_delete=True,
    )
    parent_comment: Optional["CommentTable"] = Relationship(
        back_populates="child_comments",
        sa_relationship_kwargs={
            "remote_side": "CommentTable.uuid",
        },
    )
