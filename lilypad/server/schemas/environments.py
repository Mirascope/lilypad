"""Environment schemas."""

from datetime import datetime
from uuid import UUID

from ..models.environments import EnvironmentBase


class EnvironmentPublic(EnvironmentBase):
    """Environment public model."""

    uuid: UUID
    organization_uuid: UUID
    created_at: datetime


class EnvironmentCreate(EnvironmentBase):
    """Environment create model."""

    ...
