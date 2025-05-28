"""Functions schemas."""

from enum import Enum
from typing import Annotated, Any, TypeVar, overload
from uuid import UUID

from mirascope.core.base import CommonCallParams
from pydantic import BaseModel, Field, TypeAdapter, field_validator

from ..models.functions import _FunctionBase


class Provider(str, Enum):
    """Provider name enum"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"


class FunctionCreate(_FunctionBase):
    """Function create model."""


class FunctionPublic(_FunctionBase):
    """Function public model."""

    uuid: UUID


# Security constraints
MAX_NESTING_DEPTH = 100
MAX_LIST_LENGTH = 1000
MAX_DICT_KEYS = 100
MAX_STRING_LENGTH = 32768  # 32KB

_T = TypeVar("_T")
AcceptedValue = int | float | bool | str | list | dict[str, Any]

accepted_value_adapter = TypeAdapter(AcceptedValue)


@overload
def _validate_object(
    values: dict[str, AcceptedValue], depth: int = 0
) -> dict[str, AcceptedValue]: ...


@overload
def _validate_object(
    values: list[AcceptedValue], depth: int = 0
) -> list[AcceptedValue]: ...


@overload
def _validate_object(values: _T, depth: int = 0) -> _T: ...


def _validate_object(values: Any, depth: int = 0) -> Any:
    """Recursively validate nested structures with depth and size limits."""
    # Check recursion depth
    if depth > MAX_NESTING_DEPTH:
        raise ValueError(f"Maximum nesting depth exceeded ({MAX_NESTING_DEPTH})")

    if isinstance(values, list):
        # Check list length
        if len(values) > MAX_LIST_LENGTH:
            raise ValueError(f"List exceeds maximum length ({MAX_LIST_LENGTH})")
        return [_validate_object(value, depth + 1) for value in values]

    elif isinstance(values, dict):
        # Check dictionary size
        if len(values) > MAX_DICT_KEYS:
            raise ValueError(f"Dictionary exceeds maximum keys ({MAX_DICT_KEYS})")

        # Validate each key and value
        result = {}
        for key, value in values.items():
            # Validate key is string and not too long
            if not isinstance(key, str):
                raise ValueError(f"Dictionary keys must be strings, got {type(key)}")

            if len(key) > MAX_STRING_LENGTH:
                raise ValueError(
                    f"Dictionary key too long: {len(key)} chars (max: {MAX_STRING_LENGTH})"
                )

            # Recursively validate value
            result[key] = _validate_object(value, depth + 1)
        return result

    elif isinstance(values, str):
        # Check string length
        if len(values) > MAX_STRING_LENGTH:
            raise ValueError(
                f"String too long: {len(values)} chars (max: {MAX_STRING_LENGTH})"
            )

    # Use the adapter for final validation
    return accepted_value_adapter.validate_python(values, strict=True)


class PlaygroundParameters(BaseModel):
    """Playground parameters model."""

    arg_values: dict[str, AcceptedValue]
    arg_types: dict[str, str] | None
    provider: Provider
    model: str
    prompt_template: str
    call_params: CommonCallParams | None

    @field_validator("arg_values", "call_params")
    def check_nested_values(
        cls, values: dict[str, AcceptedValue]
    ) -> dict[str, AcceptedValue]:
        """arg_values is a dictionary of key-value pairs where the value can be"""
        return _validate_object(values)


class PlaygroundErrorType(str, Enum):
    """Categorizes the types of errors that can occur during playground execution."""

    TIMEOUT = "TimeoutError"
    CONFIGURATION = "ConfigurationError"
    SUBPROCESS = "SubprocessError"
    OUTPUT_PARSING = "OutputParsingError"
    OUTPUT_MARKER = "OutputMarkerError"
    INTERNAL = "InternalPlaygroundError"
    EXECUTION_ERROR = "ExecutionError"  # Error within user code
    BAD_REQUEST = "BadRequestError"  # General validation errors before execution
    NOT_FOUND = "NotFoundError"  # Resource not found
    INVALID_INPUT = "InvalidInputError"  # Specific input format/value errors
    API_KEY_ISSUE = "ApiKeyIssue"  # Error related to API key retrieval/validation
    UNEXPECTED = "UnexpectedServerError"  # Catch-all for server issues


class PlaygroundErrorDetail(BaseModel):
    """Detailed information about a playground error."""

    type: PlaygroundErrorType | str = Field(
        ...,
        description="Category of the error (Enum value) or specific Python Exception type name.",
    )
    reason: str = Field(..., description="User-friendly description of the error.")
    details: Annotated[
        str | None,
        Field(None, description="Additional technical details, if available."),
    ] = None


class PlaygroundErrorResponse(BaseModel):
    """Standard structure for playground error responses."""

    error: PlaygroundErrorDetail


class TraceContextModel(BaseModel):
    """Represents the tracing context information provided by Lilypad."""

    span_uuid: str | None = Field(
        None, description="The unique identifier for the current span within the trace."
    )


class PlaygroundSuccessResponse(BaseModel):
    """Standard structure for successful playground execution responses."""

    result: Any = Field(
        ...,
        description="The result returned by the executed function. Can be any JSON-serializable type.",
    )
    trace_context: TraceContextModel | None = Field(
        None, description="Tracing context associated with the execution."
    )
