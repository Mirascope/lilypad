"""Provider call params models"""

from typing import Any

from pydantic import BaseModel

from lilypad.server.models import FnParamsBase, Provider


class CallArgsPublic(BaseModel):
    """Call args model."""

    id: int | None
    model: str
    provider: Provider
    prompt_template: str
    editor_state: str
    call_params: dict[str, Any] | None


class FnParamsPublic(FnParamsBase):
    """Fn params public model"""

    id: int
