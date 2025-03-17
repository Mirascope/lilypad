"""The EE `/generations` API router."""

import base64
import hashlib
import json
import logging
import os
import re
import subprocess
import tempfile
from collections.abc import Sequence
from pathlib import Path
from textwrap import dedent
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ee import Tier

from ....._utils.closure import _run_ruff
from .....ee.server.services import (
    DeploymentService,
    GenerationService,
)
from .....server._utils import construct_function, get_current_user
from .....server.models import GenerationTable
from .....server.schemas import (
    GenerationCreate,
    GenerationPublic,
    PlaygroundParameters,
    UserPublic,
)
from .....server.schemas.generations import AcceptedValue
from .....server.services import APIKeyService
from ..._utils import get_current_environment
from ...models.environments import Environment
from ...require_license import require_license

try:
    import resource

    CAN_LIMIT_RESOURCES = True
except ImportError:
    # For Windows
    CAN_LIMIT_RESOURCES = False


generations_router = APIRouter()


logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parents[3]


def sanitize_arg_types_and_values(
    arg_types: dict[str, str], arg_values: dict[str, AcceptedValue]
) -> dict[str, tuple[str, AcceptedValue]]:
    return {
        key: (arg_types[key], arg_values[key]) for key in arg_types if key in arg_values
    }


def _limit_resources(timeout: int = 15, memory: int = 200) -> None:
    if not CAN_LIMIT_RESOURCES:
        return None
    try:
        # Limit CPU time to 15 seconds
        resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
        # Limit process address space (memory) to 100MB
        resource.setrlimit(
            resource.RLIMIT_AS, (memory * 1024 * 1024, memory * 1024 * 1024)
        )
    except Exception as e:
        logger.error("Failed to set resource limits: %s", e)


@generations_router.get(
    "/projects/{project_uuid}/generations/name/{generation_name}/version/{version_num}",
    response_model=GenerationPublic,
)
@require_license(tier=Tier.ENTERPRISE)
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
    "/projects/{project_uuid}/generations/name/{generation_name}",
    response_model=Sequence[GenerationPublic],
)
@require_license(tier=Tier.ENTERPRISE)
async def get_generations_by_name(
    project_uuid: UUID,
    generation_name: str,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
) -> Sequence[GenerationTable]:
    """Get generation by name."""
    return generation_service.find_generations_by_name(project_uuid, generation_name)


@generations_router.get(
    "/projects/{project_uuid}/generations/name/{generation_name}/environments",
    response_model=GenerationPublic,
)
@require_license(tier=Tier.ENTERPRISE)
async def get_deployed_generation_by_names(
    project_uuid: UUID,
    generation_name: str,
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
    deployment_service: Annotated[DeploymentService, Depends(DeploymentService)],
    environment: Annotated[Environment, Depends(get_current_environment)],
) -> GenerationTable:
    """Get the deployed generation by generation name and environment name."""
    deployment = deployment_service.get_specific_deployment(
        project_uuid,
        environment.uuid,
        generation_name,  # pyright: ignore [reportArgumentType]
    )

    if not deployment:
        # get the latest generation as fallback
        latest_generation = generation_service.find_latest_generation_by_name(
            project_uuid, generation_name
        )
        if latest_generation:
            return latest_generation
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Generation '{generation_name}' is not deployed in environment '{environment.name}'",
        )

    if not deployment.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Generation '{generation_name}' is deployed but not active in environment '{environment.name}'",
        )

    return deployment.generation


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
    generation_create.code = construct_function(
        generation_create.arg_types or {}, generation_create.name, True
    )

    generation_create.hash = hashlib.sha256(
        generation_create.code.encode("utf-8")
    ).hexdigest()

    if generation := generation_service.check_duplicate_managed_generation(
        project_uuid, generation_create
    ):
        return generation

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
    generation = generation_service.find_record_by_uuid(generation_uuid)
    api_keys = api_key_service.find_keys_by_user_and_project(project_uuid)
    if len(api_keys) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No API keys found"
        )
    specific_generation_version_fn = (
        f"{generation.name}.version({generation.version_num})(**arg_values)"
    )

    # Sanitize and decode the argument values to prevent injection attacks
    safe_arg_types_and_values = sanitize_arg_types_and_values(
        generation.arg_types, playground_parameters.arg_values
    )
    decoded_arg_values = _decode_bytes(safe_arg_types_and_values)
    # Serialize the user input as a JSON string
    json_arg_values = json.dumps(decoded_arg_values)
    user_args_code = f"arg_values = json.loads({json.dumps(json_arg_values)!r})"

    wrapper_code = f"""
import json
import os
import lilypad

lilypad.configure()

def {generation.name}({", ".join(generation.arg_types.keys())}) -> lilypad.Message: ...

{user_args_code}
res = {specific_generation_version_fn}
"""

    env_vars = {
        "OPENAI_API_KEY": user.keys.get("openai", ""),
        "ANTHROPIC_API_KEY": user.keys.get("anthropic", ""),
        "GOOGLE_API_KEY": user.keys.get("gemini", ""),
        "OPENROUTER_API_KEY": user.keys.get("openrouter", ""),
        "LILYPAD_PROJECT_ID": str(project_uuid),
        "LILYPAD_API_KEY": api_keys[0].key_hash,
    }

    try:
        processed_code = _run_playground(wrapper_code, env_vars)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid API Key"
        )
    return processed_code


def _run_playground(code: str, env_vars: dict[str, str]) -> str:
    """Run code in playground with environment variables passed to subprocess.

    Args:
        code: The Python code to execute
        env_vars: Dictionary of environment variables to pass to the subprocess

    Returns:
        The result of code execution
    """
    # Add code to return a specific variable
    modified_code = code + "\n\nprint('__RESULT__', res, '__RESULT__')"
    modified_code = _run_ruff(dedent(modified_code)).strip()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
        tmp_file.write(modified_code)
        tmp_path = Path(tmp_file.name)
    env_vars["PATH"] = os.environ["PATH"]
    try:
        result = subprocess.run(
            ["uv", "run", str(tmp_path)],
            check=False,
            capture_output=True,
            text=True,
            env=env_vars,
            cwd=str(_PROJECT_ROOT),
            timeout=20,
            preexec_fn=_limit_resources,
        )
    except subprocess.TimeoutExpired:
        logger.error("Subprocess execution timed out. File: %s", tmp_path)
        return "Execution timed out"
    except Exception:
        logger.exception("Subprocess execution failed")
        return "Internal execution error"
    finally:
        try:
            tmp_path.unlink()
        except Exception as e:
            logger.warning("Failed to delete temporary file: %s", e)

    if result.returncode == 0:
        result_match = re.search(r"__RESULT__(.*?)__RESULT__", result.stdout, re.DOTALL)
        if result_match:
            try:
                return json.loads(result_match.group(1))
            except json.JSONDecodeError:
                return result_match.group(1)
        else:
            return result.stdout.strip()

    else:
        logger.error("Subprocess returned an error: %s", result.stderr.strip())
        return "Code execution error"


def _decode_bytes(
    arg_types_and_values: dict[str, tuple[str, AcceptedValue]],
) -> dict[str, Any]:
    """Decodes image bytes from a dictionary of argument values.

    Parameters:
        arg_types_and_values (dict): Dictionary mapping argument names to their types and values

    Returns:
        dict: Dictionary mapping argument names to their decoded values
    """
    result = {}

    for arg_name, (arg_type, arg_value) in arg_types_and_values.items():
        if arg_type == "bytes":
            if isinstance(arg_value, str):
                try:
                    decoded_data = base64.b64decode(arg_value, validate=True)
                    result[arg_name] = decoded_data

                except Exception as e:
                    raise ValueError(f"Invalid Base64 encoding: {str(e)}")
            else:
                raise ValueError(f"Expected bytes, got {type(arg_value)}")
        else:
            result[arg_name] = arg_value

    return result


__all__ = ["generations_router"]
