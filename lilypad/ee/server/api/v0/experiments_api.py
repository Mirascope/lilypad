"""API endpoints for managing experiments and runs (EE)."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ...schemas.experiments import (
    ExperimentDefinitionPublic,
    ExperimentRunCreate,
    ExperimentRunPublic,
    ExperimentRunSummaryPublic,
)
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
    "/projects/{project_uuid}/experiments/{definition_uuid}/runs",
    response_model=list[ExperimentRunSummaryPublic],
    summary="List experiment runs for a definition",
)
async def list_experiment_runs(
    run_service: Annotated[ExperimentRunService, Depends(ExperimentRunService)],
    project_uuid: UUID,
    definition_uuid: UUID,
    limit: int = 100,
    offset: int = 0,
) -> list[ExperimentRunSummaryPublic]:
    """Retrieves a list of experiment runs associated with a specific experiment definition."""
    runs = run_service.find_runs_by_definition_uuid(
        definition_uuid=definition_uuid, limit=limit, offset=offset
    )
    return [ExperimentRunSummaryPublic.model_validate(run) for run in runs]


@experiments_router.get(
    "/projects/{project_uuid}/experiments",
    response_model=list[ExperimentDefinitionPublic],
    summary="List experiment definitions in a project",
)
async def list_experiment_definitions(
    project_uuid: UUID,
    definition_service: Annotated[
        ExperimentDefinitionService, Depends(ExperimentDefinitionService)
    ],
) -> list[ExperimentDefinitionPublic]:
    """Retrieves a list of all experiment definitions within the specified project."""
    definitions = definition_service.find_all_records(project_uuid=project_uuid)
    return [ExperimentDefinitionPublic.model_validate(d) for d in definitions]


__all__ = ["experiments_router"]
