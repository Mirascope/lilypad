"""Provider call params models"""

from typing import Any, Literal

from pydantic import BaseModel

from lilypad.server.models import FnParamsBase, Provider


class ResponseFormat(BaseModel):
    """Response format model."""

    type: Literal["text", "json_object", "json_schema"]


class GeminiCallArgsCreate(BaseModel):
    """Gemini GenerationConfig call args model.
    https://ai.google.dev/api/generate-content#v1beta.GenerationConfig
    """

    response_mime_type: str
    max_output_tokens: int | None = None  # Depends on model
    temperature: float | None = None  # Depends on model
    top_k: int | None = None
    top_p: float | None = None
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    response_schema: dict[str, Any] | None = None
    stop_sequences: list[str] | None = None


class OpenAICallArgsCreate(BaseModel):
    """OpenAI call args model."""

    max_tokens: int
    temperature: float
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    response_format: ResponseFormat
    stop: str | list[str] | None = None


class AnthropicCallArgsCreate(BaseModel):
    """Anthropic call args model."""

    max_tokens: int
    temperature: float
    stop_sequences: list[str] | None = None
    top_k: int | None = None
    top_p: float | None = None


class CallArgsPublic(BaseModel):
    """Call args public model."""

    id: int | None
    model: str
    provider: Provider
    prompt_template: str | None = None
    hash: str | None = None
    call_params: (
        OpenAICallArgsCreate | AnthropicCallArgsCreate | GeminiCallArgsCreate | None
    ) = None


class CallArgsCreate(BaseModel):
    """Call args create model."""

    model: str
    provider: Provider
    prompt_template: str
    call_params: (
        OpenAICallArgsCreate | AnthropicCallArgsCreate | GeminiCallArgsCreate | None
    ) = None


class FnParamsPublic(FnParamsBase):
    """Fn params public model"""

    id: int
    llm_function_id: int
    call_params: (
        OpenAICallArgsCreate | AnthropicCallArgsCreate | GeminiCallArgsCreate | None
    ) = None
