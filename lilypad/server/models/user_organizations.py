"""Users organizations table and models."""

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from .base_sql_model import BaseSQLModel
from .organizations import OrganizationPublic
from .table_names import (
    ORGANIZATION_TABLE_NAME,
    USER_ORGANIZATION_TABLE_NAME,
    USER_TABLE_NAME,
)

if TYPE_CHECKING:
    from .organizations import OrganizationTable
    from .users import UserTable


class UserRole(str, Enum):
    """User role enum."""

    ADMIN = "admin"
    MEMBER = "member"


class _UserOrganization(BaseSQLModel):
    """Base UserOrganization Model."""

    role: UserRole = Field(nullable=False)
    user_id: int = Field(index=True, foreign_key=f"{USER_TABLE_NAME}.id")
    organization_uuid: UUID = Field(
        index=True, foreign_key=f"{ORGANIZATION_TABLE_NAME}.uuid"
    )


class UserOrganizationTable(_UserOrganization, table=True):
    """UserOrganization table."""

    __tablename__ = USER_ORGANIZATION_TABLE_NAME  # type: ignore

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    organization: "OrganizationTable" = Relationship(
        back_populates="user_organizations"
    )
    user: "UserTable" = Relationship(back_populates="user_organizations")


class UserOrganizationPublic(_UserOrganization):
    """UserOrganization public model"""

    id: int
    organization: OrganizationPublic


class UserOrganizationCreate(_UserOrganization):
    """UserOrganization create model"""

    ...
