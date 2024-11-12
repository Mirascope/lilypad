"""Functions table and models."""

from typing import TYPE_CHECKING

from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship

from .base_sql_model import BaseSQLModel
from .table_names import FUNCTION_TABLE_NAME, PROJECT_TABLE_NAME

if TYPE_CHECKING:
    from .projects import ProjectTable
    from .versions import VersionTable


class _FunctionBase(BaseSQLModel):
    """Base Function Model."""

    name: str = Field(nullable=False, index=True)
    hash: str = Field(nullable=False, index=True)
    code: str
    arg_types: dict[str, str] | None = Field(
        sa_column=Column(JSON), default_factory=dict
    )


class FunctionCreate(_FunctionBase):
    """Function create model."""

    project_id: int


class FunctionPublic(_FunctionBase):
    """Function public model."""

    id: int


class FunctionTable(_FunctionBase, table=True):
    """Function table."""

    __tablename__ = FUNCTION_TABLE_NAME  # type: ignore

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    project_id: int = Field(foreign_key=f"{PROJECT_TABLE_NAME}.id")
    project: "ProjectTable" = Relationship(back_populates="functions")
    versions: list["VersionTable"] = Relationship(
        back_populates="function", cascade_delete=True
    )