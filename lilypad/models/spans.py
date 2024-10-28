"""Span models"""

from lilypad.server.models import LLMFunctionTable, SpanBase


class SpanPublic(SpanBase):
    """Call public model with prompt version."""

    display_name: str | None = None
    llm_function: LLMFunctionTable | None = None
    child_spans: list["SpanPublic"]


class SpanCreate(SpanBase):
    """Span create model"""

    ...
