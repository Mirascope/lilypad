"""Version Models."""

from lilypad.models import FnParamsPublic, LLMFunctionBasePublic
from lilypad.server.models.versions import VersionBase


class VersionPublic(VersionBase):
    """Version public model"""

    id: int
    fn_params: FnParamsPublic | None = None
    llm_fn: LLMFunctionBasePublic
