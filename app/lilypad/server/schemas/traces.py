"""Traces schemas."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel

from .spans import SpanPublic


class TracesQueueResponse(BaseModel):
    """Response model for queued traces."""

    trace_status: Literal["queued", "processed"]
    span_count: int
    message: str
    trace_ids: list[str]


class RecentSpansResponse(BaseModel):
    """Response model for recent spans polling endpoint."""

    spans: list[SpanPublic]
    timestamp: datetime
    project_uuid: str
