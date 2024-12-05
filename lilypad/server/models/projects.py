"""Projects table and models."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base_organization_sql_model import BaseOrganizationSQLModel
from .functions import FunctionPublic
from .prompts import PromptPublic
from .table_names import PROJECT_TABLE_NAME
from .versions import VersionPublic

if TYPE_CHECKING:
    from .functions import FunctionTable
    from .organizations import OrganizationTable
    from .prompts import PromptTable
    from .versions import VersionTable


class _ProjectBase(SQLModel):
    """Base Project Model."""

    name: str = Field(nullable=False, unique=True)


class ProjectCreate(_ProjectBase):
    """Project Create Model."""

    ...


class ProjectPublic(_ProjectBase):
    """Project Public Model."""

    uuid: UUID
    functions: list[FunctionPublic] = []
    prompts: list[PromptPublic] = []
    versions: list[VersionPublic] = []


class ProjectTable(_ProjectBase, BaseOrganizationSQLModel, table=True):
    """Project Table Model."""

    __tablename__ = PROJECT_TABLE_NAME  # type: ignore
    functions: list["FunctionTable"] = Relationship(
        back_populates="project", cascade_delete=True
    )
    prompts: list["PromptTable"] = Relationship(
        back_populates="project", cascade_delete=True
    )
    versions: list["VersionTable"] = Relationship(
        back_populates="project", cascade_delete=True
    )
    organization: "OrganizationTable" = Relationship(back_populates="projects")
