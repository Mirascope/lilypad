"""Version models"""

from lilypad.models import FnParamsPublic, LLMFunctionPublic, SpanPublic
from lilypad.server.models.versions import VersionBase


class VersionPublic(VersionBase):
    """Version public model"""

    id: int
    fn_params: FnParamsPublic | None = None
    llm_fn: LLMFunctionPublic
    spans: list[SpanPublic]


class VersionCreate(VersionBase):
    """Version create model"""

    ...
