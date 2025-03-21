"""Environment SQL Model."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Index, text
from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from lilypad.server.models import BaseOrganizationSQLModel
from lilypad.server.models.table_names import ENVIRONMENT_TABLE_NAME

if TYPE_CHECKING:
    from .api_keys import APIKeyTable
    from .deployments import DeploymentTable


class EnvironmentBase(SQLModel):
    """Base Environment Model."""

    name: str = Field(nullable=False, index=True)
    description: str | None = Field(default=None)
    is_default: bool = Field(default=False, nullable=False)


class Environment(EnvironmentBase):
    """Environment model."""

    uuid: UUID


class EnvironmentTable(EnvironmentBase, BaseOrganizationSQLModel, table=True):
    """Environment table for different deployment targets (production, staging, development)."""

    __tablename__ = ENVIRONMENT_TABLE_NAME  # type: ignore
    __table_args__ = (
        UniqueConstraint("organization_uuid", "name", name="unique_org_env_name"),
        # Only one default environment per project
        Index(
            "ux_default_environment",
            "organization_uuid",
            unique=True,
            postgresql_where=text("is_default = true"),
        ),
    )
    deployments: list["DeploymentTable"] = Relationship(
        back_populates="environment", cascade_delete=True
    )
    api_keys: list["APIKeyTable"] = Relationship(
        back_populates="environment", cascade_delete=True
    )
