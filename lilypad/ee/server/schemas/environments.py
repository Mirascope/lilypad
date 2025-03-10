"""Environment schemas."""

from uuid import UUID

from ..models.environments import EnvironmentBase


class EnvironmentPublic(EnvironmentBase):
    """Environment public model."""

    uuid: UUID
    organization_uuid: UUID


class EnvironmentCreate(EnvironmentBase):
    """Environment create model."""

    ...
