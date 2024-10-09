"""LLM functions models"""

from lilypad.server.models import FnParamsTable, LLMFunctionBase


class LLMFunctionBasePublic(LLMFunctionBase):
    """LLM function base public model"""

    id: int
    fn_params: list[FnParamsTable] | None
