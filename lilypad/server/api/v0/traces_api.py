"""The `/traces` API router."""

from collections import defaultdict
from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Request
from mirascope.core.base.types import CostMetadata
from mirascope.core.costs import calculate_cost
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from ..._utils import (
    calculate_openrouter_cost,
    validate_api_key_project_strict,
)
from ...models.spans import Scope, SpanTable
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


async def _process_span(
    trace: dict,
    parent_to_children: dict[str, list[dict]],
    span_creates: list[SpanCreate],
) -> SpanCreate:
    """Process a span and its children."""
    # Process all children first (bottom-up approach)
    total_child_cost = 0
    total_input_tokens = 0
    total_output_tokens = 0
    for child in parent_to_children[trace["span_id"]]:
        span = await _process_span(child, parent_to_children, span_creates)
        if span.cost is not None:
            total_child_cost += span.cost
        if span.input_tokens is not None:
            total_input_tokens += span.input_tokens
        if span.output_tokens is not None:
            total_output_tokens += span.output_tokens

    if trace["instrumentation_scope"]["name"] == "lilypad":
        scope = Scope.LILYPAD
        span_cost = total_child_cost
        input_tokens = total_input_tokens
        output_tokens = total_output_tokens
    else:
        scope = Scope.LLM
        attributes = trace.get("attributes", {})
        span_cost = 0
        input_tokens = attributes.get(gen_ai_attributes.GEN_AI_USAGE_INPUT_TOKENS)
        output_tokens = attributes.get(gen_ai_attributes.GEN_AI_USAGE_OUTPUT_TOKENS)

        if (system := attributes.get(gen_ai_attributes.GEN_AI_SYSTEM)) and (
            model := attributes.get(gen_ai_attributes.GEN_AI_RESPONSE_MODEL)
        ):
            if system == "openrouter":
                cost = await calculate_openrouter_cost(
                    input_tokens, output_tokens, model
                )
            else:
                # TODO: Add cached_tokens once it is added to OpenTelemetry GenAI spec
                # https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/
                cost_metadata = CostMetadata(
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                cost = calculate_cost(system, model, metadata=cost_metadata)
            if cost is not None:
                span_cost = cost

    # Process attributes and create span
    attributes = trace.get("attributes", {})
    generation_uuid_str = attributes.get("lilypad.generation.uuid")

    span_create = SpanCreate(
        span_id=trace["span_id"],
        type=attributes.get("lilypad.type"),
        generation_uuid=UUID(generation_uuid_str) if generation_uuid_str else None,
        scope=scope,
        data=trace,
        parent_span_id=trace.get("parent_span_id"),
        cost=span_cost,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        duration_ms=trace["end_time"] - trace["start_time"],
    )
    span_creates.insert(0, span_create)
    return span_create


@traces_router.post("/projects/{project_uuid}/traces", response_model=SpanPublic)
async def traces(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_strict)],
    project_uuid: UUID,
    request: Request,
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> SpanTable:
    """Create span traces."""
    traces_json: list[dict] = await request.json()
    span_creates: list[SpanCreate] = []
    parent_to_children = defaultdict(list)

    # Build the parent-child relationships
    for trace in traces_json:
        if parent_span_id := trace.get("parent_span_id"):
            parent_to_children[parent_span_id].append(trace)

    # Find root spans (spans with no parents) and process each tree
    root_spans = [span for span in traces_json if span.get("parent_span_id") is None]

    # Process each root span and its subtree, this will always be 1 for now
    for root_span in root_spans:
        await _process_span(root_span, parent_to_children, span_creates)

    span_tables = span_service.create_bulk_records(span_creates, project_uuid)

    return span_tables[0]


__all__ = ["traces_router"]
