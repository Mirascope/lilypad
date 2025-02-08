"""EE Annotations schemas."""

from __future__ import annotations

from uuid import UUID

from ....server.schemas.spans import SpanMoreDetails
from ..models import AnnotationBase


class AnnotationPublic(AnnotationBase):
    """Annotation public model."""

    uuid: UUID
    project_uuid: UUID
    span_uuid: UUID
    generation_uuid: UUID
    span: SpanMoreDetails


class AnnotationCreate(AnnotationBase):
    """Annotation create model."""

    span_uuid: UUID | None = None
    project_uuid: UUID | None = None
    generation_uuid: UUID | None = None


class AnnotationUpdate(AnnotationBase):
    """Annotation update model."""

    ...
