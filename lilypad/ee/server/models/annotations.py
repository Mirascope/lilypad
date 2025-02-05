"""EE Annotation models."""

from enum import Enum
from typing import TYPE_CHECKING
from uuid import UUID

from sqlmodel import Field, Relationship, SQLModel

from ....server.models import BaseOrganizationSQLModel
from ....server.models.table_names import (
    ANNOTATION_TABLE_NAME,
    GENERATION_TABLE_NAME,
    PROJECT_TABLE_NAME,
    SPAN_TABLE_NAME,
    USER_TABLE_NAME,
)

if TYPE_CHECKING:
    from ....server.models.generations import GenerationTable
    from ....server.models.projects import ProjectTable
    from ....server.models.spans import SpanTable


class Label(str, Enum):
    """Label enum"""

    PASS = "pass"
    FAIL = "fail"


class EvaluationType(str, Enum):
    """Evaluation type enum"""

    MANUAL = "manual"
    VERIFIED = "verified"
    EDITED = "edited"


class AnnotationBase(SQLModel):
    """Base Annotation Model."""

    label: Label | None = Field(default=None, index=True)
    reasoning: str | None = Field(default=None)
    type: EvaluationType | None = Field(default=EvaluationType.MANUAL)
    assigned_to: UUID | None = Field(
        default=None, foreign_key=f"{USER_TABLE_NAME}.uuid", ondelete="CASCADE"
    )


class AnnotationTable(AnnotationBase, BaseOrganizationSQLModel, table=True):
    """Annotation table."""

    __tablename__ = ANNOTATION_TABLE_NAME  # type: ignore
    project_uuid: UUID | None = Field(
        default=None, foreign_key=f"{PROJECT_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    span_uuid: UUID | None = Field(
        default=None, foreign_key=f"{SPAN_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    generation_uuid: UUID | None = Field(
        default=None, foreign_key=f"{GENERATION_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
    project: "ProjectTable" = Relationship(back_populates="annotations")
    span: "SpanTable" = Relationship(back_populates="annotations")
    generation: "GenerationTable" = Relationship(back_populates="annotations")
