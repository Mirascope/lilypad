"""EE Annotations schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from ....server.schemas.span_more_details import SpanMoreDetails
from ..models.annotations import AnnotationBase


class AnnotationPublic(AnnotationBase):
    """Annotation public model."""

    uuid: UUID
    project_uuid: UUID
    span_uuid: UUID
    function_uuid: UUID
    created_at: datetime
    span: SpanMoreDetails


class AnnotationCreate(BaseModel):
    """Annotation create model."""

    span_uuid: UUID | None = None
    project_uuid: UUID | None = None
    function_uuid: UUID | None = None
    assigned_to: list[UUID] | None = None


class AnnotationUpdate(AnnotationBase):
    """Annotation update model."""

    ...
