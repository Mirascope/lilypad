"""Provider call params models"""

from typing import Annotated, Any, Literal

from pydantic import AfterValidator, BaseModel, BeforeValidator

from lilypad.server.models import FnParamsBase, Provider


class ResponseFormat(BaseModel):
    """Response format model."""

    type: Literal["text", "json_object", "json_schema"]


class OpenAICallArgsCreate(BaseModel):
    """OpenAI call args model."""

    max_tokens: int
    temperature: float
    top_p: float
    frequency_penalty: float
    presence_penalty: float
    response_format: ResponseFormat
    stop: str | list[str] | None = None


class CallArgsPublic(BaseModel):
    """Call args public model."""

    id: int | None
    model: str
    provider: Provider
    prompt_template: str | None = None
    hash: str | None = None
    call_params: OpenAICallArgsCreate | None = None


class CallArgsCreate(BaseModel):
    """Call args create model."""

    model: str
    provider: Provider
    prompt_template: str
    call_params: OpenAICallArgsCreate | None = None


class FnParamsPublic(FnParamsBase):
    """Fn params public model"""

    id: int
    call_params: OpenAICallArgsCreate | None = None
