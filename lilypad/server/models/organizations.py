"""Users models."""

from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from .base_sql_model import BaseSQLModel
from .table_names import ORGANIZATION_TABLE_NAME

if TYPE_CHECKING:
    from .api_keys import APIKeyTable
    from .projects import ProjectTable
    from .user_organizations import UserOrganizationTable


class OrganizationBase(SQLModel):
    """Base Organization Model."""

    name: str = Field(nullable=False, min_length=1)


class OrganizationTable(OrganizationBase, BaseSQLModel, table=True):
    """Organization table."""

    __tablename__ = ORGANIZATION_TABLE_NAME  # type: ignore

    user_organizations: list["UserOrganizationTable"] = Relationship(
        back_populates="organization", cascade_delete=True
    )
    projects: list["ProjectTable"] = Relationship(
        back_populates="organization", cascade_delete=True
    )
    api_keys: list["APIKeyTable"] = Relationship(
        back_populates="organization", cascade_delete=True
    )
    license: str | None = Field(default=None, nullable=True)
