"""The Schema models for the Lilypad v0 API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CommonCallParams(BaseModel):
    """Common parameters shared across LLM providers.

    Note: Each provider may handle these parameters differently or not support them at all.
    Please check provider-specific documentation for parameter support and behavior.

    Attributes:
        temperature: Controls randomness in the output (0.0 to 1.0).
        max_tokens: Maximum number of tokens to generate.
        top_p: Nucleus sampling parameter (0.0 to 1.0).
        frequency_penalty: Penalizes frequent tokens (-2.0 to 2.0).
        presence_penalty: Penalizes tokens based on presence (-2.0 to 2.0).
        seed: Random seed for reproducibility.
        stop: Stop sequence(s) to end generation.
    """

    temperature: float | None = Field(None, title="Temperature")
    max_tokens: int | None = Field(None, title="Max Tokens")
    top_p: float | None = Field(None, title="Top P")
    frequency_penalty: float | None = Field(None, title="Frequency Penalty")
    presence_penalty: float | None = Field(None, title="Presence Penalty")
    seed: int | None = Field(None, title="Seed")
    stop: str | list[str] | None = Field(None, title="Stop")


class DependencyInfo(BaseModel):
    version: str = Field(..., title="Version")
    extras: list[str] | None = Field(..., title="Extras")


class EvaluationType(str, Enum):
    """Evaluation type enum"""

    MANUAL = "manual"
    VERIFIED = "verified"
    EDITED = "edited"


class GenerationPublic(BaseModel):
    """Generation public model."""

    project_uuid: UUID | None = Field(None, title="Project Uuid")
    version_num: int | None = Field(None, title="Version Num")
    name: str = Field(..., min_length=1, title="Name")
    signature: str = Field(..., title="Signature")
    code: str = Field(..., title="Code")
    hash: str = Field(..., title="Hash")
    dependencies: dict[str, DependencyInfo] | None = Field(None, title="Dependencies")
    arg_types: dict[str, str] | None = Field(None, title="Arg Types")
    archived: datetime | None = Field(None, title="Archived")
    custom_id: str | None = Field(None, title="Custom Id")
    prompt_template: str | None = Field(None, title="Prompt Template")
    provider: str | None = Field(None, title="Provider")
    model: str | None = Field(None, title="Model")
    call_params: CommonCallParams | None = None
    is_default: bool | None = Field(False, title="Is Default")
    is_managed: bool | None = Field(False, title="Is Managed")
    uuid: UUID = Field(..., title="Uuid")


class Label(str, Enum):
    """Label enum"""

    PASS_ = "pass"
    FAIL = "fail"


class OrganizationPublic(BaseModel):
    """Organization public model"""

    name: str = Field(..., min_length=1, title="Name")
    uuid: UUID = Field(..., title="Uuid")


class ProjectPublic(BaseModel):
    """Project Public Model."""

    name: str = Field(..., title="Name")
    uuid: UUID = Field(..., title="Uuid")
    generations: list[GenerationPublic] | None = Field([], title="Generations")
    created_at: datetime = Field(..., title="Created At")


class Scope(str, Enum):
    """Instrumentation Scope name of the span"""

    LILYPAD = "lilypad"
    LLM = "llm"


class SpanType(str, Enum):
    """Span type"""

    GENERATION = "generation"
    TRACE = "trace"


class AnnotationTable(BaseModel):
    """Annotation table."""

    uuid: UUID | None = Field(None, title="Uuid")
    created_at: datetime | None = Field(None, title="Created At")
    organization_uuid: UUID = Field(..., title="Organization Uuid")
    label: Label | None = None
    reasoning: str | None = Field(None, title="Reasoning")
    type: EvaluationType | None = EvaluationType.MANUAL
    data: dict[str, Any] | None = Field(None, title="Data")
    assigned_to: UUID | None = Field(None, title="Assigned To")
    project_uuid: UUID | None = Field(None, title="Project Uuid")
    span_uuid: UUID | None = Field(None, title="Span Uuid")
    generation_uuid: UUID | None = Field(None, title="Generation Uuid")


class SpanPublic(BaseModel):
    """Span public model"""

    span_id: str = Field(..., title="Span Id")
    generation_uuid: UUID | None = Field(None, title="Generation Uuid")
    type: SpanType | None = None
    cost: float | None = Field(None, title="Cost")
    scope: Scope
    input_tokens: float | None = Field(None, title="Input Tokens")
    output_tokens: float | None = Field(None, title="Output Tokens")
    duration_ms: float | None = Field(None, title="Duration Ms")
    data: dict[str, Any] | None = Field(None, title="Data")
    parent_span_id: str | None = Field(None, title="Parent Span Id")
    uuid: UUID = Field(..., title="Uuid")
    project_uuid: UUID = Field(..., title="Project Uuid")
    display_name: str | None = Field(None, title="Display Name")
    generation: GenerationPublic | None = None
    annotations: list[AnnotationTable] = Field(..., title="Annotations")
    child_spans: list[SpanPublic] = Field(..., title="Child Spans")
    created_at: datetime = Field(..., title="Created At")
    version: int | None = Field(None, title="Version")
    status: str | None = Field(None, title="Status")


SpanPublic.model_rebuild()
