"""Annotations table and models."""

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from .base_organization_sql_model import BaseOrganizationSQLModel
from .table_names import (
    ANNOTATION_TABLE_NAME,
    GENERATION_TABLE_NAME,
    PROJECT_TABLE_NAME,
    SPAN_TABLE_NAME,
    USER_TABLE_NAME,
)

if TYPE_CHECKING:
    from .generations import GenerationTable
    from .projects import ProjectTable
    from .spans import SpanTable


class Label(str, Enum):
    """Label enum"""

    PASS = "pass"
    FAIL = "fail"


class EvaluationType(str, Enum):
    """Evaluation type enum"""

    MANUAL = "manual"
    VERIFIED = "verified"
    EDITED = "edited"


class _AnnotationBase(SQLModel):
    """Base Annotation Model."""

    input: dict[str, str] | None = Field(default=None)
    output: str
    project_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROJECT_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    label: Label | None = Field(default=None)
    reasoning: str | None = Field(default=None)
    type: EvaluationType | None = Field(default=None)
    assigned_to: UUID | None = Field(
        default=None, foreign_key=f"{USER_TABLE_NAME}.uuid", ondelete="CASCADE"
    )


class AnnotationPublic(_AnnotationBase):
    """Annotation public model."""

    uuid: UUID
    generation_uuid: UUID
    span_uuid: UUID


class AnnotationCreate(_AnnotationBase):
    """Annotation create model."""


# TODO: No TABLE?
class AnnotationTable(_AnnotationBase, BaseOrganizationSQLModel):
    """Annotation table."""

    __tablename__ = ANNOTATION_TABLE_NAME  # type: ignore
    generation_uuid: UUID | None = Field(
        default=None, foreign_key=f"{GENERATION_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    span_uuid: UUID | None = Field(
        default=None, foreign_key=f"{SPAN_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    project: "ProjectTable" = Relationship(back_populates="annotations")
    span: "SpanTable" = Relationship(back_populates="annotation", cascade_delete=True)
    generation: "GenerationTable" = Relationship(
        back_populates="annotation", cascade_delete=True
    )
