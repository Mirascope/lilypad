"""The `/prompts` API router."""

import hashlib
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..._utils import construct_function, get_current_user
from ...models import (
    PlaygroundParameters,
    PromptCreate,
    PromptPublic,
    PromptTable,
    PromptUpdate,
    UserPublic,
)
from ...services import PromptService

prompts_router = APIRouter()


@prompts_router.get(
    "/projects/{project_uuid}/prompts/metadata/names",
    response_model=Sequence[PromptPublic],
)
async def get_unique_generation_names(
    project_uuid: UUID,
    prompt_service: Annotated[PromptService, Depends(PromptService)],
) -> Sequence[PromptTable]:
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
    if prompt := prompt_service.check_duplicate_prompt(prompt_create):
        return prompt

    prompt_create.code = construct_function(
        prompt_create.arg_types or {}, prompt_create.name, True
    )

    prompt_create.signature = construct_function(
        prompt_create.arg_types or {}, prompt_create.name, False
    )
    prompt_create.version_num = prompt_service.get_next_version(
        project_uuid, prompt_create.name
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


@prompts_router.post("/projects/{project_uuid}/prompts/run")
def run_version(
    project_uuid: UUID,
    playground_parameters: PlaygroundParameters,
    user: Annotated[UserPublic, Depends(get_current_user)],
) -> str:
    """Run version."""
    if not playground_parameters.prompt:
        raise ValueError("Missing prompt.")
    prompt = playground_parameters.prompt
    name = prompt.name
    arg_list = [
        f"{arg_name}: {arg_type}" for arg_name, arg_type in prompt.arg_types.items()
    ]
    func_def = f"def {name}({', '.join(arg_list)}) -> str: ..."
    wrapper_code = f'''
import os

import google.generativeai as genai

from lilypad._utils import create_mirascope_call
from lilypad.server.models import PromptCreate, Provider

genai.configure(api_key="{user.keys.get("gemini", "")}")
os.environ["OPENAI_API_KEY"] = "{user.keys.get("openai", "")}"
os.environ["ANTHROPIC_API_KEY"] = "{user.keys.get("anthropic", "")}"
os.environ["OPENROUTER_API_KEY"] = "{user.keys.get("openrouter", "")}"

{func_def}

prompt = PromptCreate(
    name = "{prompt.name}",
    signature = "{prompt.signature}",
    template = """{prompt.template}""",
    arg_types = {prompt.arg_types},
    code = "{prompt.code}",
    hash = "{prompt.hash}",
    version_num = {prompt.version_num}
)
provider = Provider("{playground_parameters.provider}")
model = "{playground_parameters.model}"
arg_values = {playground_parameters.arg_values}
print(create_mirascope_call({name}, prompt, provider, model, None)(**arg_values))
'''
    try:
        processed_code = _run_playground(wrapper_code)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid API Key"
        )
    return processed_code


def _run_playground(code: str) -> str:
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
        tmp_file.write(code)
        tmp_path = Path(tmp_file.name)

    try:
        result = subprocess.run(
            ["uv", "run", str(tmp_path)],
            check=True,
            capture_output=True,
            text=True,
        )
        return result.stdout.strip()
    finally:
        tmp_path.unlink()


__all__ = ["prompts_router"]
