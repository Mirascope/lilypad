"""Generations schemas."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class Provider(str, Enum):
    """Provider name enum"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"


class GenerationCreate(BaseModel):
    """Generation create model."""

    project_uuid: UUID | None = None
    prompt_uuid: UUID | None = None
    response_model_uuid: UUID | None = None
    version_num: int | None = None
    name: str
    signature: str
    code: str
    hash: str
    dependencies: dict[str, Any] = Field(default_factory=dict)
    arg_types: dict[str, str] = Field(default_factory=dict)
    archived: datetime | None = None
    custom_id: str | None = None
    prompt_template: str | None = None
    provider: str | None = None
    model: str | None = None
    call_params: dict[str, Any] = Field(default_factory=dict)
    is_default: bool | None = False
    is_managed: bool | None = False


class GenerationPublic(BaseModel):
    """Generation public model."""

    uuid: UUID
    project_uuid: UUID | None = None
    prompt_uuid: UUID | None = None
    response_model_uuid: UUID | None = None
    version_num: int | None = None
    name: str
    signature: str
    code: str
    hash: str
    dependencies: dict[str, Any] = Field(default_factory=dict)
    arg_types: dict[str, str] = Field(default_factory=dict)
    archived: datetime | None = None
    custom_id: str | None = None
    prompt_template: str | None = None
    provider: str | None = None
    model: str | None = None
    call_params: dict[str, Any] = Field(default_factory=dict)
    is_default: bool | None = False
    is_managed: bool | None = False


class PlaygroundParameters(BaseModel):
    """Playground parameters model."""

    arg_values: dict[str, Any]
    provider: Provider
    model: str
    generation: GenerationCreate | None = None
