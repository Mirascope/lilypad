"""Deployment schemas."""

from uuid import UUID

from ..models.deployments import DeploymentBase
from .environments import EnvironmentPublic
from .generations import GenerationPublic


class DeploymentPublic(DeploymentBase):
    """Deployment public model."""

    uuid: UUID
    organization_uuid: UUID
    generation: GenerationPublic | None = None
    environment: EnvironmentPublic | None = None


class DeploymentCreate(DeploymentBase):
    """Deployment create model."""

    ...
