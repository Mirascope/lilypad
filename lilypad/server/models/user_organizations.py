"""Users organizations table and models."""

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from .base_organization_sql_model import BaseOrganizationSQLModel
from .organizations import OrganizationPublic
from .table_names import (
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


class _UserOrganizationBase(SQLModel):
    """Base UserOrganization Model."""

    role: UserRole = Field(nullable=False)
    user_uuid: UUID = Field(index=True, foreign_key=f"{USER_TABLE_NAME}.uuid")


class UserOrganizationTable(
    _UserOrganizationBase, BaseOrganizationSQLModel, table=True
):
    """UserOrganization table."""

    __tablename__ = USER_ORGANIZATION_TABLE_NAME  # type: ignore

    organization: "OrganizationTable" = Relationship(
        back_populates="user_organizations"
    )
    user: "UserTable" = Relationship(back_populates="user_organizations")


class UserOrganizationPublic(_UserOrganizationBase):
    """UserOrganization public model"""

    uuid: UUID
    organization_uuid: UUID
    organization: OrganizationPublic


class UserOrganizationCreate(BaseModel):
    """UserOrganization create model"""

    role: UserRole
