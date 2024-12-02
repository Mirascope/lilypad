"""The `/versions` API router."""

import hashlib
from collections.abc import Callable, Sequence
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

import lilypad

from ...._utils import create_mirascope_call, create_mirascope_middleware
from ....traces import trace
from ..._utils import construct_function
from ...models import (
    ActiveVersionPublic,
    FunctionCreate,
    FunctionPublic,
    PromptCreate,
    PromptPublic,
    VersionCreate,
    VersionPublic,
    VersionTable,
)
from ...services import FunctionService, PromptService, VersionService

versions_router = APIRouter()


@versions_router.get(
    "/projects/{project_uuid}/versions/{version_uuid}", response_model=VersionPublic
)
async def get_version_by_uuid(
    version_uuid: UUID,
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> VersionTable:
    """Get version by UUID."""
    return version_service.find_record_by_uuid(version_uuid)


@versions_router.get(
    "/projects/{project_uuid}/functions/{function_name}/versions",
    response_model=Sequence[VersionPublic],
)
async def get_version_by_function_name(
    project_uuid: UUID,
    function_name: str,
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> Sequence[VersionTable]:
    """Get version by UUID."""
    return version_service.find_versions_by_function_name(project_uuid, function_name)


@versions_router.get(
    "/projects/{project_uuid}/functions/{function_hash}/versions/active",
    response_model=ActiveVersionPublic,
)
async def get_active_version(
    project_uuid: UUID,
    function_hash: str,
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> VersionTable:
    """Get active version for a prompt."""
    return version_service.find_prompt_active_version(project_uuid, function_hash)


@versions_router.patch(
    "/projects/{project_uuid}/versions/{version_uuid}/active",
    response_model=ActiveVersionPublic,
)
async def set_active_version(
    project_uuid: UUID,
    version_uuid: UUID,
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> VersionTable:
    """Set active version for synced function."""
    new_active_version = version_service.find_record_by_uuid(version_uuid)
    return version_service.change_active_version(project_uuid, new_active_version)


class FunctionAndPromptVersionCreate(BaseModel):
    """Function version (with prompt) create model."""

    function_create: FunctionCreate
    prompt_create: PromptCreate


@versions_router.post("/projects/{project_uuid}/versions", response_model=VersionPublic)
async def create_new_version(
    project_uuid: UUID,
    function_and_prompt_version_create: FunctionAndPromptVersionCreate,
    version_service: Annotated[VersionService, Depends(VersionService)],
    function_service: Annotated[FunctionService, Depends(FunctionService)],
    prompt_service: Annotated[PromptService, Depends(PromptService)],
) -> VersionTable:
    """Create a new function version with a prompt."""
    function_create = function_and_prompt_version_create.function_create
    prompt_create = function_and_prompt_version_create.prompt_create
    prompt_template_hash = hashlib.sha256(
        prompt_create.template.encode("utf-8")
    ).hexdigest()
    code = construct_function(function_create.arg_types or {}, function_create.name)
    function_hash = hashlib.sha256(code.encode("utf-8")).hexdigest()
    function_create = function_create.model_copy(
        update={"project_uuid": project_uuid, "hash": function_hash, "code": code}
    )
    try:
        function = function_service.find_record_by_hash(function_hash)
    except HTTPException:
        function = function_service.create_record(function_create)

    prompt_create = prompt_create.model_copy(
        update={"project_uuid": project_uuid, "hash": prompt_template_hash}
    )
    prompt = prompt_service.find_prompt_by_call_params(prompt_create)
    function_public = FunctionPublic.model_validate(function)

    if function and prompt:
        prompt_public = PromptPublic.model_validate(prompt)
        version = version_service.find_prompt_version_by_uuid(
            project_uuid, function_public.uuid, prompt_public.uuid
        )
        if version:
            return version

    if not prompt:
        prompt = prompt_service.create_record(prompt_create)

    prompt_public = PromptPublic.model_validate(prompt)
    num_versions = version_service.get_function_version_count(
        project_uuid, function.name
    )
    new_version = VersionCreate(
        version_num=num_versions + 1,
        project_uuid=project_uuid,
        function_uuid=function_public.uuid,
        function_name=function_public.name,
        function_hash=function_public.hash,
        prompt_hash=prompt_public.hash,
        prompt_uuid=prompt_public.uuid,
        is_active=num_versions == 0,
    )
    return version_service.create_record(new_version)


@versions_router.post(
    "/projects/{project_uuid}/versions/{function_hash}", response_model=VersionPublic
)
async def create_function_version_without_prompt(
    project_uuid: UUID,
    function_hash: str,
    function_create: FunctionCreate,
    version_service: Annotated[VersionService, Depends(VersionService)],
    function_service: Annotated[FunctionService, Depends(FunctionService)],
) -> VersionTable:
    """Create a new function version without a prompt."""
    existing_version = version_service.find_function_version_by_hash(
        project_uuid, function_hash
    )
    if existing_version:
        return existing_version

    function = function_service.create_record(
        function_create.model_copy(update={"project_uuid": project_uuid})
    )

    num_versions = version_service.get_function_version_count(
        project_uuid, function.name
    )
    new_version = VersionCreate(
        version_num=num_versions + 1,
        project_uuid=project_uuid,
        function_uuid=function.uuid,
        function_name=function.name,
        function_hash=function_hash,
    )
    return version_service.create_record(new_version)


@versions_router.get(
    "/projects/{project_uuid}/versions/{function_hash}", response_model=VersionPublic
)
async def get_function_version(
    project_uuid: UUID,
    function_hash: str,
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> VersionTable:
    """Get function version by hash."""
    version = version_service.find_function_version_by_hash(project_uuid, function_hash)
    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No function version not found",
        )
    return version


@versions_router.post("/projects/{project_uuid}/versions/{version_uuid}/run")
def run_version(
    project_uuid: UUID,
    version_uuid: UUID,
    arg_values: dict[str, Any],
    version_service: Annotated[VersionService, Depends(VersionService)],
) -> str:
    """Run version."""
    version = version_service.find_record_by_uuid(version_uuid)
    function = version.function
    arg_types = function.arg_types or {}
    arg_list = [f"{arg_name}: {arg_type}" for arg_name, arg_type in arg_types.items()]
    func_def = f"def {function.name}({', '.join(arg_list)}) -> str: ..."
    namespace: dict[str, Any] = {}
    exec(func_def, namespace)
    fn: Callable[..., str] = namespace[function.name]
    lilypad.configure()
    if not version.prompt:
        return trace()(fn)(**arg_values)
    prompt = PromptPublic.model_validate(version.prompt)
    version_public = VersionPublic.model_validate(version)
    decorator = create_mirascope_middleware(
        version_public,
        arg_types,
        arg_values,
        False,
        prompt.template,
    )
    return create_mirascope_call(fn, prompt, decorator)(**arg_values)


__all__ = ["versions_router"]
