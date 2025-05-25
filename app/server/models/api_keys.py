"""API key models."""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Annotated
from uuid import UUID

from pydantic.types import AwareDatetime
from sqlmodel import DateTime, Field, Relationship, SQLModel

from .base_organization_sql_model import BaseOrganizationSQLModel
from .table_names import (
    API_KEY_TABLE_NAME,
    ENVIRONMENT_TABLE_NAME,
    PROJECT_TABLE_NAME,
    USER_TABLE_NAME,
)

if TYPE_CHECKING:
    from ...ee.server.models.user_organizations import OrganizationTable
    from .environments import EnvironmentTable
    from .projects import ProjectTable
    from .users import UserTable


class APIKeyBase(SQLModel):
    """Base APIKey Model."""

    name: str = Field(nullable=False, min_length=1)
    expires_at: Annotated[datetime, AwareDatetime] = Field(
        sa_type=DateTime(timezone=True),  # pyright: ignore [reportArgumentType]
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=365),
        nullable=False,
        schema_extra={"format": "date-time"},
    )
    project_uuid: UUID = Field(
        index=True, foreign_key=f"{PROJECT_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    environment_uuid: UUID | None = Field(
        default=None,
        foreign_key=f"{ENVIRONMENT_TABLE_NAME}.uuid",
        ondelete="CASCADE",
        index=True,
    )


class APIKeyTable(APIKeyBase, BaseOrganizationSQLModel, table=True):
    """APIKey table."""

    __tablename__ = API_KEY_TABLE_NAME  # type: ignore
    key_hash: str = Field(nullable=False)
    user_uuid: UUID = Field(
        index=True, foreign_key=f"{USER_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    organization: "OrganizationTable" = Relationship(back_populates="api_keys")
    project: "ProjectTable" = Relationship(back_populates="api_keys")
    user: "UserTable" = Relationship(back_populates="api_keys")
    environment: "EnvironmentTable" = Relationship(back_populates="api_keys")
