"""The `/spans` API router."""

import json
from collections.abc import Sequence
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes
from pydantic import BaseModel
from sqlmodel import Session, select

from ..._utils import (
    MessageParam,
    convert_anthropic_messages,
    convert_gemini_messages,
    convert_openai_messages,
)
from ...db import get_session
from ...models import Provider, Scope, SpanPublic, SpanTable
from ...services import SpanService

spans_router = APIRouter()


class SpanMoreDetails(BaseModel):
    """Span more details model."""

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

    @classmethod
    def from_span(cls, span: SpanTable) -> "SpanMoreDetails":
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
            signature, code = None, None
            if span.generation:
                signature = span.generation.signature
                code = span.generation.code
            arg_values = json.loads(
                attributes.get("lilypad.generation.arg_values", "{}")
            )
            output = attributes.get("lilypad.generation.output", "")
            display_name = attributes.get("lilypad.generation.name", "unknown")
            messages = attributes.get("lilypad.messages", [])

        return SpanMoreDetails(
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
            data=data,
            cost=span.cost,
        )


@spans_router.get("/spans/{span_uuid}", response_model=SpanMoreDetails)
async def get_span(
    span_uuid: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> SpanMoreDetails:
    """Get span by uuid."""
    span = session.exec(select(SpanTable).where(SpanTable.uuid == span_uuid)).first()
    if not span:
        raise HTTPException(status_code=404, detail="Span not found")
    return SpanMoreDetails.from_span(span)


@spans_router.get(
    "/projects/{project_uuid}/generations/{generation_uuid}/spans",
    response_model=Sequence[SpanPublic],
)
async def get_span_by_generation_uuid(
    project_uuid: UUID,
    generation_uuid: UUID,
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> Sequence[SpanTable]:
    """Get span by uuid."""
    return span_service.find_records_by_generation_uuid(project_uuid, generation_uuid)


@spans_router.get(
    "/projects/{project_uuid}/spans/{span_uuid}", response_model=SpanPublic
)
async def get_span_by_uuid(
    span_uuid: UUID,
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> SpanTable:
    """Get span by uuid."""
    return span_service.find_record_by_uuid(span_uuid)


__all__ = ["spans_router"]
