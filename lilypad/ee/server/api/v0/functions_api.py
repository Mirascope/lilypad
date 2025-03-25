"""The EE `/functions` API router."""

import base64
import json
import logging
import os
import re
import subprocess
import tempfile
from pathlib import Path
from textwrap import dedent
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from ....._utils import run_ruff
from .....server._utils import get_current_user
from .....server.schemas import (
    PlaygroundParameters,
    UserPublic,
)
from .....server.schemas.functions import AcceptedValue
from .....server.services import APIKeyService, FunctionService
from .....server.settings import get_settings

try:
    import resource

    CAN_LIMIT_RESOURCES = True
except ImportError:
    # For Windows
    class _Resource:
        """Dummy class for Windows."""

        RLIMIT_CPU = 0
        RLIMIT_AS = 0
        RLIMIT_NOFILE = 0

        @staticmethod
        def setrlimit(*args: Any, **kwargs: Any) -> int: ...

    resource = _Resource
    CAN_LIMIT_RESOURCES = False


functions_router = APIRouter()


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


@functions_router.post("/projects/{project_uuid}/functions/{function_uuid}/playground")
def run_playground(
    project_uuid: UUID,
    function_uuid: UUID,
    playground_parameters: PlaygroundParameters,
    user: Annotated[UserPublic, Depends(get_current_user)],
    function_service: Annotated[FunctionService, Depends(FunctionService)],
    api_key_service: Annotated[APIKeyService, Depends(APIKeyService)],
) -> str:
    """Run playground version."""
    function = function_service.find_record_by_uuid(function_uuid)
    api_keys = api_key_service.find_keys_by_user_and_project(project_uuid)
    if len(api_keys) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No API keys found"
        )
    specific_function_version_fn = (
        f"{function.name}.version({function.version_num})(**arg_values)"
    )

    # Sanitize and decode the argument values to prevent injection attacks
    safe_arg_types_and_values = sanitize_arg_types_and_values(
        function.arg_types, playground_parameters.arg_values
    )
    decoded_arg_values = _decode_bytes(safe_arg_types_and_values)
    # Serialize the user input as a JSON string
    json_arg_values = json.dumps(decoded_arg_values)
    user_args_code = f"arg_values = json.loads({json.dumps(json_arg_values)})"

    wrapper_code = f"""
import json
import os
import lilypad

lilypad.configure()

@lilypad.function(managed=True)
def {function.name}({", ".join(function.arg_types.keys())}) -> lilypad.Message: ...

{user_args_code}
res = {specific_function_version_fn}
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
    modified_code = run_ruff(dedent(modified_code)).strip()
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as tmp_file:
        tmp_file.write(modified_code)
        tmp_path = Path(tmp_file.name)
    env_vars["PATH"] = os.environ["PATH"]
    env_vars["LILYPAD_REMOTE_API_URL"] = get_settings().remote_api_url
    try:
        result = subprocess.run(
            ["uv", "run", str(tmp_path)],
            check=False,
            capture_output=True,
            text=True,
            env=env_vars,
            cwd=str(_PROJECT_ROOT),
            timeout=20,
            # preexec_fn=_limit_resources, # For test
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


__all__ = ["functions_router"]
