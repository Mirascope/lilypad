"""The `/prompts` API router."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends

from ...models import PromptPublic, PromptTable
from ...services import PromptService

prompts_router = APIRouter()


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
    "/projects/{project_uuid}/prompts/{prompt_uuid}/active",
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


# @prompts_router.post("/project/{project_uuid/prompts/{prompt_uuid}/run")
# async def run_prompt(
#     project_uuid: UUID,
#     prompt_uuid: UUID,
#     arg_values: dict[str, Any],
#     prompt_service: Annotated[PromptService, Depends(PromptService)],
# ) -> str:
#     """Run prompt."""
#     prompt = prompt_service.find_record_by_uuid(prompt_uuid)


# @versions_router.post("/projects/{project_uuid}/versions/{version_uuid}/run")
# def run_version(
#     project_uuid: UUID,
#     version_uuid: UUID,
#     arg_values: dict[str, Any],
#     version_service: Annotated[VersionService, Depends(VersionService)],
# ) -> str:
#     """Run version."""
#     version = version_service.find_record_by_uuid(version_uuid)
#     function = version.function
#     arg_types = function.arg_types or {}
#     arg_list = [f"{arg_name}: {arg_type}" for arg_name, arg_type in arg_types.items()]
#     func_def = f"def {function.name}({', '.join(arg_list)}) -> str: ..."
#     namespace: dict[str, Any] = {}
#     exec(func_def, namespace)
#     fn: Callable[..., str] = namespace[function.name]
#     lilypad.configure()
#     if not version.prompt:
#         return trace()(fn)(**arg_values)
#     prompt = PromptPublic.model_validate(version.prompt)
#     version_public = VersionPublic.model_validate(version)
#     decorator = create_mirascope_middleware(
#         version_public,
#         arg_types,
#         arg_values,
#         False,
#         prompt.template,
#     )
#     return create_mirascope_call(fn, prompt, decorator)(**arg_values)


__all__ = ["prompts_router"]
