"""The `/spans` API router."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query

from ..._utils import get_current_user
from ...models import SpanTable
from ...schemas.pagination import Paginated
from ...schemas.span_more_details import SpanMoreDetails
from ...schemas.spans import SpanPublic, SpanUpdate
from ...schemas.users import UserPublic
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
) -> Paginated[SpanPublic]:
    """Get spans for a function with pagination (new, non-breaking)."""
    items = span_service.find_records_by_function_uuid_paged(
        project_uuid, function_uuid, limit=limit, offset=offset
    )
    total = span_service.count_records_by_function_uuid(project_uuid, function_uuid)
    return Paginated(
        items=[SpanPublic.model_validate(i) for i in items],
        limit=limit,
        offset=offset,
        total=total,
    )

__all__ = ["spans_router"]
