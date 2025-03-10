"""Users models."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base_sql_model import BaseSQLModel, get_json_column
from .table_names import USER_TABLE_NAME
from .user_organizations import UserOrganization

if TYPE_CHECKING:
    from .api_keys import APIKeyTable
    from .organization_invites import OrganizationInviteTable
    from .user_organizations import UserOrganizationTable


class UserBase(SQLModel):
    """Base User Model."""

    first_name: str = Field(nullable=False, min_length=1)
    last_name: str | None = Field(default=None)
    email: str = Field(nullable=False, index=True, min_length=1)
    active_organization_uuid: UUID | None = Field(default=None)
    keys: dict[str, str] = Field(sa_column=get_json_column(), default_factory=dict)


class User(UserBase):
    """User public model"""

    uuid: UUID
    access_token: str | None = None
    user_organizations: list[UserOrganization] | None = None


class UserTable(UserBase, BaseSQLModel, table=True):
    """User table."""

    __tablename__ = USER_TABLE_NAME  # type: ignore

    user_organizations: list["UserOrganizationTable"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    api_keys: list["APIKeyTable"] = Relationship(
        back_populates="user", cascade_delete=True
    )
    organization_invites: list["OrganizationInviteTable"] = Relationship(
        back_populates="user", cascade_delete=True
    )
