"""Response Model for the database."""

from typing import TYPE_CHECKING, Any
from uuid import UUID

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from ..._utils import DependencyInfo
from .base_organization_sql_model import BaseOrganizationSQLModel
from .table_names import PROJECT_TABLE_NAME

if TYPE_CHECKING:
    from .generations import GenerationTable
    from .projects import ProjectTable


class _ResponseModelBase(SQLModel):
    """Base Response Model."""

    project_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROJECT_TABLE_NAME}.uuid"
    )
    name: str = Field(nullable=False, index=True, min_length=1)
    signature: str = Field(nullable=False)
    code: str = Field(nullable=False)
    hash: str = Field(nullable=False, index=True)
    dependencies: dict[str, DependencyInfo] = Field(
        sa_column=Column(JSON), default_factory=dict
    )
    schema_data: dict[str, Any] = Field(sa_column=Column(JSON), default_factory=dict)
    examples: list[dict[str, Any]] = Field(sa_column=Column(JSON), default_factory=list)
    is_active: bool = Field(default=False)


class ResponseModelPublic(_ResponseModelBase):
    """Public model for response models."""

    uuid: UUID


class ResponseModelCreate(_ResponseModelBase):
    """Create model for response models."""


class ResponseModelTable(_ResponseModelBase, BaseOrganizationSQLModel, table=True):
    """Table for response models."""

    __tablename__ = "response_models"  # pyright: ignore [reportAssignmentType]

    project: "ProjectTable" = Relationship(back_populates="response_models")
    generations: list["GenerationTable"] = Relationship(
        back_populates="response_model", cascade_delete=True
    )