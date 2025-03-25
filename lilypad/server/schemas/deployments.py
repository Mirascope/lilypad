"""Deployment schemas."""

from uuid import UUID

from lilypad.server.schemas.functions import FunctionPublic

from ..models.deployments import DeploymentBase
from .environments import EnvironmentPublic


class DeploymentPublic(DeploymentBase):
    """Deployment public model."""

    uuid: UUID
    organization_uuid: UUID
    function: FunctionPublic | None = None
    environment: EnvironmentPublic | None = None


class DeploymentCreate(DeploymentBase):
    """Deployment create model."""

    ...
