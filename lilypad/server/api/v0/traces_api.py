"""The `/traces` API router."""

from collections.abc import Sequence
from typing import Annotated

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, select

from ...db import get_session
from ...models import Scope, SpanCreate, SpanPublic, SpanTable
from ...services import SpanService

traces_router = APIRouter()


@traces_router.get("/projects/{project_id}/traces", response_model=Sequence[SpanPublic])
async def get_traces_by_project_id(
    project_id: int,
    session: Annotated[Session, Depends(get_session)],
) -> Sequence[SpanTable]:
    """Get all traces"""
    traces = session.exec(
        select(SpanTable).where(
            SpanTable.project_id == project_id,
            SpanTable.parent_span_id.is_(None),  # type: ignore
        )
    ).all()
    return traces


@traces_router.post("/traces", response_model=Sequence[SpanPublic])
async def traces(
    request: Request,
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> Sequence[SpanTable]:
    """Create span traces."""
    traces_json: list[dict] = await request.json()
    span_tables: list[SpanTable] = []
    latest_parent_span_id = None
    latest_project_id = None
    for lilypad_trace in traces_json:
        if lilypad_trace["instrumentation_scope"]["name"] == "lilypad":
            scope = Scope.LILYPAD
            latest_parent_span_id = lilypad_trace["span_id"]
            latest_project_id = lilypad_trace["attributes"]["lilypad.project_id"]
        else:
            scope = Scope.LLM

        # Handle streaming traces
        if scope == Scope.LLM and not lilypad_trace.get("parent_span_id"):
            parent_span_id = latest_parent_span_id
            project_id = latest_project_id
        else:
            parent_span_id = lilypad_trace.get("parent_span_id", None)
            project_id = lilypad_trace.get("attributes", {}).get(
                "lilypad.project_id", None
            )
        attributes = lilypad_trace.get("attributes", {})
        span_create = SpanCreate(
            id=lilypad_trace["span_id"],
            project_id=project_id,
            version_id=attributes.get("lilypad.version_id", None),
            version_num=version_num
            if (version_num := attributes.get("lilypad.version_num", None))
            and version_num >= 0
            else None,
            scope=scope,
            data=lilypad_trace,
            parent_span_id=parent_span_id,
        )
        span_tables.append(span_service.create_record(span_create))
    return span_tables


__all__ = ["traces_router"]
