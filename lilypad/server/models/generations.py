"""Generations table and models."""

from typing import TYPE_CHECKING, Optional
from uuid import UUID

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from ..._utils import DependencyInfo
from .base_organization_sql_model import BaseOrganizationSQLModel
from .prompts import PromptPublic
from .table_names import (
    GENERATION_TABLE_NAME,
    PROJECT_TABLE_NAME,
    PROMPT_TABLE_NAME,
)

if TYPE_CHECKING:
    from .projects import ProjectTable
    from .prompts import PromptTable
    from .spans import SpanTable


class _GenerationBase(SQLModel):
    """Base Generation Model."""

    project_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROJECT_TABLE_NAME}.uuid"
    )
    prompt_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROMPT_TABLE_NAME}.uuid"
    )
    name: str = Field(nullable=False, index=True, min_length=1)
    signature: str = Field(nullable=False)
    code: str = Field(nullable=False)
    hash: str = Field(nullable=False, index=True, unique=True)
    dependencies: dict[str, DependencyInfo] = Field(
        sa_column=Column(JSON), default_factory=dict
    )
    arg_types: dict[str, str] = Field(sa_column=Column(JSON), default_factory=dict)


class GenerationCreate(_GenerationBase):
    """Generation create model."""


class GenerationUpdate(SQLModel):
    """Generation update model."""

    prompt_uuid: UUID | None = None


class GenerationPublic(_GenerationBase):
    """Generation public model."""

    uuid: UUID
    prompt: PromptPublic | None = None


class GenerationTable(_GenerationBase, BaseOrganizationSQLModel, table=True):
    """Generation table."""

    __tablename__ = GENERATION_TABLE_NAME  # type: ignore

    project: "ProjectTable" = Relationship(back_populates="generations")
    spans: list["SpanTable"] = Relationship(
        back_populates="generation", cascade_delete=True
    )
    prompt: Optional["PromptTable"] = Relationship(back_populates="generations")
