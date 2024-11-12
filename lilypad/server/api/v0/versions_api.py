"""The `/versions` API router."""

from collections.abc import Callable
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from ...._configure import configure
from ...._utils import create_mirascope_call, create_mirascope_middleware
from ....traces import trace
from ...models import (
    ActiveVersionPublic,
    FunctionCreate,
    FunctionPublic,
    PromptPublic,
    VersionCreate,
    VersionPublic,
    VersionTable,
)
from ...services import FunctionService, VersionService

versions_router = APIRouter()


@versions_router.get(
    "/projects/{project_id}/versions/{version_id:int}", response_model=VersionPublic
)
async def get_version_by_id(
    version_id: int, version_service: Annotated[VersionService, Depends(VersionService)]
) -> VersionTable:
    """Get version by ID."""
    return version_service.find_record_by_id(version_id)


@versions_router.get(
    "/projects/{project_id}/versions/{function_hash}/active",
    response_model=ActiveVersionPublic,
)
async def get_active_version(
    project_id: int,
    function_hash: str,
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> VersionTable:
    """Get active version for a prompt."""
    return version_service.find_prompt_active_version(project_id, function_hash)


@versions_router.patch(
    "/projects/{project_id}/versions/{version_id}/active",
    response_model=ActiveVersionPublic,
)
async def set_active_version(
    project_id: int,
    version_id: int,
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> VersionTable:
    """Set active version for synced function."""
    new_active_version = version_service.find_record_by_id(version_id)
    return version_service.change_active_version(project_id, new_active_version)


class FunctionVersionCreate(BaseModel):
    """Function version (without prompt) create model."""

    name: str
    hash: str
    code: str
    arg_types: dict[str, str]


@versions_router.post(
    "/projects/{project_id}/versions/{function_hash}", response_model=VersionPublic
)
async def create_function_version_without_prompt(
    project_id: int,
    function_hash: str,
    function_version_create: FunctionVersionCreate,
    version_service: Annotated[VersionService, Depends(VersionService)],
    function_service: Annotated[FunctionService, Depends(FunctionService)],
) -> VersionTable:
    """Create a new function version without a prompt."""
    existing_version = version_service.find_function_version_by_hash(
        project_id, function_hash
    )
    if existing_version:
        return existing_version

    new_function = FunctionCreate(
        name=function_version_create.name,
        hash=function_version_create.hash,
        code=function_version_create.code,
        arg_types=function_version_create.arg_types,
        project_id=project_id,
    )
    function = FunctionPublic.model_validate(
        function_service.create_record(new_function)
    )

    num_versions = version_service.get_function_version_count(project_id, function.name)
    new_version = VersionCreate(
        version_num=num_versions + 1,
        project_id=project_id,
        function_id=function.id,
        function_name=function.name,
        function_hash=function_hash,
    )
    return version_service.create_record(new_version)


@versions_router.get(
    "/projects/{project_id}/versions/{function_hash}", response_model=VersionPublic
)
async def get_function_version(
    project_id: int,
    function_hash: str,
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> VersionTable:
    """Get function version by hash."""
    version = version_service.find_function_version_by_hash(project_id, function_hash)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No function version not found",
        )
    return version


# TODO: Getting RuntimeError: asyncio.run() cannot be called from a running event loop
# when running Anthropic calls, but not OpenAI
@versions_router.post("/projects/{project_id}/versions/{version_id}/run")
def run_version(
    project_id: int,
    version_id: int,
    arg_values: dict[str, Any],
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> str:
    """Run version."""
    version = VersionPublic.model_validate(
        version_service.find_record_by_id(version_id)
    )
    function = version.function
    arg_types = function.arg_types or {}
    configure()

    arg_list = [f"{arg_name}: {arg_type}" for arg_name, arg_type in arg_types.items()]
    func_def = f"def {function.name}({', '.join(arg_list)}) -> str: ..."
    namespace: dict[str, Any] = {}
    exec(func_def, namespace)
    fn: Callable[..., str] = namespace[function.name]

    if not version.prompt:
        return trace()(fn)(**arg_values)

    prompt = PromptPublic.model_validate(version.prompt)
    decorator = create_mirascope_middleware(
        version, arg_types, arg_values, False, prompt.template
    )
    return create_mirascope_call(fn, prompt, decorator)(**arg_values)


__all__ = ["versions_router"]
