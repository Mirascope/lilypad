"""Prompts table and models."""

from enum import Enum
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel
from sqlalchemy import JSON, Column
from sqlmodel import Field, Relationship

from .base_sql_model import BaseSQLModel
from .table_names import PROJECT_TABLE_NAME, PROMPT_TABLE_NAME

if TYPE_CHECKING:
    from .projects import ProjectTable
    from .versions import VersionTable


class Provider(str, Enum):
    """Provider name enum"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"


class ResponseFormat(BaseModel):
    """Response format model."""

    type: Literal["text", "json_object", "json_schema"]


class GeminiCallParams(BaseModel):
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


class OpenAICallParams(BaseModel):
    """OpenAI call args model.

    https://platform.openai.com/docs/api-reference/chat/create
    """

    max_tokens: int
    temperature: float
    top_p: float
    frequency_penalty: float | None = None
    presence_penalty: float | None = None
    response_format: ResponseFormat
    stop: str | list[str] | None = None


class AnthropicCallParams(BaseModel):
    """Anthropic call args model."""

    max_tokens: int
    temperature: float
    stop_sequences: list[str] | None = None
    top_k: int | None = None
    top_p: float | None = None


class _PromptBase(BaseSQLModel):
    """Base Prompt Model."""

    project_id: int | None = Field(default=None, foreign_key=f"{PROJECT_TABLE_NAME}.id")
    hash: str | None = Field(default=None, index=True)
    template: str
    provider: Provider
    model: str


class PromptPublic(_PromptBase):
    """Prompt public model."""

    id: int
    call_params: OpenAICallParams | AnthropicCallParams | GeminiCallParams | None = None


class PromptCreate(_PromptBase):
    """Prompt create model."""

    call_params: OpenAICallParams | AnthropicCallParams | GeminiCallParams | None = None


class PromptTable(_PromptBase, table=True):
    """Prompt table."""

    __tablename__ = PROMPT_TABLE_NAME  # type: ignore

    id: int | None = Field(default=None, primary_key=True)
    organization_id: str | None = Field(default=None, index=True)
    call_params: dict | None = Field(sa_column=Column(JSON), default_factory=dict)
    project: "ProjectTable" = Relationship(back_populates="prompts")
    version: "VersionTable" = Relationship(back_populates="prompt", cascade_delete=True)
