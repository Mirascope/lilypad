"""SpanTagLink table."""

from uuid import UUID

from sqlmodel import Field, SQLModel

from .table_names import SPAN_TABLE_NAME, SPAN_TAG_LINK_TABLE_NAME, TAG_TABLE_NAME


class SpanTagLink(SQLModel, table=True):
    """SpanTagLink table."""

    __tablename__ = SPAN_TAG_LINK_TABLE_NAME  # type: ignore
    span_uuid: UUID | None = Field(
        default=None, foreign_key=f"{SPAN_TABLE_NAME}.uuid", primary_key=True
    )
    tag_uuid: UUID | None = Field(
        default=None, foreign_key=f"{TAG_TABLE_NAME}.uuid", primary_key=True
    )
