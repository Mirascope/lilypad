"""The EE `/generations` API router."""

import base64
import hashlib
import json
import re
import subprocess
import tempfile
from pathlib import Path
from textwrap import dedent
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ee import Tier

from ....._utils.closure import _run_ruff
from .....server._utils import construct_function, get_current_user
from .....server.models import GenerationTable
from .....server.schemas import (
    GenerationCreate,
    GenerationPublic,
    PlaygroundParameters,
    UserPublic,
)
from .....server.services import APIKeyService, GenerationService
from ...require_license import require_license

generations_router = APIRouter()


@generations_router.post(
    "/projects/{project_uuid}/managed-generations",
    response_model=GenerationPublic,
)
@require_license(tier=Tier.ENTERPRISE)
async def create_managed_generation(
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
    if generation := generation_service.check_duplicate_managed_generation(
        project_uuid, generation_create
    ):
        return generation

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


@generations_router.post("/projects/{project_uuid}/generations/{generation_uuid}/run")
def run_version(
    project_uuid: UUID,
    generation_uuid: UUID,
    playground_parameters: PlaygroundParameters,
    user: Annotated[UserPublic, Depends(get_current_user)],
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
    api_key_service: Annotated[APIKeyService, Depends(APIKeyService)],
) -> str:
    """Run version."""
    if not playground_parameters.generation:
        raise ValueError("Missing generation.")
    generation = generation_service.find_record_by_uuid(generation_uuid)
    api_keys = api_key_service.find_keys_by_user_and_project(project_uuid)
    if len(api_keys) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No API keys found"
        )
    generation_dict = generation.model_dump()
    name = generation.name
    arg_list = [
        f"{arg_name}: {arg_type}" for arg_name, arg_type in generation.arg_types.items()
    ]
    func_def = f"def {name}({', '.join(arg_list)}) -> str: ..."
    wrapper_code = f'''
import os
from uuid import UUID
import google.generativeai as genai

import lilypad
from lilypad._utils import create_mirascope_call
from lilypad.server.schemas import Provider
from lilypad.server.models import GenerationTable

genai.configure(api_key="{user.keys.get("gemini", "")}")
os.environ["OPENAI_API_KEY"] = "{user.keys.get("openai", "")}"
os.environ["ANTHROPIC_API_KEY"] = "{user.keys.get("anthropic", "")}"
os.environ["OPENROUTER_API_KEY"] = "{user.keys.get("openrouter", "")}"
os.environ["LILYPAD_PROJECT_ID"] = "{project_uuid}"
os.environ["LILYPAD_API_KEY"] = (
    "{api_keys[0].key_hash}"
)

lilypad.configure()

@lilypad.generation()
{func_def}


generation = GenerationTable.model_validate({generation_dict})
# Python 3.10
provider = Provider("{playground_parameters.provider}")
# Python 3.11
# provider = {playground_parameters.provider}
model = "{playground_parameters.model}"
arg_values = {_decode_bytes(generation.arg_types, playground_parameters.arg_values)}
res = lilypad.generation()(
    create_mirascope_call(foo, generation, provider, model, None)
)(**arg_values)
'''
    try:
        processed_code = _run_playground(wrapper_code)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid API Key"
        )
    return processed_code


def _run_playground(code: str) -> str:
    # Add code to return a specific variable
    modified_code = (
        code + "\n\nimport json\nprint('__RESULT__' + json.dumps(res) + '__RESULT__')"
    )
    modified_code = _run_ruff(dedent(modified_code)).strip()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
        tmp_file.write(modified_code)
        tmp_path = Path(tmp_file.name)

    try:
        result = subprocess.run(
            ["uv", "run", str(tmp_path)],
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            # Extract the variable value from the output
            import re

            result_match = re.search(
                r"__RESULT__(.*?)__RESULT__", result.stdout, re.DOTALL
            )
            if result_match:
                try:
                    return json.loads(result_match.group(1))
                except json.JSONDecodeError:
                    return result_match.group(1)
            else:
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
