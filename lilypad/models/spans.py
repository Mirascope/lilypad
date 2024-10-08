"""Span models"""

from lilypad.server.models import LLMFunctionTable, SpanBase


class SpanPublic(SpanBase):
    """Call public model with prompt version."""

    id: str
    display_name: str | None = None
    llm_function: LLMFunctionTable | None = None
    child_spans: list["SpanPublic"]
