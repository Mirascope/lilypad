"""Users table and models."""

from typing import TYPE_CHECKING
from uuid import UUID

from pydantic import BaseModel
from sqlmodel import Field, Relationship, SQLModel

from .base_sql_model import BaseSQLModel, get_json_column
from .table_names import USER_TABLE_NAME
from .user_organizations import UserOrganizationPublic

if TYPE_CHECKING:
    from .user_organizations import UserOrganizationTable


class _UserBase(SQLModel):
    """Base Function Model."""

    first_name: str = Field(nullable=False, min_length=1)
    last_name: str | None = Field(default=None)
    email: str = Field(nullable=False, index=True, min_length=1)
    active_organization_uuid: UUID | None = Field(default=None)
    keys: dict[str, str] = Field(sa_column=get_json_column(), default_factory=dict)


class UserTable(_UserBase, BaseSQLModel, table=True):
    """Function table."""

    __tablename__ = USER_TABLE_NAME  # type: ignore

    user_organizations: list["UserOrganizationTable"] = Relationship(
        back_populates="user", cascade_delete=True
    )


class UserPublic(_UserBase):
    """User public model"""

    uuid: UUID
    access_token: str | None = None
    user_organizations: list[UserOrganizationPublic] | None = None


class UserCreate(BaseModel):
    """User create model"""

    first_name: str
    last_name: str | None = None
    email: str
    active_organization_uuid: UUID | None = None
