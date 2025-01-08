"""Spans table and models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any, Optional
from uuid import UUID

from pydantic import model_validator
from sqlalchemy import Index, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from .base_organization_sql_model import BaseOrganizationSQLModel
from .base_sql_model import get_json_column
from .generations import GenerationPublic
from .prompts import PromptPublic
from .response_models import ResponseModelPublic
from .table_names import (
    GENERATION_TABLE_NAME,
    PROJECT_TABLE_NAME,
    PROMPT_TABLE_NAME,
    RESPONSE_MODEL_TABLE_NAME,
    SPAN_TABLE_NAME,
)

if TYPE_CHECKING:
    from .generations import GenerationTable
    from .prompts import PromptTable
    from .response_models import ResponseModelTable


class Scope(str, Enum):
    """Instrumentation Scope name of the span"""

    LILYPAD = "lilypad"
    LLM = "llm"


class SpanType(str, Enum):
    """Span type"""

    GENERATION = "generation"
    PROMPT = "prompt"


class _SpanBase(SQLModel):
    """Span base model"""

    span_id: str = Field(nullable=False, index=True, unique=True)
    project_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROJECT_TABLE_NAME}.uuid"
    )
    generation_uuid: UUID | None = Field(
        default=None, foreign_key=f"{GENERATION_TABLE_NAME}.uuid"
    )
    prompt_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROMPT_TABLE_NAME}.uuid"
    )
    response_model_uuid: UUID | None = Field(
        default=None, foreign_key=f"{RESPONSE_MODEL_TABLE_NAME}.uuid"
    )
    type: SpanType | None = Field(default=None)
    cost: float | None = Field(default=None)
    scope: Scope = Field(nullable=False)
    data: dict = Field(sa_column=get_json_column(), default_factory=dict)
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
    generation: GenerationPublic | None = None
    prompt: PromptPublic | None = None
    response_model: ResponseModelPublic | None = None
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
            span_type = span.data["attributes"]["lilypad.type"]
            if span_type == SpanType.GENERATION:
                display_name = span.data["attributes"]["lilypad.generation.name"]
            elif span_type == SpanType.PROMPT:
                display_name = span.data["attributes"]["lilypad.prompt.name"]
            else:
                display_name = None
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
    generation: Optional["GenerationTable"] = Relationship(back_populates="spans")
    prompt: Optional["PromptTable"] = Relationship(back_populates="spans")
    response_model: Optional["ResponseModelTable"] = Relationship(
        back_populates="spans"
    )
    child_spans: list["SpanTable"] = Relationship(
        back_populates="parent_span", cascade_delete=True
    )
    parent_span: Optional["SpanTable"] = Relationship(
        back_populates="child_spans",
        sa_relationship_kwargs={"remote_side": "SpanTable.span_id"},
    )
