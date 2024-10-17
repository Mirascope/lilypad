"""Traces model"""

import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship

from lilypad.server.models import BaseSQLModel

from .table_names import (
    PROJECT_TABLE_NAME,
    SPAN_TABLE_NAME,
    VERSION_TABLE_NAME,
)

if TYPE_CHECKING:
    from lilypad.server.models import VersionTable


class Scope(str, Enum):
    """Instrumentation Scope name of the span"""

    LILYPAD = "lilypad"
    LLM = "llm"


class SpanBase(BaseSQLModel):
    """Span base model"""

    project_id: int | None = Field(default=None, foreign_key=f"{PROJECT_TABLE_NAME}.id")
    version_id: int | None = Field(default=None, foreign_key=f"{VERSION_TABLE_NAME}.id")
    scope: Scope = Field(nullable=False)
    version: int | None = Field(default=None)
    created_at: datetime.datetime = Field(
        default=datetime.datetime.now(datetime.timezone.utc), nullable=False
    )
    parent_span_id: str | None = Field(
        default=None, foreign_key=f"{SPAN_TABLE_NAME}.id"
    )


class SpanTable(SpanBase, table=True):
    """Span table"""

    __tablename__ = SPAN_TABLE_NAME  # type: ignore

    id: str = Field(primary_key=True)
    data: dict = Field(sa_column=Column(JSON), default_factory=dict)
    version_table: "VersionTable" = Relationship(back_populates="spans")

    child_spans: list["SpanTable"] = Relationship(back_populates="parent_span")

    parent_span: Optional["SpanTable"] = Relationship(
        back_populates="child_spans",
        sa_relationship_kwargs={"remote_side": "SpanTable.id"},
    )
