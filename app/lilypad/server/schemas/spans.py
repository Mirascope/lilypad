"""Spans schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, model_validator

from ...ee.server.schemas.annotations import AnnotationPublic
from ...server.schemas.span_more_details import SpanMoreDetails
from ..models.spans import Scope, SpanBase, SpanTable
from ..schemas.tags import TagPublic
from .functions import FunctionPublic


class SpanCreate(SpanBase):
    """Span create model"""

    project_uuid: UUID | None = None


class SpanUpdate(BaseModel):
    """Span update model"""

    tags_by_uuid: list[UUID] | None = None
    tags_by_name: list[str] | None = None

    @model_validator(mode="before")
    @classmethod
    def check_exclusive_tags(cls, data: Any) -> Any:
        """Ensure that only one of 'tags_by_uuid' or 'tags_by_name' is provided."""
        if (
            isinstance(data, dict)
            and data.get("tags_by_uuid") is not None
            and data.get("tags_by_name") is not None
        ):
            raise ValueError(
                "Provide either 'tags_by_uuid' or 'tags_by_name', not both."
            )
        return data


class SpanPublic(SpanBase):
    """Span public model"""

    uuid: UUID
    project_uuid: UUID
    display_name: str | None = None
    function: FunctionPublic | None
    annotations: list[AnnotationPublic]
    child_spans: list[SpanPublic]
    created_at: datetime
    status: str | None = None
    tags: list[TagPublic]
    score: float | None = None

    @model_validator(mode="before")
    @classmethod
    def convert_from_span_table(cls: type[SpanPublic], data: Any) -> Any:
        """Convert SpanTable to SpanPublic."""
        if isinstance(data, SpanTable):
            span_public = cls._convert_span_table_to_public(data)
            return cls(**span_public)
        return data

    @classmethod
    def _convert_span_table_to_public(
        cls,
        span: SpanTable,
    ) -> dict[str, Any]:
        """Set the display name based on the scope."""
        data = span.data
        attributes = data.get("attributes", {})
        if span.scope == Scope.LILYPAD:
            attributes: dict[str, Any] = span.data.get("attributes", {})
            display_name = span.data.get("name", "")
        else:  # Must be Scope.LLM because Scope is an Enum
            if gen_ai_system := attributes.get("gen_ai.system"):
                display_name = f"{gen_ai_system} with '{data['attributes']['gen_ai.request.model']}'"
            else:
                display_name = data.get("name", "")
        child_spans = [
            cls._convert_span_table_to_public(child_span)
            for child_span in span.child_spans
        ]
        annotations = [
            AnnotationPublic.model_validate(
                annotation, update={"span": SpanMoreDetails.from_span(annotation.span)}
            )
            for annotation in span.annotations
        ]
        return {
            "display_name": display_name,
            "child_spans": child_spans,
            "function": span.function,
            "annotations": annotations,
            "status": span.data.get("status"),
            "tags": span.tags,
            **span.model_dump(exclude={"child_spans", "data"}),
        }


class SpanStatusPublic(BaseModel):
    """Response model for span status endpoint"""

    resolved: int
    pending: int
    orphaned: int
    total: int
