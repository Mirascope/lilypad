"""The `/spans` API router."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from ..._utils import get_current_user
from ...models import SpanTable
from ...schemas import SpanMoreDetails, SpanPublic, SpanUpdate, UserPublic
from ...services import TagService
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


@spans_router.patch(
    "/projects/{project_uuid}/spans/{span_uuid}", response_model=SpanPublic
)
async def update_span_tags(
    span_uuid: UUID,
    tags: list[str],
    span_service: Annotated[SpanService, Depends(SpanService)],
    tag_service: Annotated[TagService, Depends(TagService)],
    current_user: Annotated[UserPublic, Depends(get_current_user)],
) -> SpanTable:
    """Update span tags by uuid."""
    return await span_service.update_span_tags(
        span_uuid=span_uuid,
        tag_names=tags,
        user_uuid=current_user.uuid,
        tag_service=tag_service,
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
