"""The `/spans` API router."""

from collections.abc import Sequence
from datetime import datetime, timedelta, timezone
from typing import Annotated, Any, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from ..._utils import get_current_user
from ...models import SpanTable
from ...models.spans import Scope
from ...schemas.pagination import Paginated
from ...schemas.span_more_details import SpanMoreDetails
from ...schemas.spans import SpanPublic, SpanUpdate
from ...schemas.traces import RecentSpansResponse
from ...schemas.users import UserPublic
from ...services.functions import FunctionService
from ...services.opensearch import (
    OpenSearchService,
    SearchQuery,
    get_opensearch_service,
)
from ...services.spans import AggregateMetrics, SpanService, TimeFrame

spans_router = APIRouter()


@spans_router.get(
    "/projects/{project_uuid}/spans/metadata",
    response_model=Sequence[AggregateMetrics],
)
async def get_aggregates_by_project_uuid(
    project_uuid: UUID,
    time_frame: Annotated[TimeFrame, Query()],
    span_service: Annotated[SpanService, Depends(SpanService)],
    environment_uuid: Annotated[UUID, Query()],
) -> Sequence[AggregateMetrics]:
    """Get aggregated span by project uuid."""
    return span_service.get_aggregated_metrics(
        project_uuid, time_frame=time_frame, environment_uuid=environment_uuid
    )


@spans_router.get(
    "/projects/{project_uuid}/spans/recent",
    response_model=RecentSpansResponse,
)
async def get_recent_spans(
    project_uuid: UUID,
    span_service: Annotated[SpanService, Depends(SpanService)],
    environment_uuid: Annotated[UUID, Query()],
    since: Annotated[
        datetime | None, Query(description="Get spans created since this timestamp")
    ] = None,
) -> RecentSpansResponse:
    """Get spans created recently for real-time polling.

    If no 'since' parameter is provided, returns spans from the last 30 seconds.
    """
    if not since:
        since = datetime.now(timezone.utc) - timedelta(seconds=30)

    # Get recent spans
    recent_spans = span_service.get_spans_since(project_uuid, since, environment_uuid)

    return RecentSpansResponse(
        spans=[SpanPublic.model_validate(span) for span in recent_spans],
        timestamp=datetime.now(timezone.utc),
        project_uuid=str(project_uuid),
    )


@spans_router.get(
    "/projects/{project_uuid}/spans/{span_identifier}", response_model=SpanMoreDetails
)
async def get_span(
    project_uuid: UUID,
    span_identifier: str,
    span_service: Annotated[SpanService, Depends(SpanService)],
    environment_uuid: Annotated[UUID, Query()],
) -> SpanMoreDetails:
    """Get span by uuid or span_id."""
    # Try to parse as UUID first
    try:
        span_uuid = UUID(span_identifier)
        span = span_service.find_record_by_uuid(
            span_uuid, project_uuid=project_uuid, environment_uuid=environment_uuid
        )
    except ValueError:
        # If not a UUID, treat as span_id
        span = span_service.get_record_by_span_id(
            project_uuid, span_identifier, environment_uuid
        )

    if not span:
        raise HTTPException(status_code=404, detail="Span not found")
    return SpanMoreDetails.from_span(span)


@spans_router.patch("/spans/{span_uuid}", response_model=SpanMoreDetails)
async def update_span(
    span_uuid: UUID,
    span_update: SpanUpdate,
    span_service: Annotated[SpanService, Depends(SpanService)],
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> SpanMoreDetails:
    """Update span by uuid."""
    updated_span = await span_service.update_span(
        span_uuid=span_uuid,
        update_data=span_update,
        user_uuid=current_user.uuid,
    )
    return SpanMoreDetails.from_span(updated_span)


@spans_router.get(
    "/projects/{project_uuid}/functions/{function_uuid}/spans/metadata",
    response_model=Sequence[AggregateMetrics],
)
async def get_aggregates_by_function_uuid(
    project_uuid: UUID,
    function_uuid: UUID,
    time_frame: TimeFrame,
    span_service: Annotated[SpanService, Depends(SpanService)],
    environment_uuid: Annotated[UUID, Query()],
) -> Sequence[AggregateMetrics]:
    """Get aggregated span by function uuid."""
    return span_service.get_aggregated_metrics(
        project_uuid, function_uuid, time_frame, environment_uuid
    )


@spans_router.get("/projects/{project_uuid}/spans", response_model=Sequence[SpanPublic])
async def search_traces(
    project_uuid: UUID,
    opensearch_service: Annotated[OpenSearchService, Depends(get_opensearch_service)],
    function_service: Annotated[FunctionService, Depends(FunctionService)],
    search_query: Annotated[SearchQuery, Query()],
) -> Sequence[SpanPublic]:
    """Search for traces in OpenSearch."""
    if not opensearch_service.is_enabled:
        return []
    hits = opensearch_service.search_traces(
        project_uuid, search_query.environment_uuid, search_query
    )
    # Extract function UUIDs and fetch functions in batch
    function_uuids = {
        UUID(hit["_source"]["function_uuid"])
        for hit in hits
        if hit["_source"].get("function_uuid")
    }

    functions = function_service.find_records_by_uuids(uuids=function_uuids)
    # Filter by project_uuid since BaseOrganizationService doesn't filter by additional params
    functions = [f for f in functions if f.project_uuid == project_uuid]
    functions_by_id = {str(func.uuid): func for func in functions if func.uuid}

    # Build spans from search results
    spans_by_id: dict[str, SpanPublic] = {}
    for hit in hits:
        source: dict[str, Any] = hit["_source"]
        function_uuid_str = source.get("function_uuid")
        if "organization_uuid" not in source or "span_id" not in source:
            continue  # Skip if either key is missing
        span = SpanTable(
            uuid=hit["_id"],
            organization_uuid=source["organization_uuid"],
            project_uuid=project_uuid,
            span_id=source["span_id"],
            trace_id=source.get("trace_id"),
            parent_span_id=source.get("parent_span_id"),
            type=source["type"],
            function_uuid=UUID(function_uuid_str) if function_uuid_str else None,
            function=functions_by_id.get(function_uuid_str)
            if function_uuid_str
            else None,
            scope=Scope(source["scope"]) if source["scope"] else Scope.LILYPAD,
            cost=source["cost"],
            input_tokens=source.get("input_tokens"),
            output_tokens=source.get("output_tokens"),
            duration_ms=source.get("duration_ms"),
            created_at=source.get("created_at", datetime.now(timezone.utc)),
            data=source.get("data", {}),
            child_spans=[],
        )

        span_public = SpanPublic.model_validate(span)
        span_public.score = hit.get("_score")
        spans_by_id[source["span_id"]] = span_public

    # Establish parent-child relationships
    for span in spans_by_id.values():
        if span.parent_span_id and span.parent_span_id in spans_by_id:
            spans_by_id[span.parent_span_id].child_spans.append(span)

    # Return only root spans
    return [
        span
        for span in spans_by_id.values()
        if not span.parent_span_id or span.parent_span_id not in spans_by_id
    ]


async def delete_span_in_opensearch(
    project_uuid: UUID,
    span_uuid: UUID,
    environment_uuid: UUID,
    opensearch_service: OpenSearchService,
) -> None:
    """Delete span in OpenSearch."""
    if opensearch_service.is_enabled:
        opensearch_service.delete_trace_by_uuid(
            project_uuid, environment_uuid, span_uuid
        )


@spans_router.delete("/projects/{project_uuid}/spans/{span_uuid}")
async def delete_spans(
    project_uuid: UUID,
    span_uuid: UUID,
    span_service: Annotated[SpanService, Depends(SpanService)],
    opensearch_service: Annotated[OpenSearchService, Depends(get_opensearch_service)],
    background_tasks: BackgroundTasks,
    environment_uuid: Annotated[UUID, Query()],
) -> bool:
    """Delete spans by UUID."""
    try:
        span_service.delete_record_by_uuid(span_uuid)
        if opensearch_service.is_enabled:
            background_tasks.add_task(
                delete_span_in_opensearch,
                project_uuid,
                span_uuid,
                environment_uuid,
                opensearch_service,
            )
    except Exception:
        return False
    return True


@spans_router.get(
    "/projects/{project_uuid}/functions/{function_uuid}/spans/paginated",
    response_model=Paginated[SpanPublic],
)
async def get_spans_by_function_uuid_paginated(
    project_uuid: UUID,
    function_uuid: UUID,
    span_service: Annotated[SpanService, Depends(SpanService)],
    environment_uuid: Annotated[UUID, Query()],
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    order: Literal["asc", "desc"] = Query(
        "desc", pattern="^(asc|desc)$", examples=["asc", "desc"]
    ),
) -> Paginated[SpanPublic]:
    """Get spans for a function with pagination (new, non-breaking)."""
    items = span_service.find_records_by_function_uuid_paged(
        project_uuid,
        function_uuid,
        environment_uuid=environment_uuid,
        limit=limit,
        offset=offset,
        order=order,
    )
    total = span_service.count_records_by_function_uuid(
        project_uuid, function_uuid, environment_uuid
    )
    return Paginated(
        items=[SpanPublic.model_validate(i) for i in items],
        limit=limit,
        offset=offset,
        total=total,
    )


__all__ = ["spans_router"]
