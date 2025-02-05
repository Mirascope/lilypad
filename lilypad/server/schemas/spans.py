"""Spans schemas."""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any
from uuid import UUID

from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from pydantic import BaseModel, model_validator

from ...ee.server.models.annotations import AnnotationTable
from .._utils import (
    MessageParam,
    convert_anthropic_messages,
    convert_gemini_messages,
    convert_mirascope_messages,
    convert_openai_messages,
)
from ..models.prompts import Provider
from ..models.spans import Scope, SpanBase, SpanTable
from .generations import GenerationPublic
from .prompts import PromptPublic
from .response_models import ResponseModelPublic


class SpanCreate(SpanBase):
    """Span create model"""

    project_uuid: UUID | None = None


class SpanPublic(SpanBase):
    """Span public model"""

    uuid: UUID
    project_uuid: UUID
    display_name: str | None = None
    generation: GenerationPublic | None = None
    prompt: PromptPublic | None = None
    response_model: ResponseModelPublic | None = None
    annotations: list[AnnotationTable]
    child_spans: list[SpanPublic]
    created_at: datetime
    version: int | None = None

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
            "annotations": span.annotations,
            **span.model_dump(exclude={"child_spans", "data"}),
        }


class SpanMoreDetails(BaseModel):
    """Span more details model."""

    project_uuid: UUID | None = None
    display_name: str
    provider: str
    model: str
    input_tokens: float | None = None
    output_tokens: float | None = None
    duration_ms: float
    signature: str | None = None
    code: str | None = None
    arg_values: dict[str, Any] | None = None
    output: str | None = None
    messages: list[MessageParam]
    data: dict[str, Any]
    cost: float | None = None
    template: str | None = None

    @classmethod
    def from_span(cls, span: SpanTable) -> SpanMoreDetails:
        """Create a SpanMoreDetails object from a SpanTable object."""
        data = span.data
        messages = []
        attributes: dict = data["attributes"]
        if span.scope == Scope.LLM:
            display_name = data["name"]
            signature = None
            code = None
            arg_values = None
            output = None
            template = None
            provider = attributes.get(gen_ai_attributes.GEN_AI_SYSTEM, "unknown")
            if provider == Provider.GEMINI.value:
                messages = convert_gemini_messages(data["events"])
            elif (
                provider == Provider.OPENROUTER.value
                or provider == Provider.OPENAI.value
            ):
                messages = convert_openai_messages(data["events"])
            elif provider == Provider.ANTHROPIC.value:
                messages = convert_anthropic_messages(data["events"])
        else:
            lilypad_type = attributes.get("lilypad.type")
            if not lilypad_type:
                raise ValueError("Span type is unknown. Please set `lilypad.type`.")
            signature = attributes.get(f"lilypad.{lilypad_type}.signature", "")
            code = attributes.get(f"lilypad.{lilypad_type}.code", "")
            arg_values = json.loads(
                attributes.get(f"lilypad.{lilypad_type}.arg_values", "{}")
            )
            output = attributes.get(f"lilypad.{lilypad_type}.output", "")
            display_name = attributes.get(f"lilypad.{lilypad_type}.name", "unknown")
            messages = convert_mirascope_messages(
                attributes.get(f"lilypad.{lilypad_type}.messages", [])
            )
            template = attributes.get(f"lilypad.{lilypad_type}.template", "")
        return SpanMoreDetails(
            project_uuid=span.project_uuid,
            display_name=display_name,
            model=attributes.get(gen_ai_attributes.GEN_AI_REQUEST_MODEL, "unknown"),
            provider=attributes.get(gen_ai_attributes.GEN_AI_SYSTEM, "unknown"),
            input_tokens=attributes.get(gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS),
            output_tokens=attributes.get(gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS),
            duration_ms=data["end_time"] - data["start_time"],
            signature=signature,
            code=code,
            arg_values=arg_values,
            output=output,
            messages=messages,
            template=template,
            data=data,
            cost=span.cost,
        )
