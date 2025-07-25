"""The `/traces` API router."""

import logging
from collections import defaultdict
from typing import Annotated, Literal
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

from ee.validate import LicenseInfo

from ....ee.server.features import cloud_features
from ....ee.server.require_license import get_organization_license, is_lilypad_cloud
from ..._utils import (
    get_current_user,
    validate_api_key_project_strict,
)
from ..._utils.opensearch import index_traces_in_opensearch
from ..._utils.span_processing import create_span_from_data
from ...models.api_keys import APIKeyTable
from ...models.spans import SpanTable
from ...schemas.pagination import Paginated
from ...schemas.spans import SpanCreate, SpanPublic
from ...schemas.traces import TracesQueueResponse
from ...schemas.users import UserPublic
from ...services import (
    OpenSearchService,
    SpanKafkaService,
    SpanService,
    StripeKafkaService,
    get_opensearch_service,
    get_span_kafka_service,
    get_stripe_kafka_service,
)
from ...services.billing import BillingService
from ...services.projects import ProjectService

traces_router = APIRouter()
logger = logging.getLogger(__name__)


@traces_router.get(
    "/projects/{project_uuid}/traces/{span_id}/root", response_model=SpanPublic
)
async def get_trace_by_span_uuid(
    project_uuid: UUID,
    span_id: str,
    span_service: Annotated[SpanService, Depends(SpanService)],
    environment_uuid: Annotated[UUID, Query()],
) -> SpanTable:
    """Get traces by project UUID."""
    span = span_service.find_root_parent_span(span_id)
    if not span:
        raise HTTPException(status_code=404, detail="Span not found")
    return span


@traces_router.get(
    "/projects/{project_uuid}/traces/by-trace-id/{trace_id}",
    response_model=list[SpanPublic],
)
async def get_spans_by_trace_id(
    project_uuid: UUID,
    trace_id: str,
    span_service: Annotated[SpanService, Depends(SpanService)],
    environment_uuid: Annotated[UUID, Query()],
) -> list[SpanPublic]:
    """Get all spans for a given trace ID."""
    spans = span_service.find_spans_by_trace_id(
        project_uuid, trace_id, environment_uuid
    )
    if not spans:
        raise HTTPException(
            status_code=404, detail=f"No spans found for trace_id: {trace_id}"
        )
    return [SpanPublic.model_validate(span) for span in spans]


@traces_router.get(
    "/projects/{project_uuid}/traces", response_model=Paginated[SpanPublic]
)
async def get_traces_by_project_uuid(
    project_uuid: UUID,
    span_service: Annotated[SpanService, Depends(SpanService)],
    environment_uuid: Annotated[UUID, Query()],
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order: Literal["asc", "desc"] = Query(
        "desc", pattern="^(asc|desc)$", examples=["asc", "desc"]
    ),
) -> Paginated[SpanPublic]:
    """Get traces by project UUID."""
    items = span_service.find_all_no_parent_spans(
        project_uuid,
        environment_uuid=environment_uuid,
        limit=limit,
        offset=offset,
        order=order,
    )
    total = span_service.count_no_parent_spans(project_uuid, environment_uuid)
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
    """Process a span and its children"""
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

    span_create = await create_span_from_data(
        trace,
        child_costs=total_child_cost,
        child_input_tokens=total_input_tokens,
        child_output_tokens=total_output_tokens,
    )
    span_creates.insert(0, span_create)
    return span_create


@traces_router.post(
    "/projects/{project_uuid}/traces", response_model=TracesQueueResponse
)
async def traces(
    api_key: Annotated[APIKeyTable, Depends(validate_api_key_project_strict)],
    license: Annotated[LicenseInfo, Depends(get_organization_license)],
    is_lilypad_cloud: Annotated[bool, Depends(is_lilypad_cloud)],
    project_uuid: UUID,
    request: Request,
    span_service: Annotated[SpanService, Depends(SpanService)],
    opensearch_service: Annotated[OpenSearchService, Depends(get_opensearch_service)],
    background_tasks: BackgroundTasks,
    project_service: Annotated[ProjectService, Depends(ProjectService)],
    billing_service: Annotated[BillingService, Depends(BillingService)],
    user: Annotated[UserPublic, Depends(get_current_user)],
    kafka_service: Annotated[SpanKafkaService, Depends(get_span_kafka_service)],
    stripe_kafka_service: Annotated[
        StripeKafkaService | None, Depends(get_stripe_kafka_service)
    ],
) -> TracesQueueResponse:
    """Create span traces using queue-based processing."""
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
    logger.info(
        f"[TRACES-API] 📨 Received {len(traces_json)} spans - Project: {project_uuid}, User: {user.uuid}"
    )
    logger.debug(f"[TRACES-API] Span data: {traces_json}")
    # Add project and environment UUID to each span's attributes for queue processing
    for trace in traces_json:
        if "attributes" not in trace:
            trace["attributes"] = {}
        trace["attributes"]["lilypad.project.uuid"] = str(project_uuid)
        trace["attributes"]["lilypad.environment.uuid"] = str(api_key.environment_uuid)

    # Extract unique trace IDs from spans
    trace_ids = list(
        {str(trace["trace_id"]) for trace in traces_json if trace.get("trace_id")}
    )

    # Try to send to Kafka queue
    logger.info(
        f"[TRACES-API] 🚀 Attempting to send {len(traces_json)} spans to Kafka queue - Project: {project_uuid}, User: {user.uuid}"
    )
    logger.info("[TRACES-API] Calling kafka_service.send_batch()")
    kafka_available = await kafka_service.send_batch(traces_json)
    logger.info(f"[TRACES-API] kafka_service.send_batch() returned: {kafka_available}")
    if kafka_available:
        # Queue processing successful
        logger.info(
            f"[TRACES-API] ✅ Successfully queued {len(traces_json)} spans to Kafka - Project: {project_uuid}, User: {user.uuid}, Environment: {api_key.environment_uuid}"
        )
        traces_queue_response = TracesQueueResponse(
            trace_status="queued",
            span_count=len(traces_json),
            message="Spans queued for processing",
            trace_ids=trace_ids,
        )
    else:
        # Fallback to synchronous processing if Kafka is not available
        logger.warning(
            f"[TRACES-API] ⚠️ Kafka not available, falling back to synchronous processing - Project: {project_uuid}, Spans: {len(traces_json)}"
        )

        span_creates: list[SpanCreate] = []
        parent_to_children = defaultdict(list)

        # Build the parent-child relationships
        for trace in traces_json:
            if parent_span_id := trace.get("parent_span_id"):
                parent_to_children[parent_span_id].append(trace)
        # Find root spans (spans with no parents) and process each tree
        root_spans = [
            span for span in traces_json if span.get("parent_span_id") is None
        ]

        for root_span in root_spans:
            await _process_span(root_span, parent_to_children, span_creates)
        project = project_service.find_record_no_organization(project_uuid)
        span_tables = span_service.create_bulk_records(
            span_creates,
            project_uuid,
            project.organization_uuid,
        )
        try:
            await billing_service.report_span_usage_with_fallback(
                project.organization_uuid, len(span_creates), stripe_kafka_service
            )
        except Exception as e:
            # if reporting fails, we don't want to fail the entire span creation
            logger.error("Error reporting span usage: %s", e)
        if opensearch_service.is_enabled and api_key.environment_uuid:
            trace_dicts = [span.model_dump() for span in span_tables]
            background_tasks.add_task(
                index_traces_in_opensearch,
                project_uuid,
                api_key.environment_uuid,
                trace_dicts,
                opensearch_service,
            )

        # Return consistent response format
        traces_queue_response = TracesQueueResponse(
            trace_status="processed",
            span_count=len(span_tables),
            message="Spans processed synchronously",
            trace_ids=trace_ids,
        )
    return traces_queue_response


__all__ = ["traces_router"]
