"""API key models."""

from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base_organization_sql_model import BaseOrganizationSQLModel
from .table_names import API_KEY_TABLE_NAME, PROJECT_TABLE_NAME, USER_TABLE_NAME

if TYPE_CHECKING:
    from .projects import ProjectTable
    from .user_organizations import OrganizationTable
    from .users import UserTable


class _APIKeyBase(SQLModel):
    """Base APIKey Model."""

    name: str = Field(nullable=False, min_length=1)
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(days=365),
        nullable=False,
    )
    project_uuid: UUID = Field(
        index=True, foreign_key=f"{PROJECT_TABLE_NAME}.uuid", ondelete="CASCADE"
    )


class APIKeyTable(_APIKeyBase, BaseOrganizationSQLModel, table=True):
    """APIKey table."""

    __tablename__ = API_KEY_TABLE_NAME  # type: ignore
    key_hash: str = Field(nullable=False)
    user_uuid: UUID = Field(
        index=True, foreign_key=f"{USER_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    organization: "OrganizationTable" = Relationship(back_populates="api_keys")
    project: "ProjectTable" = Relationship(back_populates="api_keys")
    user: "UserTable" = Relationship(back_populates="api_keys")
