"""Environment SQL Model."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from .base_organization_sql_model import BaseOrganizationSQLModel
from .table_names import ENVIRONMENT_TABLE_NAME, PROJECT_TABLE_NAME

if TYPE_CHECKING:
    from .deployments import DeploymentTable
    from .projects import ProjectTable


class EnvironmentBase(SQLModel):
    """Base Environment Model."""

    name: str = Field(nullable=False, index=True)
    description: str | None = Field(default=None)
    project_uuid: UUID = Field(
        index=True, foreign_key=f"{PROJECT_TABLE_NAME}.uuid", ondelete="CASCADE"
    )


class EnvironmentTable(EnvironmentBase, BaseOrganizationSQLModel, table=True):
    """Environment table for different deployment targets (production, staging, development)."""

    __tablename__ = ENVIRONMENT_TABLE_NAME  # type: ignore
    __table_args__ = (
        UniqueConstraint(
            "organization_uuid", "project_uuid", "name", name="unique_org_proj_env_name"
        ),
    )
    deployments: list["DeploymentTable"] = Relationship(
        back_populates="environment", cascade_delete=True
    )
    project: "ProjectTable" = Relationship(back_populates="environments")
