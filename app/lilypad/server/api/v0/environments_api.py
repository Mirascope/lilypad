"""API endpoints for environments and deployments."""

from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from lilypad.server.models import FunctionTable
from lilypad.server.schemas.functions import FunctionPublic

from ....server.schemas.deployments import (
    DeploymentPublic,
)
from ....server.schemas.environments import (
    EnvironmentCreate,
    EnvironmentPublic,
)
from ....server.services import DeploymentService, EnvironmentService
from ...models.deployments import DeploymentTable
from ...models.environments import EnvironmentTable

environments_router = APIRouter()


# Environment endpoints
@environments_router.get("/environments", response_model=Sequence[EnvironmentPublic])
async def get_environments(
    environment_service: Annotated[EnvironmentService, Depends(EnvironmentService)],
) -> Sequence[EnvironmentTable]:
    """Get all environments for a project."""
    return environment_service.find_all_records()  # pragma: no cover


@environments_router.post("/environments", response_model=EnvironmentPublic)
async def create_environment(
    environment_create: EnvironmentCreate,
    environment_service: Annotated[EnvironmentService, Depends(EnvironmentService)],
) -> EnvironmentTable:
    """Create a new environment."""
    return environment_service.create_record(environment_create)  # pragma: no cover


@environments_router.get(
    "/environments/{environment_uuid}",
    response_model=EnvironmentPublic,
)
async def get_environment(
    environment_uuid: UUID,
    environment_service: Annotated[EnvironmentService, Depends(EnvironmentService)],
) -> EnvironmentTable:
    """Get environment by UUID."""
    return environment_service.find_record_by_uuid(environment_uuid)  # pragma: no cover


@environments_router.delete("/environments/{environment_uuid}")
async def delete_environment(
    environment_uuid: UUID,
    environment_service: Annotated[EnvironmentService, Depends(EnvironmentService)],
) -> bool:
    """Delete an environment."""
    return environment_service.delete_record_by_uuid(
        environment_uuid
    )  # pragma: no cover


# Deployment endpoints
@environments_router.post(
    "/projects/{project_uuid}/environments/{environment_uuid}/deploy",
    response_model=DeploymentPublic,
)
async def deploy_function(
    project_uuid: UUID,
    environment_uuid: UUID,
    function_uuid: UUID,
    deployment_service: Annotated[DeploymentService, Depends(DeploymentService)],
    notes: str | None = None,
) -> DeploymentTable:
    """Deploy a function to an environment."""
    return deployment_service.deploy_function(
        environment_uuid, function_uuid, notes
    )  # pragma: no cover


@environments_router.get(
    "/projects/{project_uuid}/environments/{environment_uuid}/deployment",
    response_model=DeploymentPublic,
)
async def get_active_deployment(
    project_uuid: UUID,
    environment_uuid: UUID,
    deployment_service: Annotated[DeploymentService, Depends(DeploymentService)],
) -> DeploymentTable:
    """Get active deployment for an environment."""
    return deployment_service.get_active_deployment(
        environment_uuid
    )  # pragma: no cover


@environments_router.get(
    "/projects/{project_uuid}/environments/{environment_uuid}/function",
    response_model=FunctionPublic,
)
async def get_environment_function(
    project_uuid: UUID,
    environment_uuid: UUID,
    deployment_service: Annotated[DeploymentService, Depends(DeploymentService)],
) -> FunctionTable:
    """Get the currently active function for an environment."""
    return deployment_service.get_function_for_environment(
        environment_uuid
    )  # pragma: no cover


@environments_router.get(
    "/projects/{project_uuid}/environments/{environment_uuid}/history",
    response_model=Sequence[DeploymentPublic],
)
async def get_deployment_history(
    project_uuid: UUID,
    environment_uuid: UUID,
    deployment_service: Annotated[DeploymentService, Depends(DeploymentService)],
) -> Sequence[DeploymentTable]:
    """Get deployment history for an environment."""
    return deployment_service.get_deployment_history(
        environment_uuid
    )  # pragma: no cover
