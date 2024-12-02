"""Users table and models."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base_sql_model import BaseSQLModel
from .table_names import ORGANIZATION_TABLE_NAME

if TYPE_CHECKING:
    from .projects import ProjectTable
    from .user_organizations import UserOrganizationTable


class _OrganizationBase(SQLModel):
    """Base Organization Model."""

    name: str = Field(nullable=False, min_length=1)


class OrganizationTable(_OrganizationBase, BaseSQLModel, table=True):
    """Organization table."""

    __tablename__ = ORGANIZATION_TABLE_NAME  # type: ignore

    user_organizations: list["UserOrganizationTable"] = Relationship(
        back_populates="organization", cascade_delete=True
    )
    projects: list["ProjectTable"] = Relationship(
        back_populates="organization", cascade_delete=True
    )


class OrganizationPublic(_OrganizationBase):
    """Organization public model"""

    uuid: UUID


class OrganizationCreate(_OrganizationBase):
    """Organization create model"""

    ...
