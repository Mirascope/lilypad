"""Spans table and models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from pydantic import model_validator
from sqlalchemy import JSON, Column, Index, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from .base_organization_sql_model import BaseOrganizationSQLModel
from .table_names import (
    PROJECT_TABLE_NAME,
    SPAN_TABLE_NAME,
    VERSION_TABLE_NAME,
)

if TYPE_CHECKING:
    from .versions import VersionPublic, VersionTable


class Scope(str, Enum):
    """Instrumentation Scope name of the span"""

    LILYPAD = "lilypad"
    LLM = "llm"


class _SpanBase(SQLModel):
    """Span base model"""

    span_id: str = Field(nullable=False, index=True, unique=True)
    project_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROJECT_TABLE_NAME}.uuid"
    )
    version_uuid: UUID | None = Field(
        default=None, foreign_key=f"{VERSION_TABLE_NAME}.uuid"
    )
    version_num: int | None = Field(default=None)
    scope: Scope = Field(nullable=False)
    data: dict = Field(sa_column=Column(JSON), default_factory=dict)
    parent_span_id: str | None = Field(
        default=None, foreign_key=f"{SPAN_TABLE_NAME}.span_id"
    )


class SpanCreate(_SpanBase):
    """Span create model"""

    ...


class SpanPublic(_SpanBase):
    """Span public model"""

    uuid: UUID
    display_name: str | None = None
    version: Optional["VersionPublic"] = None
    child_spans: list["SpanPublic"]
    created_at: datetime

    @model_validator(mode="before")
    @classmethod
    def convert_from_span_table(cls: type["SpanPublic"], data: Any) -> Any:
        """Convert SpanTable to SpanPublic."""
        if isinstance(data, SpanTable):
            span_public = cls._convert_span_table_to_public(data)
            return cls(**span_public)
        return data

    @classmethod
    def _convert_span_table_to_public(
        cls,
        span: "SpanTable",
    ) -> dict[str, Any]:
        """Set the display name based on the scope."""
        # TODO: Handle error cases where spans dont have attributes
        if span.scope == Scope.LILYPAD:
            display_name = span.data["attributes"]["lilypad.function_name"]
        else:  # Must be Scope.LLM because Scope is an Enum
            data = span.data
            display_name = f"{data['attributes']['gen_ai.system']} with '{data['attributes']['gen_ai.request.model']}'"
        child_spans = [
            cls._convert_span_table_to_public(child_span)
            for child_span in span.child_spans
        ]
        return {
            "display_name": display_name,
            "child_spans": child_spans,
            **span.model_dump(exclude={"child_spans"}),
        }


class SpanTable(_SpanBase, BaseOrganizationSQLModel, table=True):
    """Span table"""

    __tablename__ = SPAN_TABLE_NAME  # type: ignore
    __table_args__ = (UniqueConstraint("span_id"), Index("ix_spans_span_id", "span_id"))
    version: "VersionTable" = Relationship(back_populates="spans")
    child_spans: list["SpanTable"] = Relationship(
        back_populates="parent_span", cascade_delete=True
    )
    parent_span: Optional["SpanTable"] = Relationship(
        back_populates="child_spans",
        sa_relationship_kwargs={"remote_side": "SpanTable.span_id"},
    )
