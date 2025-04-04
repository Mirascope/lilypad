"""The `/spans` API router."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from ...models import SpanTable
from ...schemas import SpanMoreDetails, SpanPublic, SpanUpdate
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
) -> SpanTable:
    """Update span by uuid."""
    return span_service.update_record_by_uuid(
        span_uuid, span_update.model_dump(exclude_unset=True)
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


__all__ = ["spans_router"]
