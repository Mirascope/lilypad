"""Users table and models."""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship

from .base_sql_model import BaseSQLModel
from .table_names import ORGANIZATION_TABLE_NAME

if TYPE_CHECKING:
    from .projects import ProjectTable
    from .user_organizations import UserOrganizationTable


class _Organization(BaseSQLModel):
    """Base Organization Model."""

    name: str = Field(nullable=False, min_length=1)


class OrganizationTable(_Organization, table=True):
    """Organization table."""

    __tablename__ = ORGANIZATION_TABLE_NAME  # type: ignore

    uuid: UUID | None = Field(
        nullable=False,
        default_factory=uuid4,
        primary_key=True,
    )
    user_organizations: list["UserOrganizationTable"] = Relationship(
        back_populates="organization", cascade_delete=True
    )
    projects: list["ProjectTable"] = Relationship(
        back_populates="organization", cascade_delete=True
    )


class OrganizationPublic(_Organization):
    """Organization public model"""

    uuid: UUID


class OrganizationCreate(_Organization):
    """Organization create model"""

    ...
