"""Generations models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from mirascope.core.base import CommonCallParams
from sqlalchemy import Column
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from ..._utils import DependencyInfo
from .base_organization_sql_model import BaseOrganizationSQLModel
from .base_sql_model import JSONTypeDecorator, get_json_column
from .table_names import (
    GENERATION_TABLE_NAME,
    PROJECT_TABLE_NAME,
)

if TYPE_CHECKING:
    from ...ee.server.models.annotations import AnnotationTable
    from .projects import ProjectTable
    from .spans import SpanTable


class _GenerationBase(SQLModel):
    """Base Generation Model."""

    project_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROJECT_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    version_num: int | None = Field(default=None)
    name: str = Field(nullable=False, index=True, min_length=1)
    signature: str = Field(nullable=False)
    code: str = Field(nullable=False)
    hash: str = Field(nullable=False, index=True)
    dependencies: dict[str, DependencyInfo] = Field(
        sa_column=get_json_column(), default_factory=dict
    )
    arg_types: dict[str, str] = Field(sa_column=get_json_column(), default_factory=dict)
    archived: datetime | None = Field(default=None, index=True)
    custom_id: str | None = Field(default=None, index=True)
    prompt_template: str | None = Field(default=None)
    provider: str | None = Field(default=None)
    model: str | None = Field(default=None)
    call_params: CommonCallParams = Field(
        sa_column=Column(JSONTypeDecorator, nullable=False), default_factory=dict
    )
    is_default: bool | None = Field(default=False, index=True, nullable=True)
    is_managed: bool | None = Field(default=False, index=True, nullable=True)


class GenerationUpdate(SQLModel):
    """Generation update model."""

    ...


class GenerationTable(_GenerationBase, BaseOrganizationSQLModel, table=True):
    """Generation table."""

    __tablename__ = GENERATION_TABLE_NAME  # type: ignore
    __table_args__ = (
        UniqueConstraint("project_uuid", "hash", name="unique_project_generation_hash"),
    )
    project: "ProjectTable" = Relationship(back_populates="generations")
    spans: list["SpanTable"] = Relationship(
        back_populates="generation", cascade_delete=True
    )
    annotations: list["AnnotationTable"] = Relationship(
        back_populates="generation",
        sa_relationship_kwargs={"lazy": "selectin"},  # codespell:ignore selectin
        cascade_delete=True,
    )
