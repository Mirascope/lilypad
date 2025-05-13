"""The `/functions` API router."""

import hashlib
from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ..._utils import (
    construct_function,
    get_current_environment,
    validate_api_key_project_no_strict,
    validate_api_key_project_strict,
)
from ...models import (
    FunctionTable,
    FunctionUpdate,
)
from ...models.environments import Environment
from ...schemas.functions import (
    FunctionCreate,
    FunctionPublic,
)
from ...services import DeploymentService, FunctionService, SpanService
from ...services.opensearch import OpenSearchService, get_opensearch_service

functions_router = APIRouter()


@functions_router.get(
    "/projects/{project_uuid}/functions/name/{function_name}/version/{version_num}",
    response_model=FunctionPublic,
)
async def get_function_by_version(
    project_uuid: UUID,
    function_name: str,
    version_num: int,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
) -> FunctionTable:
    """Get function by name."""
    return function_service.find_functions_by_version(
        project_uuid, function_name, version_num
    )


@functions_router.get(
    "/projects/{project_uuid}/functions/name/{function_name}",
    response_model=Sequence[FunctionPublic],
)
async def get_functions_by_name(
    project_uuid: UUID,
    function_name: str,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
) -> Sequence[FunctionTable]:
    """Get function by name."""
    return function_service.find_functions_by_name(project_uuid, function_name)


@functions_router.get(
    "/projects/{project_uuid}/functions/name/{function_name}/environments",
    response_model=FunctionPublic,
)
async def get_deployed_function_by_names(
    project_uuid: UUID,
    function_name: str,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
    deployment_service: Annotated[DeploymentService, Depends(DeploymentService)],
    environment: Annotated[Environment, Depends(get_current_environment)],
) -> FunctionTable:
    """Get the deployed function by function name and environment name."""
    deployment = deployment_service.get_specific_deployment(
        project_uuid,
        environment.uuid,
        function_name,  # pyright: ignore [reportArgumentType]
    )

    if not deployment:
        # get the latest function as fallback
        latest_function = function_service.find_latest_function_by_name(
            project_uuid, function_name
        )
        if latest_function:
            return latest_function
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Function '{function_name}' is not deployed in environment '{environment.name}'",
        )

    if not deployment.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Function '{function_name}' is deployed but not active in environment '{environment.name}'",
        )

    return deployment.function


@functions_router.post(
    "/projects/{project_uuid}/versioned-functions",
    response_model=FunctionPublic,
)
async def create_versioned_function(
    project_uuid: UUID,
    function_create: FunctionCreate,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
) -> FunctionTable:
    """Create a managed function."""
    if not function_create.prompt_template:
        raise HTTPException(
            detail="Prompt template is required.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    function_create.is_versioned = True
    function_create.code = construct_function(
        function_create.arg_types or {}, function_create.name, True
    )

    function_create.hash = hashlib.sha256(
        function_create.code.encode("utf-8")
    ).hexdigest()

    if function := function_service.check_duplicate_managed_function(
        project_uuid, function_create
    ):
        return function

    function_create.signature = construct_function(
        function_create.arg_types or {}, function_create.name, False
    )
    function_create.version_num = function_service.get_next_version(
        project_uuid, function_create.name
    )

    return function_service.create_record(function_create, project_uuid=project_uuid)


@functions_router.get(
    "/projects/{project_uuid}/functions/metadata/names", response_model=Sequence[str]
)
async def get_unique_function_names(
    project_uuid: UUID,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
) -> Sequence[str]:
    """Get all unique function names."""
    return function_service.find_unique_function_names_by_project_uuid(project_uuid)


@functions_router.get(
    "/projects/{project_uuid}/functions/metadata/names/versions",
    response_model=Sequence[FunctionPublic],
)
async def get_latest_version_unique_function_names(
    project_uuid: UUID,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
) -> Sequence[FunctionTable]:
    """Get all unique function names."""
    return function_service.find_unique_function_names(project_uuid)


@functions_router.get(
    "/projects/{project_uuid}/functions/hash/{function_hash}",
    response_model=FunctionPublic,
)
async def get_function_by_hash(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_strict)],
    project_uuid: UUID,
    function_hash: str,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
) -> FunctionTable:
    """Get function by hash."""
    return function_service.find_record_by_hash(project_uuid, function_hash)


@functions_router.get(
    "/projects/{project_uuid}/functions", response_model=Sequence[FunctionPublic]
)
async def get_functions(
    project_uuid: UUID,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
) -> Sequence[FunctionTable]:
    """Grab all functions."""
    return function_service.find_all_records(project_uuid=project_uuid)


@functions_router.get(
    "/projects/{project_uuid}/functions/{function_uuid}",
    response_model=FunctionPublic,
)
async def get_function(
    project_uuid: UUID,
    function_uuid: UUID,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
) -> FunctionTable:
    """Grab function by UUID."""
    return function_service.find_record_by_uuid(
        function_uuid, project_uuid=project_uuid
    )


@functions_router.post(
    "/projects/{project_uuid}/functions", response_model=FunctionPublic
)
async def create_new_function(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_strict)],
    project_uuid: UUID,
    function_create: FunctionCreate,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
) -> FunctionTable:
    """Create a new function version."""
    function_create = function_create.model_copy(
        update={
            "project_uuid": project_uuid,
            "version_num": function_service.get_next_version(
                project_uuid, function_create.name
            ),
        }
    )
    try:
        return function_service.find_record_by_hash(project_uuid, function_create.hash)
    except HTTPException:
        new_function = function_service.create_record(function_create)
        return new_function


@functions_router.patch(
    "/projects/{project_uuid}/functions/{function_uuid}",
    response_model=FunctionPublic,
)
async def update_function(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_no_strict)],
    project_uuid: UUID,
    function_uuid: UUID,
    function_update: FunctionUpdate,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
) -> FunctionTable:
    """Update a function."""
    return function_service.update_record_by_uuid(
        function_uuid,
        function_update.model_dump(exclude_unset=True),
        project_uuid=project_uuid,
    )


@functions_router.delete("/projects/{project_uuid}/functions/names/{function_name}")
async def archive_functions_by_name(
    project_uuid: UUID,
    function_name: str,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
    span_service: Annotated[SpanService, Depends(SpanService)],
    opensearch_service: Annotated[OpenSearchService, Depends(get_opensearch_service)],
) -> bool:
    """Archive a function by name and delete spans by function name."""
    try:
        archived_functions = function_service.archive_record_by_name(
            project_uuid, function_name
        )
        span_service.delete_records_by_function_name(project_uuid, function_name)
        if opensearch_service.is_enabled:
            for function in archived_functions:
                if function.uuid:
                    opensearch_service.delete_traces_by_function_uuid(
                        project_uuid, function.uuid
                    )
    except Exception:
        return False
    return True


@functions_router.delete("/projects/{project_uuid}/functions/{function_uuid}")
async def archive_function(
    project_uuid: UUID,
    function_uuid: UUID,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
    span_service: Annotated[SpanService, Depends(SpanService)],
    opensearch_service: Annotated[OpenSearchService, Depends(get_opensearch_service)],
) -> bool:
    """Archive a function and delete spans by function UUID."""
    try:
        function_service.archive_record_by_uuid(function_uuid)
        span_service.delete_records_by_function_uuid(project_uuid, function_uuid)
        if opensearch_service.is_enabled:
            opensearch_service.delete_traces_by_function_uuid(
                project_uuid, function_uuid
            )
    except Exception:
        return False
    return True


__all__ = ["functions_router"]
