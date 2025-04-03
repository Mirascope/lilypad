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
from .....server.schemas import (
    PlaygroundParameters,
)
from .....server.schemas.functions import AcceptedValue
from .....server.services import APIKeyService, FunctionService
from .....server.services.user_external_api_key_service import UserExternalAPIKeyService
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

        @staticmethod
        def getrlimit(*args: Any, **kwargs: Any) -> tuple[int, int]: ...


    resource = _Resource
    CAN_LIMIT_RESOURCES = False


functions_router = APIRouter()


logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).parents[5]


def sanitize_arg_types_and_values(
    arg_types: dict[str, str], arg_values: dict[str, AcceptedValue]
) -> dict[str, tuple[str, AcceptedValue]]:
    """Sanitize argument types and values to prevent injection attacks.

    Args:
        arg_types: Dictionary mapping argument names to their types
        arg_values: Dictionary mapping argument names to their values

    Returns:
        Dictionary mapping argument names to tuples of (type, value)
    """
    return {
        key: (arg_types[key], arg_values[key]) for key in arg_types if key in arg_values
    }


def _validate_python_identifier(name: str) -> bool:
    """Validate if a string is a valid Python identifier.

    Args:
        name: The string to validate

    Returns:
        True if valid, False otherwise
    """
    if not name:
        return False

    # Check if it matches the pattern for a valid identifier
    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", name):
        logger.warning(f"Invalid Python identifier format: {name}")
        return False

    # Check if it's not a Python keyword
    import keyword

    if keyword.iskeyword(name):
        logger.warning(f"Python keyword cannot be used as identifier: {name}")
        return False

    # Check if it's not a Python built-in
    if name in dir(__builtins__):
        logger.warning(f"Python built-in cannot be used as identifier: {name}")
        return False

    return True


def _validate_function_data(function: Any) -> bool:
    """Validate all function data for security.

    Args:
        function: The function data to validate

    Returns:
        True if all validations pass, False otherwise
    """
    # Validate function name
    if not _validate_python_identifier(function.name):
        logger.warning(f"Invalid function name: {function.name}")
        return False

    # Validate prompt template
    if not _validate_template_string(function.prompt_template):
        logger.warning("Invalid template string in function")
        return False

    # Validate call_params - ensure it's JSON serializable
    try:
        json.dumps(function.call_params)
    except (TypeError, ValueError):
        logger.warning("call_params is not JSON serializable")
        return False

    # Validate arg_types - ensure all keys are valid Python identifiers
    for arg_name in function.arg_types:
        if not _validate_python_identifier(arg_name):
            logger.warning(f"Invalid argument name: {arg_name}")
            return False

    return True


def _validate_api_keys(env_vars: dict[str, str]) -> dict[str, str]:
    """Validate API keys to prevent environment variable injection attacks.

    Args:
        env_vars: Dictionary of environment variables

    Returns:
        Dictionary with validated environment variables
    """
    sanitized_env = env_vars.copy()

    # API key validation pattern for common LLM providers
    api_key_vars = [
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "GOOGLE_API_KEY",
        "OPENROUTER_API_KEY",
    ]

    # Validate each API key
    for key_var in api_key_vars:
        if key_var in sanitized_env and sanitized_env[key_var]:
            value = sanitized_env[key_var]

            # Check for command injection characters
            if re.search(r"[;&|`$><]", value):
                logger.warning(
                    f"Potential injection attempt in {key_var}, removing value"
                )
                sanitized_env[key_var] = ""
                continue

            # Basic validation - most API keys are alphanumeric with possible dashes/underscores
            if not re.match(r"^[a-zA-Z0-9_\-]{20,200}$", value):
                logger.warning(f"Invalid {key_var} format, removing value")
                sanitized_env[key_var] = ""

    return sanitized_env


def _limit_resources(timeout: int = 180, memory: int = 8192) -> None:
    """Limit system resources to prevent resource exhaustion attacks.

    Args:
        timeout: CPU time limit in seconds
        memory: Memory limit in MB
    """
    if not CAN_LIMIT_RESOURCES:
        return None
    try:
        # Limit CPU time
        resource.setrlimit(resource.RLIMIT_CPU, (timeout, timeout))
        # Limit process address space (memory)
        resource.setrlimit(
            resource.RLIMIT_AS, (memory * 1024 * 1024, memory * 1024 * 1024)
        )
        # Limit number of open files. Torch can open many files, so we set it to 20K * 10
        rlimit = resource.getrlimit(resource.RLIMIT_NOFILE)
        resource.setrlimit(resource.RLIMIT_NOFILE, (2048 * 20, rlimit[1]))
    except Exception as e:
        logger.error("Failed to set resource limits: %s", e)


def _validate_template_values(provider: str, model: str) -> bool:
    """Validate template values for security issues.

    Args:
        provider: LLM provider name
        model: Model name

    Returns:
        True if values are safe, False otherwise
    """
    # Check provider (should only contain alphanumeric, dots, hyphens)
    if not re.match(r"^[a-zA-Z0-9\.\-_]+$", provider):
        logger.warning(f"Invalid provider format: {provider}")
        return False

    # Check model (should only contain alphanumeric, dots, hyphens, slashes)
    if not re.match(r"^[a-zA-Z0-9\.\-_/]+$", model):
        logger.warning(f"Invalid model format: {model}")
        return False

    return True


@functions_router.post("/projects/{project_uuid}/functions/{function_uuid}/playground")
def run_playground(
    project_uuid: UUID,
    function_uuid: UUID,
    playground_parameters: PlaygroundParameters,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
    api_key_service: Annotated[APIKeyService, Depends(APIKeyService)],
    user_external_api_key_service: Annotated[
        UserExternalAPIKeyService, Depends(UserExternalAPIKeyService)
    ],
) -> str:
    """Run playground version of a function with enhanced security.

    Args:
        project_uuid: UUID of the project
        function_uuid: UUID of the function
        playground_parameters: Parameters for the playground execution
        function_service: Service for function management
        api_key_service: Service for API key management
        user_external_api_key_service: Service for external API key management

    Returns:
        Result of the function execution
    """
    # Get the function from the database
    function = function_service.find_record_by_uuid(function_uuid)

    if not function:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Function not found"
        )
    # Validate all function data for security
    if not _validate_function_data(function):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Function contains potentially unsafe data",
        )

    # Get API keys for the project
    api_keys = api_key_service.find_keys_by_user_and_project(project_uuid)
    if len(api_keys) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="No API keys found"
        )

    # Extract required values from playground_parameters
    provider = playground_parameters.provider.value
    model = playground_parameters.model

    # Validate provider and model values
    if not _validate_template_values(provider, model):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid provider or model values detected",
        )

    # Prepare function arguments string - with validation
    arg_definitions = []

    arg_types = (
        playground_parameters.arg_types
        if playground_parameters.arg_types is not None
        else function.arg_types
    )
    for arg_name in arg_types:
        if arg_name == "trace_ctx":
            continue  # Skip trace context argument
        # Double-check that argument names are valid Python identifiers
        if not _validate_python_identifier(arg_name):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid argument name: {arg_name}",
            )
        arg_definitions.append(f"{arg_name}")

    arguments_str = ", " + ", ".join(arg_definitions) if arg_definitions else ""

    function_code = """
import lilypad
from mirascope import llm, prompt_template


lilypad.configure(auto_llm=True)

@lilypad.trace(versioning="automatic")
@llm.call(provider={provider}, model={model}, call_params={call_params})
@prompt_template({template})
def {function_name}(trace_ctx{arguments}) -> None:
    trace_ctx.metadata({{"scope": "playground"}})
""".format(
        provider=json.dumps(provider),
        model=json.dumps(model),
        call_params=json.dumps(
            (
                playground_parameters.call_params
                if playground_parameters.call_params is not None
                else function.call_params
            )
            or {}
        ),
        template=json.dumps(
            (
                playground_parameters.prompt_template
                if playground_parameters.prompt_template is not None
                else function.prompt_template
            )
            or ""
        ),
        function_name=function.name,  # Already validated
        arguments=arguments_str,  # Already validated
    )

    # Sanitize and decode the argument values
    safe_arg_types_and_values = sanitize_arg_types_and_values(
        arg_types, playground_parameters.arg_values
    )
    decoded_arg_values = _decode_bytes(safe_arg_types_and_values)

    # Serialize user input as a JSON string with proper escaping
    json_arg_values = json.dumps(decoded_arg_values)
    user_args_code = f"arg_values = json.loads({json.dumps(json_arg_values)})"

    wrapper_code = f"""
import json
import os


{function_code}

{user_args_code}
response = {function.name}(**arg_values)
"""
    external_api_key_names = user_external_api_key_service.list_api_keys().keys()
    external_api_keys = {
        name: user_external_api_key_service.get_api_key(name)
        if name in external_api_key_names
        else ""
        for name in ["openai", "anthropic", "gemini", "openrouter"]
    }
    settings = get_settings()
    env_vars = {
        "OPENAI_API_KEY": external_api_keys["openai"],
        "ANTHROPIC_API_KEY": external_api_keys["anthropic"],
        "GOOGLE_API_KEY": external_api_keys["gemini"],
        "OPENROUTER_API_KEY": external_api_keys["openrouter"],
        "LILYPAD_PROJECT_ID": str(project_uuid),
        "LILYPAD_API_KEY": api_keys[0].key_hash,
        "PATH": os.environ["PATH"],
        "LILYPAD_REMOTE_API_URL": settings.remote_api_url,
        "LILYPAD_BASE_URL": f"{settings.remote_api_url}/v0",
    }
    try:
        processed_code = _run_playground(wrapper_code, env_vars)
    except Exception as e:
        logger.exception("Failed to run playground: %s", e)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid API Key"
        )

    return processed_code


def _validate_template_string(template: str | None) -> bool:
    """Validate a template string for potential injection patterns.

    Args:
        template: The template string to validate

    Returns:
        True if safe, False otherwise
    """
    if not template:
        return True

    suspicious_patterns = [
        r"{.*?__.*?}",  # Dunder methods
        r'{.*?["\']\s*:\s*["\'].*?}',  # Dict with string keys like format string attacks
        r"{.*?\\.*?}",  # Escape sequences
        r"{.*?#.*?}",  # Comments
        r"{.*?eval\(.*?}",  # Eval attempts
        r"{.*?exec\(.*?}",  # Exec attempts
        r"{.*?import\s+.*?}",  # Import attempts
        r"{.*?open\(.*?}",  # File operations
        r"{.*?system\(.*?}",  # System command execution
    ]

    for pattern in suspicious_patterns:
        if re.search(pattern, template):
            logger.warning(f"Suspicious pattern in template: {pattern}")
            return False

    if template.count("{") != template.count("}"):
        logger.warning("Unbalanced braces in template")
        return False

    placeholders = re.findall(r"{([^{}]+)}", template)
    for placeholder in placeholders:
        if not re.fullmatch(r"[a-zA-Z_][a-zA-Z0-9_]*", placeholder.strip()):
            logger.warning("Invalid placeholder in template: %s", placeholder)
            return False

    return True


def _run_playground(code: str, env_vars: dict[str, str]) -> str:
    """Run code in playground with enhanced security.

    Args:
        code: The Python code to execute
        env_vars: Dictionary of environment variables to pass to the subprocess

    Returns:
        The result of code execution
    """
    modified_code = code + "\n\nprint('__RESULT__', response, '__RESULT__')"
    modified_code = run_ruff(dedent(modified_code)).strip()
    sanitized_env = _validate_api_keys(env_vars)
    settings = get_settings()
    python_executable = Path(settings.playground_venv_path, "bin/python")
    if not python_executable.exists():
        logger.error("Python executable not found")
        logger.error("Please setup the playground environment")
        logger.error(
            f"$ uv venv --no-project {str(settings.playground_venv_path)} &&"
            f" VIRTUAL_ENV={str(settings.playground_venv_path)} uv pip sync playground-requirements.lock"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Python executable not found",
        )
    logger.error(f"modified_code: {modified_code}")
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "playground.py"
        tmp_path.write_text(modified_code)
        try:
            result = subprocess.run(
                [str(python_executable.absolute()), str(tmp_path)],
                check=False,
                capture_output=True,
                text=True,
                env=sanitized_env,
                cwd=tmpdir,
                timeout=60,
                preexec_fn=_limit_resources,
            )
        except subprocess.TimeoutExpired:
            logger.error("Subprocess execution timed out.")
            return "Execution timed out"
        except Exception:
            logger.exception("Subprocess execution failed")
            return "Internal execution error"

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
        arg_types_and_values: Dictionary mapping argument names to their types and values

    Returns:
        Dictionary mapping argument names to their decoded values
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
