"""Deployment SQLModel."""

from datetime import datetime, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import text
from sqlmodel import DateTime, Field, Index, Relationship, SQLModel

from lilypad.server.models import BaseOrganizationSQLModel
from lilypad.server.models.table_names import (
    DEPLOYMENT_TABLE_NAME,
    ENVIRONMENT_TABLE_NAME,
    FUNCTION_TABLE_NAME,
    PROJECT_TABLE_NAME,
)

if TYPE_CHECKING:
    from .environments import EnvironmentTable
    from .functions import FunctionTable
    from .projects import ProjectTable


class DeploymentBase(SQLModel):
    """Base Deployment Model."""

    environment_uuid: UUID = Field(
        foreign_key=f"{ENVIRONMENT_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    function_uuid: UUID = Field(
        foreign_key=f"{FUNCTION_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    project_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROJECT_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    is_active: bool = Field(default=True, index=True)
    version_num: int = Field(default=1)
    notes: str | None = Field(default=None)
    activated_at: datetime = Field(
        sa_type=DateTime(timezone=True),  # pyright: ignore [reportArgumentType]
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True,
        description="Timestamp when the deployment was activated.",
        schema_extra={"format": "date-time"},
    )


class DeploymentTable(DeploymentBase, BaseOrganizationSQLModel, table=True):
    """Deployment table tracking which functions are active in which environments."""

    __tablename__ = DEPLOYMENT_TABLE_NAME  # type: ignore
    __table_args__ = (
        Index(
            "ux_environment_active_deployment",
            "environment_uuid",
            unique=True,
            postgresql_where=text(
                "is_active = true"
            ),  # Use text() for partial index condition
        ),
    )
    environment: "EnvironmentTable" = Relationship(back_populates="deployments")
    function: "FunctionTable" = Relationship(back_populates="deployments")
    project: "ProjectTable" = Relationship(back_populates="deployments")
