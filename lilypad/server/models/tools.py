"""Tool for the database."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from ..._utils import DependencyInfo
from .base_organization_sql_model import BaseOrganizationSQLModel
from .base_sql_model import get_json_column
from .table_names import PROJECT_TABLE_NAME, TOOL_TABLE_NAME, GENERATION_TABLE_NAME, SPAN_TABLE_NAME

if TYPE_CHECKING:
    from .generations import GenerationTable
    from .projects import ProjectTable
    from .spans import SpanTable


class _ToolBase(SQLModel):
    """Base Response Model."""

    project_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROJECT_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    name: str = Field(nullable=False, index=True, min_length=1)
    signature: str = Field(nullable=False)
    code: str = Field(nullable=False)
    hash: str = Field(nullable=False, index=True)
    dependencies: dict[str, DependencyInfo] = Field(
        sa_column=get_json_column(), default_factory=dict
    )
    is_active: bool = Field(default=False)


class ToolTable(_ToolBase, BaseOrganizationSQLModel, table=True):
    """Table for response models."""

    __tablename__ = TOOL_TABLE_NAME  # pyright: ignore [reportAssignmentType]

    project_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROJECT_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    span_uuid: UUID | None = Field(
        default=None, foreign_key=f"{SPAN_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    generation_uuid: UUID | None = Field(
        default=None, foreign_key=f"{GENERATION_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    project: "ProjectTable" = Relationship(back_populates="tools")
    span: "SpanTable" = Relationship(back_populates="tools")
    generation: "GenerationTable" = Relationship(back_populates="tools")
