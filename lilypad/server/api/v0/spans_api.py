"""The `/spans` API router."""

import json
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import Session, select

from ...._utils import (
    MessageParam,
    convert_anthropic_messages,
    convert_gemini_messages,
    group_span_keys,
)
from ...db import get_session
from ...models import Provider, Scope, SpanPublic, SpanTable

spans_router = APIRouter()


class SpanMoreDetails(BaseModel):
    """Span more details model."""

    display_name: str
    provider: str
    model: str
    prompt_tokens: float | None = None
    completion_tokens: float | None = None
    duration_ms: float
    code: str | None = None
    arg_values: dict[str, Any] | None = None
    output: str | None = None
    messages: list[MessageParam]
    data: dict[str, Any]

    @classmethod
    def from_span(cls, span: SpanTable) -> "SpanMoreDetails":
        """Create a SpanMoreDetails object from a SpanTable object."""
        data = span.data
        messages = []
        if span.scope == Scope.LLM:
            raw_messages = group_span_keys(data["attributes"])
            display_name = data["name"]
            code = None
            arg_values = None
            output = None
            provider = data["attributes"]["gen_ai.system"].lower()
            if provider == Provider.GEMINI:
                messages = convert_gemini_messages(raw_messages)
            elif provider == Provider.OPENROUTER or provider == Provider.OPENAI:
                # TODO: Handle OpenAI messages
                messages = []
            elif provider == Provider.ANTHROPIC:
                messages = convert_anthropic_messages(raw_messages)
        else:
            code = span.version.function.code
            arg_values = json.loads(data["attributes"]["lilypad.arg_values"])
            output = data["attributes"]["lilypad.output"]
            display_name = data["attributes"]["lilypad.function_name"]
            messages = data["attributes"]["lilypad.messages"]
        attributes: dict = data["attributes"]
        return SpanMoreDetails(
            display_name=display_name,
            model=attributes.get("gen_ai.request.model", "unknown"),
            provider=attributes.get("gen_ai.system", "unknown"),
            prompt_tokens=attributes.get("gen_ai.usage.prompt_tokens"),
            completion_tokens=attributes.get("gen_ai.usage.completion_tokens"),
            duration_ms=data["end_time"] - data["start_time"],
            code=code,
            arg_values=arg_values,
            output=output,
            messages=messages,
            data=data,
        )


@spans_router.get("/spans/{span_id}", response_model=SpanMoreDetails)
async def get_span(
    span_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> SpanMoreDetails:
    """Get span by id."""
    span = session.exec(select(SpanTable).where(SpanTable.id == span_id)).first()
    if not span:
        raise HTTPException(status_code=404, detail="Span not found")
    return SpanMoreDetails.from_span(span)


@spans_router.get("/projects/{project_id}/spans/{span_id}", response_model=SpanPublic)
async def get_span_by_project_id(
    span_id: str,
    session: Annotated[Session, Depends(get_session)],
) -> SpanTable:
    """Get span by id."""
    span = session.exec(select(SpanTable).where(SpanTable.id == span_id)).first()
    if not span:
        raise HTTPException(status_code=404, detail="Span not found")
    return span


__all__ = ["spans_router"]
