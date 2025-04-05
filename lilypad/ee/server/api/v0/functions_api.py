"""The EE `/functions` API router."""

import base64
import binascii
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
from .....server.schemas.functions import (
    AcceptedValue,
    PlaygroundErrorDetail,
    PlaygroundErrorResponse,
    PlaygroundErrorType,
    PlaygroundParameters,
    PlaygroundSuccessResponse,
)
from .....server.services import APIKeyService, FunctionService, SpanService
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
_JSON_START_MARKER = "__JSON_START__"
_JSON_END_MARKER = "__JSON_END__"


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
                logger.error(f"Invalid API key: {value}")
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


def _validate_provider_api_key(
    provider: str, external_api_keys: dict[str, str]
) -> bool:
    """Check if the required API key for the specified provider is available.

    Args:
        provider: The provider name (e.g., 'openai', 'anthropic')
        external_api_keys: Dictionary of available API keys

    Returns:
        True if the required API key is available, False otherwise
    """
    provider_to_key_map = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY",
        "gemini": "GOOGLE_API_KEY",
        "openrouter": "OPENROUTER_API_KEY",
    }

    required_key = provider_to_key_map.get(provider.lower())
    if not required_key:
        logger.warning(f"Unknown provider: {provider}")
        return False

    return required_key in external_api_keys and bool(external_api_keys[required_key])


@functions_router.post(
    "/projects/{project_uuid}/functions/{function_uuid}/playground",
    response_model=PlaygroundSuccessResponse,  # Use imported model
    summary="Run Function in Playground",
    description="Executes a function with specified parameters in a secure playground environment.",
    responses={
        status.HTTP_200_OK: {
            "description": "Function executed successfully.",
            "model": PlaygroundSuccessResponse,
        },
        status.HTTP_400_BAD_REQUEST: {
            "description": "Bad Request",
            "model": PlaygroundErrorResponse,
        },
        status.HTTP_404_NOT_FOUND: {
            "description": "Function not found",
            "model": PlaygroundErrorResponse,
        },
        status.HTTP_408_REQUEST_TIMEOUT: {
            "description": "Request Timeout",
            "model": PlaygroundErrorResponse,
        },
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "description": "Internal Server Error",
            "model": PlaygroundErrorResponse,
        },
    },
)
def run_playground(
    project_uuid: UUID,
    function_uuid: UUID,
    playground_parameters: PlaygroundParameters,
    function_service: Annotated[FunctionService, Depends(FunctionService)],
    api_key_service: Annotated[APIKeyService, Depends(APIKeyService)],
    user_external_api_key_service: Annotated[
        UserExternalAPIKeyService, Depends(UserExternalAPIKeyService)
    ],
    span_service: Annotated[SpanService, Depends(SpanService)],
) -> PlaygroundSuccessResponse:
    """Run playground version of a function with enhanced security.

    Args:
        project_uuid: UUID of the project
        function_uuid: UUID of the function
        playground_parameters: Parameters for the playground execution
        function_service: Service for function management
        api_key_service: Service for API key management
        user_external_api_key_service: Service for external API key management
        span_service: Service for span management

    Returns:
        Result of the function execution
    """
    try:
        function = function_service.find_record_by_uuid(function_uuid)
        if not function:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": PlaygroundErrorDetail(  # Use imported model
                        type=PlaygroundErrorType.NOT_FOUND,
                        reason="Function not found.",
                        details=f"Function with UUID {function_uuid} does not exist.",
                    ).model_dump()
                },
            )
        if not _validate_function_data(function):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": PlaygroundErrorDetail(  # Use imported model
                        type=PlaygroundErrorType.BAD_REQUEST,
                        reason="Function data validation failed.",
                        details="The function's stored configuration contains potentially unsafe data.",
                    ).model_dump()
                },
            )

        # Get API keys for the project
        api_keys = api_key_service.find_keys_by_user_and_project(project_uuid)
        if len(api_keys) == 0:
            logger.warning(
                f"No project-specific API keys found for project {project_uuid}. Relying on user's external keys."
            )

        # Extract required values from playground_parameters
        provider = playground_parameters.provider.value
        model = playground_parameters.model

        # Validate provider and model values
        if not _validate_template_values(provider, model):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": PlaygroundErrorDetail(  # Use imported model
                        type=PlaygroundErrorType.INVALID_INPUT,
                        reason="Invalid provider or model name format.",
                    ).model_dump()
                },
            )

        arg_types = (
            playground_parameters.arg_types
            if playground_parameters.arg_types is not None
            else function.arg_types
        ) or {}

        arg_definitions = []
        for arg_name in arg_types:
            if arg_name == "trace_ctx":
                continue
            if not _validate_python_identifier(arg_name):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error": PlaygroundErrorDetail(  # Use imported model
                            type=PlaygroundErrorType.INVALID_INPUT,
                            reason=f"Invalid argument name: {arg_name}.",
                            details="Argument names must be valid Python identifiers.",
                        ).model_dump()
                    },
                )
            arg_definitions.append(f"{arg_name}")

        arguments_str = ", " + ", ".join(arg_definitions) if arg_definitions else ""

        try:
            safe_arg_types_and_values = sanitize_arg_types_and_values(
                arg_types, playground_parameters.arg_values or {}
            )
            decoded_arg_values = _decode_bytes(safe_arg_types_and_values)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": PlaygroundErrorDetail(  # Use imported model
                        type=PlaygroundErrorType.INVALID_INPUT,
                        reason="Invalid argument value encoding.",
                        details=str(e),
                    ).model_dump()
                },
            )

        json_arg_values = json.dumps(decoded_arg_values)
        user_args_preparation_code = (
            f"arg_values = json.loads({json.dumps(json_arg_values)})"
        )
        function_definition_code = f"""
import json
import os
import sys

import lilypad
from mirascope import llm, prompt_template


lilypad.configure(auto_llm=True)

@lilypad.trace(versioning="automatic", mode="wrap")
@llm.call(provider={json.dumps(provider)}, model={json.dumps(model)}, call_params={
            json.dumps(
                (
                    playground_parameters.call_params
                    if playground_parameters.call_params is not None
                    else function.call_params
                )
                or {}
            )
        })
@prompt_template({
            json.dumps(
                (
                    playground_parameters.prompt_template
                    if playground_parameters.prompt_template is not None
                    else function.prompt_template
                )
                or ""
            )
        })
def {function.name}(trace_ctx{arguments_str}) -> None:
    trace_ctx.metadata({{"scope": "playground"}})

"""
        full_wrapper_code = dedent(f"""
{dedent(function_definition_code)}

{dedent(user_args_preparation_code)}

output_data = None
try:
    response = {function.name}(**arg_values)

    output_data = {{
        "result": response.response.content,
        "span_id": response.formated_span_id
    }}
except Exception as e:
    import traceback
    error_reason = str(e)
    print("--- Playground Execution Traceback ---", file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    print("------------------------------------", file=sys.stderr)
    output_data = {{
        "error": {{
            # Use specific Python error type name directly as string
            "type": type(e).__name__,
            "reason": error_reason,
            "details": "Error during playground function execution."
        }}
    }}
finally:
    _JSON_START_MARKER = "{_JSON_START_MARKER}"
    _JSON_END_MARKER = "{_JSON_END_MARKER}"

    if output_data is None:
         output_data = {{ "error": {{ "type": "InternalPlaygroundError", "reason": "Failed to produce result or capture error.", "details": "" }} }}
    try:
        json_output = json.dumps(output_data)
        print(f"{{_JSON_START_MARKER}}{{json_output}}{{_JSON_END_MARKER}}")
    except Exception as dump_error:
        fallback_error_data = {{
            "error": {{
                 "type": type(dump_error).__name__, # Type of the dumping error
                 "reason": "Failed to serialize final playground output to JSON.",
                 "details": str(dump_error)
            }}
        }}
        print(f"{{_JSON_START_MARKER}}{{json.dumps(fallback_error_data)}}{{_JSON_END_MARKER}}")
""")

        try:
            formatted_wrapper_code = run_ruff(full_wrapper_code)
        except Exception as format_error:
            logger.warning(
                f"Ruff formatting failed: {format_error}. Proceeding with unformatted code."
            )
            formatted_wrapper_code = full_wrapper_code

        external_api_keys = {}
        try:
            key_names = user_external_api_key_service.list_api_keys().keys()
            for name in ["openai", "anthropic", "gemini", "openrouter"]:
                api_key_val = (
                    user_external_api_key_service.get_api_key(name)
                    if name in key_names
                    else None
                )
                if api_key_val:
                    external_api_keys[name.upper() + "_API_KEY"] = api_key_val
        except Exception as key_error:
            logger.error(f"Failed to retrieve external API keys: {key_error}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": PlaygroundErrorDetail(  # Use imported model
                        type=PlaygroundErrorType.API_KEY_ISSUE,
                        reason="Failed to retrieve external API keys.",
                    ).model_dump()
                },
            )
        # Validate that the required API key for the specified provider is available
        if not _validate_provider_api_key(provider, external_api_keys):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": PlaygroundErrorDetail(
                        type=PlaygroundErrorType.API_KEY_ISSUE,
                        reason=f"Missing API key for provider '{provider}'.",
                        details=f"Please add your {provider.upper()} API key in the settings before running this playground.",
                    ).model_dump()
                },
            )
        settings = get_settings()
        env_vars = {
            **external_api_keys,
            "LILYPAD_PROJECT_ID": str(project_uuid),
            "LILYPAD_API_KEY": api_keys[0].key_hash,
            "PATH": os.environ["PATH"],
            "LILYPAD_REMOTE_API_URL": settings.remote_api_url,
            "LILYPAD_BASE_URL": f"{settings.remote_api_url}/v0",
        }

        execution_result = _run_playground(formatted_wrapper_code, env_vars)

        if "error" not in execution_result:
            spand_id = execution_result.pop("span_id", None)
            if isinstance(spand_id, str) and (
                spand := span_service.get_record_by_span_id(project_uuid, spand_id)
            ):
                return PlaygroundSuccessResponse.model_validate(
                    {
                        "trace_context": {"span_uuid": str(spand.uuid)},
                        **execution_result,
                    }
                )

            logger.warning("Playground function did not return a span_id.")
            execution_result = {
                "error": PlaygroundErrorDetail(
                    type=PlaygroundErrorType.INTERNAL,
                    reason="Missing span_id in response.",
                    details="The function did not return a span_id.",
                ).model_dump()
            }

        try:
            error_detail_validated = PlaygroundErrorDetail(**execution_result["error"])
            error_type = error_detail_validated.type
        except Exception as validation_error:
            logger.error(
                f"Playground returned invalid error structure: {validation_error}\n{execution_result}"
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": PlaygroundErrorDetail(
                        type=PlaygroundErrorType.INTERNAL,
                        reason="Playground returned an invalid error structure.",
                    ).model_dump()
                },
            )

        status_code = status.HTTP_400_BAD_REQUEST
        if isinstance(error_type, PlaygroundErrorType):
            if error_type == PlaygroundErrorType.TIMEOUT:
                status_code = status.HTTP_408_REQUEST_TIMEOUT
            elif error_type in [
                PlaygroundErrorType.CONFIGURATION,
                PlaygroundErrorType.SUBPROCESS,
                PlaygroundErrorType.INTERNAL,
            ]:
                status_code = status.HTTP_500_INTERNAL_SERVER_ERROR

        raise HTTPException(
            status_code=status_code,
            detail=execution_result,  # Pass the original dict (now known to contain a valid error structure)
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(
            "Unexpected error occurred during playground request processing: %s", e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": PlaygroundErrorDetail(
                    type=PlaygroundErrorType.UNEXPECTED,
                    reason="An unexpected server error occurred.",
                ).model_dump()
            },
        )


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


def _run_playground(code: str, env_vars: dict[str, str]) -> dict[str, Any]:
    """Runs code in playground, returning structured dict for success or error."""
    sanitized_env = _validate_api_keys(env_vars)
    settings = get_settings()
    python_executable = Path(settings.playground_venv_path, "bin/python")
    timeout_seconds = 60

    if not python_executable.exists():
        logger.error(f"Playground Python executable not found: {python_executable}")
        return {
            "error": PlaygroundErrorDetail(
                type=PlaygroundErrorType.CONFIGURATION,
                reason="Playground Python executable not found.",
                details="Server environment setup issue.",
            ).model_dump()
        }

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir) / "playground.py"
        tmp_path.write_text(code)

        try:
            result = subprocess.run(
                [str(python_executable.absolute()), str(tmp_path)],
                check=False,
                capture_output=True,
                text=True,
                env=sanitized_env,
                cwd=tmpdir,
                timeout=timeout_seconds,
                preexec_fn=_limit_resources,
            )

            if result.returncode == 0:
                stdout_content = result.stdout
                start_index = stdout_content.find(_JSON_START_MARKER)
                end_index = stdout_content.rfind(_JSON_END_MARKER)

                if start_index != -1 and end_index != -1 and start_index < end_index:
                    json_payload = stdout_content[
                        start_index + len(_JSON_START_MARKER) : end_index
                    ]
                    try:
                        parsed_output = json.loads(json_payload)
                        if (
                            isinstance(parsed_output, dict)
                            and "error" in parsed_output
                            and isinstance(parsed_output["error"], dict)
                        ):
                            try:
                                # Validate and return the error structure
                                validated_error = PlaygroundErrorDetail(
                                    **parsed_output["error"]
                                )
                                return {"error": validated_error.model_dump()}
                            except Exception as validation_error:
                                logger.warning(
                                    f"Script returned error structure that failed validation: {validation_error}. Returning raw structure."
                                )
                                # Return the unvalidated structure but still wrapped in "error" key if possible
                                return {"error": parsed_output["error"]}

                        return parsed_output
                    except json.JSONDecodeError as json_err:
                        logger.error(
                            f"Failed to parse JSON between markers: {json_err}\nPayload: {json_payload[:500]}"
                        )
                        return {
                            "error": PlaygroundErrorDetail(
                                type=PlaygroundErrorType.OUTPUT_PARSING,
                                reason="Playground produced invalid JSON output between markers.",
                            ).model_dump()
                        }
                else:
                    logger.error(
                        f"Output markers not found in stdout.\nStdout: {stdout_content[:1000]}"
                    )
                    if result.stderr:
                        logger.error(
                            f"Stderr on return code 0:\n{result.stderr.strip()[:1000]}"
                        )
                    return {
                        "error": PlaygroundErrorDetail(  # Use imported model
                            type=PlaygroundErrorType.OUTPUT_MARKER,
                            reason="Playground did not produce expected output markers.",
                            details="Execution might have finished unexpectedly or stdout is malformed.",
                        ).model_dump()
                    }
            else:
                stderr_content = result.stderr.strip()
                logger.error(
                    f"Subprocess returned error (code {result.returncode}):\n{stderr_content}"
                )
                error_type_str = (
                    PlaygroundErrorType.EXECUTION_ERROR
                )  # Default Enum value
                error_reason = "Code execution failed inside the playground."
                last_line = stderr_content.splitlines()[-1] if stderr_content else ""
                match = re.search(r"^(?:[\w\.]+\.)*(\w*Error):\s*(.*)", last_line)
                if match:
                    error_reason = (
                        match.group(2).strip()
                        if match.group(2)
                        else f"Python {match.group(1)}"
                    )

                return {
                    "error": PlaygroundErrorDetail(  # Use imported model
                        type=error_type_str,
                        reason=error_reason,
                    ).model_dump()
                }

        except subprocess.TimeoutExpired:
            logger.error(
                f"Subprocess execution timed out after {timeout_seconds} seconds."
            )
            return {
                "error": PlaygroundErrorDetail(  # Use imported model
                    type=PlaygroundErrorType.TIMEOUT,
                    reason="Playground execution exceeded the time limit.",
                    details=f"Timeout was {timeout_seconds} seconds.",
                ).model_dump()
            }
        except FileNotFoundError:
            logger.error(
                f"Playground Python executable failed to run (FileNotFoundError): {python_executable}"
            )
            return {
                "error": PlaygroundErrorDetail(  # Use imported model
                    type=PlaygroundErrorType.CONFIGURATION,
                    reason="Failed to execute the playground Python interpreter.",
                    details="Check server environment setup and executable path.",
                ).model_dump()
            }
        except Exception:
            logger.exception("Subprocess execution failed unexpectedly.")
            return {
                "error": PlaygroundErrorDetail(  # Use imported model
                    type=PlaygroundErrorType.SUBPROCESS,
                    reason="An unexpected error occurred while managing the playground process.",
                ).model_dump()
            }


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
                except (
                    TypeError,
                    binascii.Error,
                ) as e:  # binascii.Error covers most b64decode issues
                    # Raise ValueError with specific argument name and chained exception
                    raise ValueError(
                        f"Invalid Base64 encoding for argument '{arg_name}': {str(e)}"
                    ) from e
            elif arg_value is None:
                result[arg_name] = None
            elif isinstance(arg_value, bytes):
                result[arg_name] = arg_value
            else:
                raise ValueError(
                    f"Expected base64 encoded string or None for bytes argument '{arg_name}', got {type(arg_value)}"
                )
        else:
            result[arg_name] = arg_value

    return result


__all__ = ["functions_router"]
