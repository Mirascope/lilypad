"""Projects models."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from .base_organization_sql_model import BaseOrganizationSQLModel
from .table_names import PROJECT_TABLE_NAME

if TYPE_CHECKING:
    from ...ee.server.models.annotations import AnnotationTable
    from .api_keys import APIKeyTable
    from .deployments import DeploymentTable
    from .functions import FunctionTable
    from .organizations import OrganizationTable
    from .tags import TagTable


class _ProjectBase(SQLModel):
    """Base Project Model."""

    name: str = Field(nullable=False)


class ProjectTable(_ProjectBase, BaseOrganizationSQLModel, table=True):
    """Project Table Model."""

    __tablename__ = PROJECT_TABLE_NAME  # type: ignore
    __table_args__ = (
        UniqueConstraint("organization_uuid", "name", name="unique_project_name"),
    )
    functions: list["FunctionTable"] = Relationship(
        back_populates="project", cascade_delete=True
    )
    organization: "OrganizationTable" = Relationship(back_populates="projects")
    api_keys: list["APIKeyTable"] = Relationship(
        back_populates="project", cascade_delete=True
    )
    annotations: list["AnnotationTable"] = Relationship(
        back_populates="project", cascade_delete=True
    )
    deployments: list["DeploymentTable"] = Relationship(
        back_populates="project", cascade_delete=True
    )
    tags: list["TagTable"] = Relationship(back_populates="project", cascade_delete=True)
