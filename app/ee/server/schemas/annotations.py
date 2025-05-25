"""EE Annotations schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, model_validator

from ....server.schemas.span_more_details import SpanMoreDetails
from ..models.annotations import AnnotationBase, EvaluationType, Label


class AnnotationPublic(AnnotationBase):
    """Annotation public model."""

    uuid: UUID
    project_uuid: UUID
    span_uuid: UUID
    function_uuid: UUID | None = None
    created_at: datetime
    span: SpanMoreDetails


class AnnotationCreate(BaseModel):
    """Annotation create model."""

    span_uuid: UUID | None = None
    project_uuid: UUID | None = None
    function_uuid: UUID | None = None
    label: Label | None = None
    reasoning: str | None = None
    type: EvaluationType | None = None
    data: dict[str, Any] | None = None
    assigned_to: list[UUID] | None = None
    assignee_email: list[str] | None = None

    @model_validator(mode="before")
    @classmethod
    def check_exclusive_assignment(cls, data: Any) -> Any:
        """Check that either assigned_to or assignee_email is provided, but not both."""
        if isinstance(data, dict):
            assigned_to_present = (
                data.get("assigned_to") is not None and data["assigned_to"]
            )
            assignee_email_present = data.get("assignee_email") is not None
            if assigned_to_present and assignee_email_present:
                raise ValueError(
                    "Provide either 'assigned_to' (list of UUIDs) or 'assignee_email' (list of email) , not both."
                )
        return data


class AnnotationUpdate(AnnotationBase):
    """Annotation update model."""

    ...
