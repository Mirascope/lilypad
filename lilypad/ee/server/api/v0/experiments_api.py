"""API endpoints for managing experiments and runs (EE)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from .....server._utils import (
    validate_api_key_project_strict,
)
from ...schemas.experiments import ExperimentRunCreate, ExperimentRunPublic
from ...services.experiments import ExperimentDefinitionService, ExperimentRunService

experiments_router = APIRouter()


@experiments_router.post(
    "/projects/{project_uuid}/experiments/runs",
    response_model=ExperimentRunPublic,
    status_code=status.HTTP_201_CREATED,
    summary="Record an experiment run (EE)",
)
async def record_experiment_run(
    project_uuid: UUID,
    run_data: ExperimentRunCreate,
    _match_api_key: Annotated[bool, Depends(validate_api_key_project_strict)],
    definition_service: Annotated[
        ExperimentDefinitionService, Depends(ExperimentDefinitionService)
    ],
    run_service: Annotated[ExperimentRunService, Depends(ExperimentRunService)],
) -> ExperimentRunPublic:
    """Receives and stores the results of a completed experiment run from the SDK (EE)."""
    try:
        definition = definition_service.find_or_create_definition(
            project_uuid=project_uuid, name=run_data.experiment_name
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process experiment definition: {e}",
        )

    created_run = run_service.create_experiment_run(
        project_uuid=project_uuid, run_data=run_data, definition_uuid=definition.uuid
    )

    run_with_results = run_service.find_run_with_results(created_run.uuid)
    return ExperimentRunPublic.model_validate(run_with_results)


@experiments_router.get(
    "/experiments/runs/{run_uuid}",
    response_model=ExperimentRunPublic,
    summary="Get details of a specific experiment run (EE)",
)
async def get_experiment_run(
    run_uuid: UUID,
    run_service: Annotated[ExperimentRunService, Depends(ExperimentRunService)],
) -> ExperimentRunPublic:
    """Retrieves details of a specific experiment run, including its sample results (EE)."""
    run_with_results = run_service.find_run_with_results(run_uuid)
    return ExperimentRunPublic.model_validate(run_with_results)


__all__ = ["experiments_router"]
