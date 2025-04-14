from pydantic import BaseModel


class SpanAssignmentUpdate(BaseModel):
    """Request body schema for assigning an annotation via span."""
    assignee_email: str