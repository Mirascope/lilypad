"""Users organizations models."""

import enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Column, Enum, Field, Relationship, SQLModel

from .base_organization_sql_model import BaseOrganizationSQLModel
from .table_names import (
    USER_ORGANIZATION_TABLE_NAME,
    USER_TABLE_NAME,
)

if TYPE_CHECKING:
    from .organizations import OrganizationTable
    from .users import UserTable


class UserRole(str, enum.Enum):
    """User role enum."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class UserOrganizationBase(SQLModel):
    """Base UserOrganization Model."""

    role: UserRole = Field(sa_column=Column(Enum(UserRole), nullable=False))
    user_uuid: UUID = Field(
        index=True, foreign_key=f"{USER_TABLE_NAME}.uuid", ondelete="CASCADE"
    )


class UserOrganizationTable(UserOrganizationBase, BaseOrganizationSQLModel, table=True):
    """UserOrganization table."""

    __tablename__ = USER_ORGANIZATION_TABLE_NAME  # type: ignore

    organization: "OrganizationTable" = Relationship(
        back_populates="user_organizations"
    )
    user: "UserTable" = Relationship(back_populates="user_organizations")
