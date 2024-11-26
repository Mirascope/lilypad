"""Projects table and models."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from .base_sql_model import BaseSQLModel
from .functions import FunctionPublic
from .prompts import PromptPublic
from .table_names import ORGANIZATION_TABLE_NAME, PROJECT_TABLE_NAME
from .versions import VersionPublic

if TYPE_CHECKING:
    from .functions import FunctionTable
    from .organizations import OrganizationTable
    from .prompts import PromptTable
    from .versions import VersionTable


class _ProjectBase(BaseSQLModel):
    """Base Project Model."""

    name: str = Field(nullable=False, unique=True)


class ProjectCreate(_ProjectBase):
    """Project Create Model."""


class ProjectPublic(_ProjectBase):
    """Project Public Model."""

    id: int
    functions: list[FunctionPublic] = []
    prompts: list[PromptPublic] = []
    versions: list[VersionPublic] = []


class ProjectTable(_ProjectBase, table=True):
    """Project Table Model."""

    __tablename__ = PROJECT_TABLE_NAME  # type: ignore
    id: int | None = Field(default=None, primary_key=True)
    organization_uuid: UUID = Field(
        index=True, foreign_key=f"{ORGANIZATION_TABLE_NAME}.uuid"
    )
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
