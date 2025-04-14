"""Tags models."""

from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

from .base_organization_sql_model import BaseOrganizationSQLModel
from .function_tag_link import FunctionTagLink
from .span_tag_link import SpanTagLink
from .table_names import PROJECT_TABLE_NAME, TAG_TABLE_NAME

if TYPE_CHECKING:
    from .functions import FunctionTable
    from .organizations import OrganizationTable
    from .projects import ProjectTable
    from .spans import SpanTable


class _TagBase(SQLModel):
    """Base Tag Model."""

    project_uuid: UUID | None = Field(
        default=None,
        index=True,
        foreign_key=f"{PROJECT_TABLE_NAME}.uuid",
        ondelete="CASCADE",
    )
    name: str = Field(nullable=False, min_length=1)


class TagTable(_TagBase, BaseOrganizationSQLModel, table=True):
    """Tag Table Model."""

    __tablename__ = TAG_TABLE_NAME  # type: ignore

    __table_args__ = (
        UniqueConstraint(
            "organization_uuid", "project_uuid", "name", name="unique_tag_name"
        ),
    )
    project: "ProjectTable" = Relationship(back_populates="tags")
    organization: "OrganizationTable" = Relationship(back_populates="tags")
    spans: list["SpanTable"] = Relationship(
        back_populates="tags", link_model=SpanTagLink
    )
    functions: list["FunctionTable"] = Relationship(
        back_populates="tags", link_model=FunctionTagLink
    )
