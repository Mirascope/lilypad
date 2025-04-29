"""The `/spans` API router."""

from collections.abc import Sequence
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query

from ..._utils import get_current_user
from ...models import SpanTable
from ...models.spans import Scope
from ...schemas.pagination import Paginated
from ...schemas.span_more_details import SpanMoreDetails
from ...schemas.spans import SpanPublic, SpanUpdate
from ...schemas.users import UserPublic
from ...services.functions import FunctionService
from ...services.opensearch import (
    OpenSearchService,
    SearchQuery,
    get_opensearch_service,
)
from ...services.spans import AggregateMetrics, SpanService, TimeFrame

spans_router = APIRouter()


@spans_router.get("/spans/{span_uuid}", response_model=SpanMoreDetails)
async def get_span(
    span_uuid: UUID,
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> SpanMoreDetails:
    """Get span by uuid."""
    span = span_service.find_record_by_uuid(span_uuid)
    if not span:
        raise HTTPException(status_code=404, detail="Span not found")
    return SpanMoreDetails.from_span(span)


@spans_router.get(
    "/projects/{project_uuid}/spans/metadata",
    response_model=Sequence[AggregateMetrics],
)
async def get_aggregates_by_project_uuid(
    project_uuid: UUID,
    time_frame: TimeFrame,
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> Sequence[AggregateMetrics]:
    """Get aggregated span by project uuid."""
    return span_service.get_aggregated_metrics(project_uuid, time_frame=time_frame)


# Order matters, this endpoint should be last
@spans_router.get(
    "/projects/{project_uuid}/spans/{span_id}", response_model=SpanMoreDetails
)
async def get_span_by_span_id(
    project_uuid: UUID,
    span_id: str,
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> SpanMoreDetails:
    """Get span by project_uuid and span_id."""
    span = span_service.get_record_by_span_id(project_uuid, span_id)
    if not span:
        raise HTTPException(status_code=404, detail="Span not found")
    return SpanMoreDetails.from_span(span)


@spans_router.patch("/spans/{span_uuid}", response_model=SpanPublic)
async def update_span(
    span_uuid: UUID,
    span_update: SpanUpdate,
    span_service: Annotated[SpanService, Depends(SpanService)],
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> SpanTable:
    """Update span by uuid."""
    return await span_service.update_span(
        span_uuid=span_uuid,
        update_data=span_update,
        user_uuid=current_user.uuid,
    )


@spans_router.get(
    "/projects/{project_uuid}/functions/{function_uuid}/spans",
    response_model=Sequence[SpanPublic],
)
async def get_span_by_function_uuid(
    project_uuid: UUID,
    function_uuid: UUID,
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> Sequence[SpanTable]:
    """Get span by uuid."""
    return span_service.find_records_by_function_uuid(project_uuid, function_uuid)


@spans_router.get(
    "/projects/{project_uuid}/functions/{function_uuid}/spans/metadata",
    response_model=Sequence[AggregateMetrics],
)
async def get_aggregates_by_function_uuid(
    project_uuid: UUID,
    function_uuid: UUID,
    time_frame: TimeFrame,
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> Sequence[AggregateMetrics]:
    """Get aggregated span by function uuid."""
    return span_service.get_aggregated_metrics(project_uuid, function_uuid, time_frame)


@spans_router.get("/projects/{project_uuid}/spans", response_model=Sequence[SpanPublic])
async def search_traces(
    project_uuid: UUID,
    opensearch_service: Annotated[OpenSearchService, Depends(get_opensearch_service)],
    function_service: Annotated[FunctionService, Depends(FunctionService)],
    query_string: Annotated[str, Query(description="Search query string")],
    time_range_start: Annotated[
        int | None, Query(description="Start time range in milliseconds")
    ] = None,
    time_range_end: Annotated[
        int | None, Query(description="End time range in milliseconds")
    ] = None,
    limit: Annotated[
        int, Query(description="Maximum number of results to return")
    ] = 100,
    scope: Annotated[Scope | None, Query(description="Scope of the search")] = None,
    type: Annotated[
        str | None, Query(description="Type of spans to search for")
    ] = None,
) -> Sequence[SpanPublic]:
    """Search for traces in OpenSearch."""
    if not opensearch_service.is_enabled:
        return []

    search_query = SearchQuery(
        query_string=query_string,
        time_range_start=time_range_start,
        time_range_end=time_range_end,
        limit=limit,
        scope=scope,
        type=type,
    )
    hits = opensearch_service.search_traces(project_uuid, search_query)
    # Extract function UUIDs and fetch functions in batch
    function_uuids = {
        UUID(hit["_source"]["function_uuid"])
        for hit in hits
        if hit["_source"].get("function_uuid")
    }

    functions = function_service.find_records_by_uuids(
        project_uuid=project_uuid, uuids=function_uuids
    )
    functions_by_id = {str(func.uuid): func for func in functions if func.uuid}

    # Build spans from search results
    spans_by_id: dict[str, SpanPublic] = {}
    for hit in hits:
        source = hit["_source"]
        function_uuid_str = source.get("function_uuid")

        span = SpanTable(
            uuid=hit["_id"],
            organization_uuid=source["organization_uuid"],
            project_uuid=project_uuid,
            span_id=source["span_id"],
            parent_span_id=source["parent_span_id"],
            type=source["type"],
            function_uuid=UUID(function_uuid_str) if function_uuid_str else None,
            function=functions_by_id.get(function_uuid_str),
            scope=Scope(source["scope"]) if source["scope"] else Scope.LILYPAD,
            cost=source["cost"],
            input_tokens=source["input_tokens"],
            output_tokens=source["output_tokens"],
            duration_ms=source["duration_ms"],
            created_at=source["created_at"],
            data=source["data"],
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
    opensearch_service: OpenSearchService,
) -> None:
    """Delete span in OpenSearch."""
    if opensearch_service.is_enabled:
        opensearch_service.delete_trace_by_uuid(project_uuid, span_uuid)


@spans_router.delete("/projects/{project_uuid}/spans/{span_uuid}")
async def delete_spans(
    project_uuid: UUID,
    span_uuid: UUID,
    span_service: Annotated[SpanService, Depends(SpanService)],
    opensearch_service: Annotated[OpenSearchService, Depends(get_opensearch_service)],
    background_tasks: BackgroundTasks,
) -> bool:
    """Delete spans by UUID."""
    try:
        span_service.delete_record_by_uuid(span_uuid)
        if opensearch_service.is_enabled:
            background_tasks.add_task(
                delete_span_in_opensearch, project_uuid, span_uuid, opensearch_service
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
        limit=limit,
        offset=offset,
        order=order,
    )
    total = span_service.count_records_by_function_uuid(project_uuid, function_uuid)
    return Paginated(
        items=[SpanPublic.model_validate(i) for i in items],
        limit=limit,
        offset=offset,
        total=total,
    )


__all__ = ["spans_router"]
