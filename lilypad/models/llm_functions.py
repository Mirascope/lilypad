"""LLM functions models"""

from lilypad.server.models import LLMFunctionBase, ProviderCallParamsTable


class LLMFunctionBasePublic(LLMFunctionBase):
    """LLM function base public model"""

    id: int
    provider_call_params: list[ProviderCallParamsTable] | None
