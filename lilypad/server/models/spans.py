"""Traces model"""

import datetime
from enum import Enum
from typing import TYPE_CHECKING, Optional

from sqlmodel import Field, Relationship

from lilypad.server.models import BaseSQLModel

from .table_names import PROMPT_VERSION_TABLE_NAME, SPAN_TABLE_NAME

if TYPE_CHECKING:
    from lilypad.server.models import PromptVersionTable


class Scope(str, Enum):
    """Instrumentation Scope name of the span"""

    LILYPAD = "lilypad"
    LLM = "llm"


class SpanBase(BaseSQLModel):
    """Span base model"""

    prompt_version_id: int | None = Field(
        default=None, foreign_key=f"{PROMPT_VERSION_TABLE_NAME}.id"
    )
    scope: Scope = Field(nullable=False)
    data: str
    created_at: datetime.datetime = Field(
        default=datetime.datetime.now(datetime.UTC), nullable=False
    )
    parent_span_id: str | None = Field(
        default=None, foreign_key=f"{SPAN_TABLE_NAME}.id"
    )


class SpanTable(SpanBase, table=True):
    """Span table"""

    __tablename__ = SPAN_TABLE_NAME  # type: ignore

    id: str = Field(primary_key=True)
    prompt_version: "PromptVersionTable" = Relationship(back_populates="spans")

    child_spans: list["SpanTable"] = Relationship(back_populates="parent_span")

    parent_span: Optional["SpanTable"] = Relationship(
        back_populates="child_spans",
        sa_relationship_kwargs={"remote_side": "SpanTable.id"},
    )
