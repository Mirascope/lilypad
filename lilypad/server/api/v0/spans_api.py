"""The `/spans` API router."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from ...db import get_session
from ...models import SpanTable
from ...schemas import SpanMoreDetails, SpanPublic
from ...services import SpanService

spans_router = APIRouter()


@spans_router.get("/spans/{span_uuid}", response_model=SpanMoreDetails)
async def get_span(
    span_uuid: UUID,
    session: Annotated[Session, Depends(get_session)],
) -> SpanMoreDetails:
    """Get span by uuid."""
    span = session.exec(select(SpanTable).where(SpanTable.uuid == span_uuid)).first()
    if not span:
        raise HTTPException(status_code=404, detail="Span not found")
    return SpanMoreDetails.from_span(span)


@spans_router.get(
    "/projects/{project_uuid}/generations/{generation_uuid}/spans",
    response_model=Sequence[SpanPublic],
)
async def get_span_by_generation_uuid(
    project_uuid: UUID,
    generation_uuid: UUID,
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> Sequence[SpanTable]:
    """Get span by uuid."""
    return span_service.find_records_by_generation_uuid(project_uuid, generation_uuid)


__all__ = ["spans_router"]
