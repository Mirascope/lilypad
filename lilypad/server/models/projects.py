"""Projects table and models."""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from .base_organization_sql_model import BaseOrganizationSQLModel
from .generations import GenerationPublic
from .prompts import PromptPublic
from .response_models import ResponseModelPublic
from .table_names import PROJECT_TABLE_NAME

if TYPE_CHECKING:
    from .api_keys import APIKeyTable
    from .generations import GenerationTable
    from .organizations import OrganizationTable
    from .prompts import PromptTable
    from .response_models import ResponseModelTable


class _ProjectBase(SQLModel):
    """Base Project Model."""

    name: str = Field(nullable=False)


class ProjectCreate(_ProjectBase):
    """Project Create Model."""

    ...


class ProjectPublic(_ProjectBase):
    """Project Public Model."""

    uuid: UUID
    generations: list[GenerationPublic] = []
    prompts: list[PromptPublic] = []
    response_models: list[ResponseModelPublic] = []
    created_at: datetime


class ProjectTable(_ProjectBase, BaseOrganizationSQLModel, table=True):
    """Project Table Model."""

    __tablename__ = PROJECT_TABLE_NAME  # type: ignore
    __table_args__ = (
        UniqueConstraint("organization_uuid", "name", name="unique_project_name"),
    )
    generations: list["GenerationTable"] = Relationship(
        back_populates="project", cascade_delete=True
    )
    prompts: list["PromptTable"] = Relationship(
        back_populates="project", cascade_delete=True
    )
    response_models: list["ResponseModelTable"] = Relationship(
        back_populates="project", cascade_delete=True
    )
    organization: "OrganizationTable" = Relationship(back_populates="projects")
    api_keys: list["APIKeyTable"] = Relationship(
        back_populates="project", cascade_delete=True
    )
