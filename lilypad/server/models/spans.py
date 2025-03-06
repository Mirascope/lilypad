"""Spans models."""

from enum import Enum
from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel, text

from .base_organization_sql_model import BaseOrganizationSQLModel
from .base_sql_model import get_json_column
from .table_names import (
    GENERATION_TABLE_NAME,
    PROJECT_TABLE_NAME,
    SPAN_TABLE_NAME,
)

if TYPE_CHECKING:
    from ...ee.server.models.annotations import AnnotationTable
    from .generations import GenerationTable


class Scope(str, Enum):
    """Instrumentation Scope name of the span"""

    LILYPAD = "lilypad"
    LLM = "llm"


class SpanType(str, Enum):
    """Span type"""

    GENERATION = "generation"
    TRACE = "trace"


class SpanBase(SQLModel):
    """Span base model"""

    span_id: str = Field(nullable=False, index=True, unique=True)
    generation_uuid: UUID | None = Field(
        default=None, foreign_key=f"{GENERATION_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    type: SpanType | None = Field(default=None)
    cost: float | None = Field(default=None)
    scope: Scope = Field(nullable=False)
    input_tokens: float | None = Field(default=None)
    output_tokens: float | None = Field(default=None)
    duration_ms: float | None = Field(default=None)
    data: dict = Field(sa_column=get_json_column(), default_factory=dict)
    parent_span_id: str | None = Field(
        default=None,
        index=True,
        foreign_key=f"{SPAN_TABLE_NAME}.span_id",
        ondelete="CASCADE",
    )


class SpanTable(SpanBase, BaseOrganizationSQLModel, table=True):
    """Span table"""

    __tablename__ = SPAN_TABLE_NAME  # type: ignore
    __table_args__ = (
        UniqueConstraint("span_id"),
        Index("ix_spans_span_id", "span_id"),
        Index(
            "idx_spans_project_parent_filtered",
            "project_uuid",
            postgresql_where=text("parent_span_id IS NULL"),
        ),
    )
    project_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROJECT_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    generation: Optional["GenerationTable"] = Relationship(back_populates="spans")
    annotations: list["AnnotationTable"] = Relationship(
        back_populates="span",
        sa_relationship_kwargs={"lazy": "selectin"},  # codespell:ignore selectin
        cascade_delete=True,
    )
    child_spans: list["SpanTable"] = Relationship(
        back_populates="parent_span",
        sa_relationship_kwargs={
            "lazy": "selectin",  # codespell:ignore selectin
        },
        cascade_delete=True,
    )
    parent_span: Optional["SpanTable"] = Relationship(
        back_populates="child_spans",
        sa_relationship_kwargs={
            "remote_side": "SpanTable.span_id",
        },
    )
