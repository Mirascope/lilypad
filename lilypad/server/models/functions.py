"""Functions table and models."""

from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship, SQLModel

from .base_organization_sql_model import BaseOrganizationSQLModel
from .table_names import (
    FUNCTION_TABLE_NAME,
    PROJECT_TABLE_NAME,
)

if TYPE_CHECKING:
    from .projects import ProjectTable
    from .versions import VersionTable


class _FunctionBase(SQLModel):
    """Base Function Model."""

    project_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROJECT_TABLE_NAME}.uuid"
    )
    name: str = Field(nullable=False, index=True, min_length=1)
    arg_types: dict[str, str] | None = Field(
        sa_column=Column(JSON), default_factory=dict
    )
    hash: str = Field(nullable=False, index=True, unique=True)
    code: str = Field(nullable=False)


class FunctionCreate(BaseModel):
    """Function create model."""

    name: str
    arg_types: dict[str, str] | None = None
    hash: str | None = None
    code: str | None = None


class FunctionPublic(_FunctionBase):
    """Function public model."""

    uuid: UUID


class FunctionTable(_FunctionBase, BaseOrganizationSQLModel, table=True):
    """Function table."""

    __tablename__ = FUNCTION_TABLE_NAME  # type: ignore

    project: "ProjectTable" = Relationship(back_populates="functions")
    versions: list["VersionTable"] = Relationship(
        back_populates="function", cascade_delete=True
    )
