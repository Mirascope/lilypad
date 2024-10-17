"""LLM functions models"""

from lilypad.server.models import FnParamsTable, LLMFunctionBase


class LLMFunctionCreate(LLMFunctionBase):
    """LLM function create model."""

    ...


class LLMFunctionPublic(LLMFunctionBase):
    """LLM function base public model"""

    id: int
    fn_params: list[FnParamsTable] | None
