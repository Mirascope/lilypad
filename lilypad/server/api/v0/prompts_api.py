"""The `/prompts` API router."""

import hashlib
from collections.abc import Callable, Sequence
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

import lilypad
from lilypad._utils import create_mirascope_call
from lilypad.server._utils import construct_function

from ...models import PromptCreate, PromptPublic, PromptTable, PromptUpdate, Provider
from ...services import PromptService

prompts_router = APIRouter()


@prompts_router.get(
    "/projects/{project_uuid}/prompts/metadata/names", response_model=Sequence[str]
)
async def get_unique_generation_names(
    project_uuid: UUID,
    prompt_service: Annotated[PromptService, Depends(PromptService)],
) -> Sequence[str]:
    """Get all unique prompt names."""
    return prompt_service.find_unique_prompt_names(project_uuid)


@prompts_router.get(
    "/projects/{project_uuid}/prompts/metadata/signature",
    response_model=Sequence[PromptPublic],
)
async def get_prompts_by_signature(
    project_uuid: UUID,
    prompt_service: Annotated[PromptService, Depends(PromptService)],
    signature: str = Query(...),
) -> Sequence[PromptTable]:
    """Get all prompts by signature."""
    return prompt_service.find_prompts_by_signature(project_uuid, signature)


@prompts_router.get(
    "/projects/{project_uuid}/prompts/name/{prompt_name}",
    response_model=Sequence[PromptPublic],
)
async def get_prompts_by_name(
    project_uuid: UUID,
    prompt_name: str,
    prompt_service: Annotated[PromptService, Depends(PromptService)],
) -> Sequence[PromptTable]:
    """Get prompts by name."""
    return prompt_service.find_prompts_by_name(project_uuid, prompt_name)


@prompts_router.get(
    "/projects/{project_uuid}/prompts/{prompt_uuid}", response_model=PromptPublic
)
async def get_prompt_by_uuid(
    project_uuid: UUID,
    prompt_uuid: UUID,
    prompt_service: Annotated[PromptService, Depends(PromptService)],
) -> PromptTable:
    """Get prompt by uuid."""
    return prompt_service.find_record_by_uuid(prompt_uuid, project_uuid=project_uuid)


@prompts_router.get(
    "/projects/{project_uuid}/prompts/hash/{prompt_hash}/active",
    response_model=PromptPublic,
)
async def get_prompt_active_version_by_hash(
    project_uuid: UUID,
    prompt_hash: str,
    prompt_service: Annotated[PromptService, Depends(PromptService)],
) -> PromptTable:
    """Get prompt by hash."""
    return prompt_service.find_prompt_active_version_by_hash(prompt_hash)


@prompts_router.patch(
    "/projects/{project_uuid}/prompts/{prompt_uuid}/default",
    response_model=PromptPublic,
)
async def set_active_version(
    project_uuid: UUID,
    prompt_uuid: UUID,
    prompt_service: Annotated[PromptService, Depends(PromptService)],
) -> PromptTable:
    """Set active version for synced function."""
    new_active_version = prompt_service.find_record_by_uuid(prompt_uuid)
    return prompt_service.change_active_version(project_uuid, new_active_version)


@prompts_router.post(
    "/projects/{project_uuid}/prompts",
    response_model=PromptPublic,
)
async def create_prompt(
    project_uuid: UUID,
    prompt_create: PromptCreate,
    prompt_service: Annotated[PromptService, Depends(PromptService)],
) -> PromptTable:
    """Create a prompt."""
    prompt_create.hash = hashlib.sha256(
        prompt_create.template.encode("utf-8")
    ).hexdigest()
    if prompt := prompt_service.find_prompt_by_call_params(prompt_create):
        return prompt

    prompt_create.code = construct_function(
        prompt_create.arg_types or {}, prompt_create.name, True
    )

    prompt_create.signature = construct_function(
        prompt_create.arg_types or {}, prompt_create.name, False
    )

    prompts = prompt_service.find_prompts_by_signature(
        project_uuid, prompt_create.signature
    )
    if len(prompts) == 0:
        prompt_create.is_default = True

    return prompt_service.create_record(prompt_create, project_uuid=project_uuid)


@prompts_router.patch(
    "/projects/{project_uuid}/prompts/{prompt_uuid}",
    response_model=PromptPublic,
)
async def update_generation(
    project_uuid: UUID,
    prompt_uuid: UUID,
    generation_update: PromptUpdate,
    prompt_service: Annotated[PromptService, Depends(PromptService)],
) -> PromptTable:
    """Update a prompt."""
    return prompt_service.update_record_by_uuid(
        prompt_uuid,
        generation_update.model_dump(exclude_unset=True),
        project_uuid=project_uuid,
    )


class PlaygroundParameters(BaseModel):
    arg_values: dict[str, Any]
    provider: Provider
    model: str
    prompt: PromptCreate | None = None


@prompts_router.post("/projects/{project_uuid}/prompts/run")
def run_version(
    project_uuid: UUID,
    playground_parameters: PlaygroundParameters,
) -> str:
    """Run version."""
    if not playground_parameters.prompt:
        raise ValueError("Missing prompt.")
    prompt = playground_parameters.prompt
    arg_types = prompt.arg_types
    name = prompt.name
    arg_list = [f"{arg_name}: {arg_type}" for arg_name, arg_type in arg_types.items()]
    func_def = f"def {name}({', '.join(arg_list)}) -> str: ..."
    namespace: dict[str, Any] = {}
    exec(func_def, namespace)
    fn: Callable[..., str] = namespace[name]
    lilypad.configure()
    return create_mirascope_call(
        fn, prompt, playground_parameters.provider, playground_parameters.model, None
    )(**playground_parameters.arg_values)


__all__ = ["prompts_router"]
