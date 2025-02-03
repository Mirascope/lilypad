"""Spans schemas."""

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import model_validator

from ..models.spans import Scope, SpanTable, _SpanBase
from . import GenerationPublic, PromptPublic
from .response_models import ResponseModelPublic


class SpanCreate(_SpanBase):
    """Span create model"""

    ...


class SpanPublic(_SpanBase):
    """Span public model"""

    uuid: UUID
    display_name: str | None = None
    generation: GenerationPublic | None = None
    prompt: PromptPublic | None = None
    response_model: ResponseModelPublic | None = None
    child_spans: list["SpanPublic"]
    created_at: datetime
    version: int | None = None

    @model_validator(mode="before")
    @classmethod
    def convert_from_span_table(cls: type["SpanPublic"], data: Any) -> Any:
        """Convert SpanTable to SpanPublic."""
        if isinstance(data, SpanTable):
            span_public = cls._convert_span_table_to_public(data)
            return cls(**span_public)
        return data

    @classmethod
    def _convert_span_table_to_public(
        cls,
        span: "SpanTable",
    ) -> dict[str, Any]:
        """Set the display name based on the scope."""
        # TODO: Handle error cases where spans dont have attributes
        if span.scope == Scope.LILYPAD:
            attributes: dict[str, Any] = span.data.get("attributes", {})
            span_type: str = attributes.get("lilypad.type", "unknown")
            display_name = attributes.get(f"lilypad.{span_type}.name", None)
            version = attributes.get(f"lilypad.{span_type}.version")
        else:  # Must be Scope.LLM because Scope is an Enum
            data = span.data
            display_name = f"{data['attributes']['gen_ai.system']} with '{data['attributes']['gen_ai.request.model']}'"
            version = None
        child_spans = [
            cls._convert_span_table_to_public(child_span)
            for child_span in span.child_spans
        ]
        return {
            "display_name": display_name,
            "child_spans": child_spans,
            "version": version,
            **span.model_dump(exclude={"child_spans", "data"}),
        }
