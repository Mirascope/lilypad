"""Deployment SQLModel."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from lilypad.server.models import BaseOrganizationSQLModel
from lilypad.server.models.table_names import (
    DEPLOYMENT_TABLE_NAME,
    ENVIRONMENT_TABLE_NAME,
    GENERATION_TABLE_NAME,
)

if TYPE_CHECKING:
    from ....server.models.generations import GenerationTable
    from .environments import EnvironmentTable


class DeploymentBase(SQLModel):
    """Base Deployment Model."""

    environment_uuid: UUID = Field(
        foreign_key=f"{ENVIRONMENT_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    generation_uuid: UUID = Field(
        foreign_key=f"{GENERATION_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    is_active: bool = Field(default=True, index=True)
    revision: int = Field(default=1)
    notes: str | None = Field(default=None)


class DeploymentTable(DeploymentBase, BaseOrganizationSQLModel, table=True):
    """Deployment table tracking which generations are active in which environments."""

    __tablename__ = DEPLOYMENT_TABLE_NAME  # type: ignore
    environment: "EnvironmentTable" = Relationship(back_populates="deployments")
    generation: "GenerationTable" = Relationship(back_populates="deployments")
