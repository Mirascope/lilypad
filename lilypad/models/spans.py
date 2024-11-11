"""Span models"""

from typing import Any

from pydantic import model_validator

from lilypad.server.models import LLMFunctionTable, SpanBase
from lilypad.server.models.spans import Scope, SpanTable


class SpanPublic(SpanBase):
    """Call public model with prompt version."""

    display_name: str | None = None
    llm_function: LLMFunctionTable | None = None
    child_spans: list["SpanPublic"]

    @model_validator(mode="before")
    @classmethod
    def convert_from_span_table(cls: type["SpanPublic"], data: Any) -> Any:
        """Convert SpanTable to SpanPublic."""
        if isinstance(data, SpanTable):
            span_public = convert_span_table_to_public(data)
            return cls(**span_public)
        return data


class SpanCreate(SpanBase):
    """Span create model"""

    ...


def convert_span_table_to_public(
    span: SpanTable,
) -> dict:
    """Set the display name based on the scope."""
    # TODO: Handle error cases where spans dont have attributes
    if span.scope == Scope.LILYPAD:
        display_name = span.data["attributes"]["lilypad.function_name"]
    elif span.scope == Scope.LLM:
        data = span.data
        display_name = f"{data['attributes']['gen_ai.system']} with '{data['attributes']['gen_ai.request.model']}'"
    else:
        display_name = "Unknown"
    child_spans = [
        convert_span_table_to_public(child_span) for child_span in span.child_spans
    ]
    return {
        "display_name": display_name,
        "child_spans": child_spans,
        **span.model_dump(exclude={"child_spans"}),
    }
