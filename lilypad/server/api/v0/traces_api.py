"""The `/traces` API router."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from ..._utils import (
    calculate_cost,
    calculate_openrouter_cost,
    validate_api_key_project_strict,
)
from ...models import Scope, SpanTable
from ...schemas import SpanCreate, SpanPublic
from ...services import SpanService

traces_router = APIRouter()


@traces_router.get(
    "/projects/{project_uuid}/traces", response_model=Sequence[SpanPublic]
)
async def get_traces_by_project_uuid(
    project_uuid: UUID,
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> Sequence[SpanTable]:
    """Get all traces.

    Child spans are not lazy loaded to avoid N+1 queries.
    """
    return span_service.find_all_no_parent_spans(project_uuid)


@traces_router.post(
    "/projects/{project_uuid}/traces", response_model=Sequence[SpanPublic]
)
async def traces(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_strict)],
    project_uuid: UUID,
    request: Request,
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> Sequence[SpanTable]:
    """Create span traces."""
    traces_json: list[dict] = await request.json()
    span_tables: list[SpanTable] = []
    latest_parent_span_id = None
    cost = None
    for lilypad_trace in reversed(traces_json):
        if lilypad_trace["instrumentation_scope"]["name"] == "lilypad":
            scope = Scope.LILYPAD
            latest_parent_span_id = lilypad_trace["span_id"]
        else:
            scope = Scope.LLM
            attributes: dict = lilypad_trace.get("attributes", {})
            if (system := attributes.get(gen_ai_attributes.GEN_AI_SYSTEM)) and (
                model := attributes.get(gen_ai_attributes.GEN_AI_RESPONSE_MODEL)
            ):
                input_tokens = attributes.get(
                    gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS
                )
                output_tokens = attributes.get(
                    gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS
                )
                if system == "openrouter":
                    cost = await calculate_openrouter_cost(
                        input_tokens, output_tokens, model
                    )

                else:
                    cost = calculate_cost(
                        input_tokens,
                        output_tokens,
                        system,
                        model,
                    )
        # Handle streaming traces
        if scope == Scope.LLM and not lilypad_trace.get("parent_span_id"):
            parent_span_id = latest_parent_span_id

        else:
            parent_span_id = lilypad_trace.get("parent_span_id", None)
        attributes = lilypad_trace.get("attributes", {})
        span_create = SpanCreate(
            span_id=lilypad_trace["span_id"],
            project_uuid=project_uuid,
            type=attributes.get("lilypad.type", None),
            generation_uuid=UUID(generation_uuid_str)
            if (generation_uuid_str := attributes.get("lilypad.generation.uuid", None))
            else None,
            prompt_uuid=UUID(prompt_uuid_str)
            if (prompt_uuid_str := attributes.get("lilypad.prompt.uuid", None))
            else None,
            scope=scope,
            data=lilypad_trace,
            parent_span_id=parent_span_id,
            cost=cost,
        )
        span_tables.append(span_service.create_record(span_create))
    return span_tables


__all__ = ["traces_router"]
