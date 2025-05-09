"""The `/traces` API router."""

import logging
from collections import defaultdict
from collections.abc import Sequence
from typing import Annotated, Literal, cast
from uuid import UUID

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Query,
    Request,
    status,
)
from mirascope.core import Provider
from mirascope.core.base.types import CostMetadata
from mirascope.core.costs import calculate_cost
from opentelemetry.semconv._incubating.attributes import gen_ai_attributes

from ee.validate import LicenseInfo

from ....ee.server.features import cloud_features
from ....ee.server.require_license import get_organization_license, is_lilypad_cloud
from ..._utils import (
    validate_api_key_project_strict,
)
from ...models.spans import Scope, SpanTable
from ...schemas.pagination import Paginated
from ...schemas.span_more_details import calculate_openrouter_cost
from ...schemas.spans import SpanCreate, SpanPublic
from ...services import OpenSearchService, SpanService, get_opensearch_service
from ...services.billing import BillingService
from ...services.projects import ProjectService

traces_router = APIRouter()
logger = logging.getLogger(__name__)


def _convert_system_to_provider(system: str) -> Provider:
    if system == "az.ai.inference":
        return "azure"
    elif system == "google_genai":
        return "google"
    return cast(Provider, system)


@traces_router.get(
    "/projects/{project_uuid}/traces", response_model=Paginated[SpanPublic]
)
async def get_traces_by_project_uuid(
    project_uuid: UUID,
    span_service: Annotated[SpanService, Depends(SpanService)],
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order: Literal["asc", "desc"] = Query(
        "desc", pattern="^(asc|desc)$", examples=["asc", "desc"]
    ),
) -> Paginated[SpanPublic]:
    """Get traces by project UUID."""
    items = span_service.find_all_no_parent_spans(
        project_uuid, limit=limit, offset=offset, order=order
    )
    total = span_service.count_no_parent_spans(project_uuid)
    return Paginated(
        items=[SpanPublic.model_validate(item) for item in items],
        limit=limit,
        offset=offset,
        total=total,
    )


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
                cost = calculate_cost(
                    _convert_system_to_provider(system), model, metadata=cost_metadata
                )
            if cost is not None:
                span_cost = cost

    # Process attributes and create span
    attributes = trace.get("attributes", {})
    function_uuid_str = attributes.get("lilypad.function.uuid")

    span_create = SpanCreate(
        span_id=trace["span_id"],
        type=attributes.get("lilypad.type"),
        function_uuid=UUID(function_uuid_str) if function_uuid_str else None,
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


async def index_traces_in_opensearch(
    project_uuid: UUID,
    traces: list[dict],
    opensearch_service: OpenSearchService,
) -> None:
    """Index traces in OpenSearch."""
    try:
        success = opensearch_service.bulk_index_traces(project_uuid, traces)
        if not success:
            logger.error(
                f"Failed to index {len(traces)} traces for project {project_uuid}"
            )
        else:
            logger.info(
                f"Successfully indexed {len(traces)} traces for project {project_uuid}"
            )
    except Exception as e:
        logger.error(f"Exception during trace indexing: {str(e)}")


@traces_router.post(
    "/projects/{project_uuid}/traces", response_model=Sequence[SpanPublic]
)
async def traces(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_strict)],
    license: Annotated[LicenseInfo, Depends(get_organization_license)],
    is_lilypad_cloud: Annotated[bool, Depends(is_lilypad_cloud)],
    project_uuid: UUID,
    request: Request,
    span_service: Annotated[SpanService, Depends(SpanService)],
    opensearch_service: Annotated[OpenSearchService, Depends(get_opensearch_service)],
    background_tasks: BackgroundTasks,
    project_service: Annotated[ProjectService, Depends(ProjectService)],
    billing_service: Annotated[BillingService, Depends(BillingService)],
) -> Sequence[SpanTable]:
    """Create span traces."""
    if is_lilypad_cloud:
        tier = license.tier
        num_traces = span_service.count_by_current_month()
        if num_traces >= cloud_features[tier].traces_per_month:
            logger.warning(
                f"Trace limit exceeded for project {project_uuid}. "
                f"Tier: {tier.name.capitalize()}, "
                f"Current traces: {num_traces}, "
                f"Limit: {cloud_features[tier].traces_per_month}."
            )
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail=f"Exceeded the maximum number of traces per month for {tier.name.capitalize()} plan",
            )

    # Process the traces
    traces_json: list[dict] = await request.json()
    span_creates: list[SpanCreate] = []
    parent_to_children = defaultdict(list)

    # Build the parent-child relationships
    for trace in traces_json:
        if parent_span_id := trace.get("parent_span_id"):
            parent_to_children[parent_span_id].append(trace)
    # Find root spans (spans with no parents) and process each tree
    root_spans = [span for span in traces_json if span.get("parent_span_id") is None]

    for root_span in root_spans:
        await _process_span(root_span, parent_to_children, span_creates)
    project = project_service.find_record_no_organization(project_uuid)
    span_tables = span_service.create_bulk_records(
        span_creates,
        billing_service if is_lilypad_cloud else None,
        project_uuid,
        project.organization_uuid,
    )
    if opensearch_service.is_enabled:
        trace_dicts = [span.model_dump() for span in span_tables]
        background_tasks.add_task(
            index_traces_in_opensearch, project_uuid, trace_dicts, opensearch_service
        )
    return [span for span in span_tables if span.parent_span_id is None]


__all__ = ["traces_router"]
