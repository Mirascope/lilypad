"""The `/spans` API router."""

from collections.abc import AsyncGenerator, Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from ....ee.server.generate import dummy_prompt
from ....ee.server.services import AnnotationService
from ...models import SpanTable
from ...schemas import SpanMoreDetails, SpanPublic
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


@spans_router.get(
    "/projects/{project_uuid}/generations/{generation_uuid}/spans/metadata",
    response_model=Sequence[AggregateMetrics],
)
async def get_aggregates_by_generation_uuid(
    project_uuid: UUID,
    generation_uuid: UUID,
    time_frame: TimeFrame,
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> Sequence[AggregateMetrics]:
    """Get aggregated span by generation uuid."""
    return span_service.get_aggregated_metrics(
        project_uuid, generation_uuid, time_frame
    )


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


@spans_router.get("/projects/{project_uuid}/spans/{span_uuid}/generate")
async def stream_generation(
    span_uuid: UUID,
    annotation_service: Annotated[AnnotationService, Depends(AnnotationService)],
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> StreamingResponse:
    """Stream generation."""
    data = {}
    annotation = annotation_service.find_record_by_span_uuid(span_uuid)
    if not annotation:
        span = span_service.find_record_by_uuid(span_uuid)
        if not span:
            raise HTTPException(status_code=404, detail="Span not found")
        else:
            attributes = span.data.get("attributes", {})
            lilypad_type = attributes.get("lilypad.type")
            output = attributes.get(f"lilypad.{lilypad_type}.output", None)
            if isinstance(output, str):
                data["output"] = {
                    "idealOutput": output,
                    "reasoning": "",
                    "exact": False,
                    "label": None,
                }
            else:
                for key, value in output.items():
                    data[key] = {
                        "idealOutput": value,
                        "reasoning": "",
                        "exact": False,
                        "label": None,
                    }
    else:
        if annotation.data:
            data = annotation.data

    async def stream() -> AsyncGenerator[str, None]:
        r"""Stream the generation. Must yield 'data: {your_data}\n\n'."""
        async for chunk in await dummy_prompt():
            yield f"data: {chunk.model_dump_json()}\n\n"

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


__all__ = ["spans_router"]
