"""The `/generations` API router."""

import base64
import hashlib
import re
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ..._utils import (
    construct_function,
    get_current_user,
    validate_api_key_project_no_strict,
    validate_api_key_project_strict,
)
from ...models import (
    GenerationTable,
    GenerationUpdate,
)
from ...schemas import (
    GenerationCreate,
    GenerationPublic,
    PlaygroundParameters,
    UserPublic,
)
from ...services import GenerationService, SpanService

generations_router = APIRouter()


@generations_router.get(
    "/projects/{project_uuid}/generations/metadata/names", response_model=Sequence[str]
)
async def get_unique_generation_names(
    project_uuid: UUID,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> Sequence[str]:
    """Get all unique generation names."""
    return generation_service.find_unique_generation_names_by_project_uuid(project_uuid)


@generations_router.get(
    "/projects/{project_uuid}/generations/{generation_uuid}",
    response_model=GenerationPublic,
)
async def get_generation_by_uuid(
    generation_uuid: UUID,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Get generation by UUID."""
    return generation_service.find_record_by_uuid(generation_uuid)


@generations_router.get(
    "/projects/{project_uuid}/generations/name/{generation_name}",
    response_model=Sequence[GenerationPublic],
)
async def get_generations_by_name(
    project_uuid: UUID,
    generation_name: str,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> Sequence[GenerationTable]:
    """Get generation by name."""
    return generation_service.find_generations_by_name(project_uuid, generation_name)


@generations_router.get(
    "/projects/{project_uuid}/generations/name/{generation_name}/version/{version_num}",
    response_model=GenerationPublic,
)
async def get_generation_by_version(
    project_uuid: UUID,
    generation_name: str,
    version_num: int,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Get generation by name."""
    return generation_service.find_generations_by_version(
        project_uuid, generation_name, version_num
    )


@generations_router.get(
    "/projects/{project_uuid}/generations/metadata/names/versions",
    response_model=Sequence[GenerationPublic],
)
async def get_latest_version_unique_generation_names(
    project_uuid: UUID,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> Sequence[GenerationTable]:
    """Get all unique generation names."""
    return generation_service.find_unique_generation_names(project_uuid)


@generations_router.get(
    "/projects/{project_uuid}/generations/hash/{generation_hash}",
    response_model=GenerationPublic,
)
async def get_generation_by_hash(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_strict)],
    project_uuid: UUID,
    generation_hash: str,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Get generation by hash."""
    return generation_service.find_record_by_hash(project_uuid, generation_hash)


@generations_router.get(
    "/projects/{project_uuid}/generations", response_model=Sequence[GenerationPublic]
)
async def get_generations(
    project_uuid: UUID,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> Sequence[GenerationTable]:
    """Grab all generations."""
    return generation_service.find_all_records(project_uuid=project_uuid)


@generations_router.get(
    "/projects/{project_uuid}/generations/{generation_uuid}",
    response_model=GenerationPublic,
)
async def get_generation(
    project_uuid: UUID,
    generation_uuid: UUID,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Grab generation by UUID."""
    return generation_service.find_record_by_uuid(
        generation_uuid, project_uuid=project_uuid
    )


@generations_router.post(
    "/projects/{project_uuid}/managed-generations",
    response_model=GenerationPublic,
)
async def create_prompt(
    project_uuid: UUID,
    generation_create: GenerationCreate,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Create a managed generation."""
    if not generation_create.prompt_template:
        raise HTTPException(
            detail="Prompt template is required.",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
    generation_create.is_managed = True
    generation_create.hash = hashlib.sha256(
        generation_create.prompt_template.encode("utf-8")
    ).hexdigest()
    if prompt := generation_service.check_duplicate_managed_generation(
        project_uuid, generation_create
    ):
        return prompt

    generation_create.code = construct_function(
        generation_create.arg_types or {}, generation_create.name, True
    )

    generation_create.signature = construct_function(
        generation_create.arg_types or {}, generation_create.name, False
    )
    generation_create.version_num = generation_service.get_next_version(
        project_uuid, generation_create.name
    )
    generations = generation_service.find_generations_by_signature(
        project_uuid, generation_create.signature
    )
    if len(generations) == 0:
        generation_create.is_default = True

    return generation_service.create_record(
        generation_create, project_uuid=project_uuid
    )


@generations_router.post(
    "/projects/{project_uuid}/generations", response_model=GenerationPublic
)
async def create_new_generation(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_strict)],
    project_uuid: UUID,
    generation_create: GenerationCreate,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Create a new generation version."""
    generation_create = generation_create.model_copy(
        update={
            "project_uuid": project_uuid,
            "version_num": generation_service.get_next_version(
                project_uuid, generation_create.name
            ),
        }
    )
    try:
        return generation_service.find_record_by_hash(
            project_uuid, generation_create.hash
        )
    except HTTPException:
        new_generation = generation_service.create_record(generation_create)
        return new_generation


@generations_router.patch(
    "/projects/{project_uuid}/generations/{generation_uuid}",
    response_model=GenerationPublic,
)
async def update_generation(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_no_strict)],
    project_uuid: UUID,
    generation_uuid: UUID,
    generation_update: GenerationUpdate,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> GenerationTable:
    """Update a generation."""
    return generation_service.update_record_by_uuid(
        generation_uuid,
        generation_update.model_dump(exclude_unset=True),
        project_uuid=project_uuid,
    )


@generations_router.delete(
    "/projects/{project_uuid}/generations/names/{generation_name}"
)
async def archive_generations_by_name(
    project_uuid: UUID,
    generation_name: str,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> bool:
    """Archive a generation by name and delete spans by generation name."""
    try:
        generation_service.archive_record_by_name(project_uuid, generation_name)
        span_service.delete_records_by_generation_name(project_uuid, generation_name)
    except Exception:
        return False
    return True


@generations_router.delete("/projects/{project_uuid}/generations/{generation_uuid}")
async def archive_generation(
    project_uuid: UUID,
    generation_uuid: UUID,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> bool:
    """Archive a generation and delete spans by generation UUID."""
    try:
        generation_service.archive_record_by_uuid(generation_uuid)
        span_service.delete_records_by_generation_uuid(project_uuid, generation_uuid)
    except Exception:
        return False
    return True


@generations_router.post("/projects/{project_uuid}/generations/run")
def run_version(
    project_uuid: UUID,
    playground_parameters: PlaygroundParameters,
    user: Annotated[UserPublic, Depends(get_current_user)],
) -> str:
    """Run version."""
    if not playground_parameters.generation:
        raise ValueError("Missing generation.")
    generation = playground_parameters.generation
    name = generation.name
    arg_list = [
        f"{arg_name}: {arg_type}" for arg_name, arg_type in generation.arg_types.items()
    ]
    func_def = f"def {name}({', '.join(arg_list)}) -> str: ..."
    wrapper_code = f'''
import os
import google.generativeai as genai
from lilypad._utils import create_mirascope_call
from lilypad.server.schemas import GenerationCreate, Provider
genai.configure(api_key="{user.keys.get("gemini", "")}")
os.environ["OPENAI_API_KEY"] = "{user.keys.get("openai", "")}"
os.environ["ANTHROPIC_API_KEY"] = "{user.keys.get("anthropic", "")}"
os.environ["OPENROUTER_API_KEY"] = "{user.keys.get("openrouter", "")}"
{func_def}
generation = GenerationCreate(
    name = "{generation.name}",
    signature = "{generation.signature}",
    prompt_template = """{generation.prompt_template}""",
    arg_types = {generation.arg_types},
    code = "{generation.code}",
    hash = "{generation.hash}",
    version_num = {generation.version_num}
)
# Python 3.10
provider = Provider("{playground_parameters.provider}")
# Python 3.11
# provider = {playground_parameters.provider}
model = "{playground_parameters.model}"
arg_values = {_decode_bytes(generation.arg_types, playground_parameters.arg_values)}
print(create_mirascope_call({name}, generation, provider, model, None)(**arg_values))
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
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            error_output = result.stderr.strip()
            import re

            # Find the last error line in the traceback
            error_match = re.search(r"(\w+Error.*?)$", error_output, re.DOTALL)
            if error_match:
                return error_match.group(1).strip()
            else:
                return error_output

    except Exception as e:
        return f"Exception: {str(e)}"
    finally:
        tmp_path.unlink()


def _decode_bytes(
    arg_types: dict[str, str], arg_values: dict[str, Any]
) -> dict[str, Any]:
    """Decodes image bytes from a dictionary of argument values.

    Parameters:
    arg_types (dict): Dictionary mapping argument names to their types
    arg_values (dict): Dictionary mapping argument names to their values

    Returns:
    dict: Dictionary mapping argument names to their decoded values
    """
    result = {}

    for arg_name, arg_type in arg_types.items():
        if arg_type == "bytes" and arg_name in arg_values:
            value = arg_values[arg_name]

            if isinstance(value, str):
                if value.startswith('b"') or value.startswith("b'"):
                    match = re.match(r'^b["\'](.*)["\']$', value, re.DOTALL)
                    if match:
                        value = match.group(1)

                try:
                    decoded_data = base64.b64decode(value)
                    result[arg_name] = decoded_data

                except Exception as e:
                    result[arg_name] = f"Error decoding image: {str(e)}"
            else:
                result[arg_name] = "Not a string value"
        else:
            if arg_name in arg_values:
                result[arg_name] = arg_values[arg_name]

    return result


__all__ = ["generations_router"]
