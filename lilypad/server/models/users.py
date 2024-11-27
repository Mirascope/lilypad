"""Users table and models."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship

from .base_sql_model import BaseSQLModel
from .table_names import USER_TABLE_NAME
from .user_organizations import UserOrganizationPublic

if TYPE_CHECKING:
    from .user_organizations import UserOrganizationTable


class _User(BaseSQLModel):
    """Base Function Model."""

    first_name: str = Field(nullable=False, min_length=1)
    last_name: str | None = Field(default=None)
    email: str = Field(nullable=False, index=True, min_length=1)
    active_organization_uuid: UUID | None = Field(default=None)


class UserTable(_User, table=True):
    """Function table."""

    __tablename__ = USER_TABLE_NAME  # type: ignore

    id: int | None = Field(default=None, primary_key=True, nullable=False)
    user_organizations: list["UserOrganizationTable"] = Relationship(
        back_populates="user", cascade_delete=True
    )


class UserPublic(_User):
    """User public model"""

    id: int
    access_token: str | None = None
    user_organizations: list[UserOrganizationPublic]


class UserCreate(_User):
    """User create model"""

    ...
