"""Prompts table and models."""

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from mirascope.core.base import CommonCallParams
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from .base_organization_sql_model import BaseOrganizationSQLModel
from .table_names import PROJECT_TABLE_NAME, PROMPT_TABLE_NAME

if TYPE_CHECKING:
    from .generations import GenerationTable
    from .projects import ProjectTable
    from .spans import SpanTable


class Provider(str, Enum):
    """Provider name enum"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"


class _PromptBase(SQLModel):
    """Base Prompt Model."""

    project_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROJECT_TABLE_NAME}.uuid"
    )
    name: str = Field(nullable=False, index=True, min_length=1)
    signature: str = Field(nullable=False)
    code: str = Field(nullable=False)
    hash: str = Field(nullable=False, index=True)
    template: str


class PromptPublic(_PromptBase):
    """Prompt public model."""

    uuid: UUID
    call_params: CommonCallParams | None = None


class PromptCreate(_PromptBase):
    """Prompt create model."""

    call_params: CommonCallParams | None = None


class PromptTable(_PromptBase, BaseOrganizationSQLModel, table=True):
    """Prompt table."""

    __tablename__ = PROMPT_TABLE_NAME  # type: ignore

    call_params: dict | None = Field(sa_column=Column(JSON), default_factory=dict)
    project: "ProjectTable" = Relationship(back_populates="prompts")
    spans: list["SpanTable"] = Relationship(
        back_populates="prompt", cascade_delete=True
    )
    generations: list["GenerationTable"] = Relationship(
        back_populates="prompt", cascade_delete=True
    )
