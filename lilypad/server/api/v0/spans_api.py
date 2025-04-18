"""The `/spans` API router."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from ..._utils import get_current_user
from ...models import SpanTable
from ...models.spans import Scope
from ...schemas.span_more_details import SpanMoreDetails
from ...schemas.spans import SpanPublic, SpanUpdate
from ...schemas.users import UserPublic
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


@spans_router.get("/projects/{project_uuid}/spans", response_model=Sequence[SpanPublic])
async def search_traces(
    project_uuid: UUID,
    opensearch_service: Annotated[OpenSearchService, Depends(get_opensearch_service)],
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
) -> Sequence[SpanTable]:
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
    traces = []
    for hit in hits:
        source = hit["_source"]
        trace = SpanTable(
            uuid=hit["_id"],
            organization_uuid=source["organization_uuid"],
            project_uuid=project_uuid,
            span_id=source["span_id"],
            parent_span_id=source["parent_span_id"],
            type=source["type"],
            function_uuid=UUID(source["function_uuid"])
            if source["function_uuid"]
            else None,
            scope=Scope(source["scope"]) if source["scope"] else Scope.LILYPAD,
            cost=source["cost"],
            input_tokens=source["input_tokens"],
            output_tokens=source["output_tokens"],
            duration_ms=source["duration_ms"],
            created_at=source["created_at"],
            data=source["data"],
        )
        traces.append(trace)

    return traces


__all__ = ["spans_router"]
