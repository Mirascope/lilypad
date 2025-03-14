"""The Schema models for the Lilypad v0 API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Annotated, Any
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

    temperature: Annotated[float | None, Field(title="Temperature")] = None
    max_tokens: Annotated[int | None, Field(title="Max Tokens")] = None
    top_p: Annotated[float | None, Field(title="Top P")] = None
    frequency_penalty: Annotated[float | None, Field(title="Frequency Penalty")] = None
    presence_penalty: Annotated[float | None, Field(title="Presence Penalty")] = None
    seed: Annotated[int | None, Field(title="Seed")] = None
    stop: Annotated[str | list[str] | None, Field(title="Stop")] = None


class DependencyInfo(BaseModel):
    version: Annotated[str, Field(title="Version")]
    extras: Annotated[list[str] | None, Field(title="Extras")] = None


class EvaluationType(str, Enum):
    """Evaluation type enum"""

    MANUAL = "manual"
    VERIFIED = "verified"
    EDITED = "edited"


class GenerationCreate(BaseModel):
    """Generation create model."""

    project_uuid: Annotated[UUID | None, Field(title="Project Uuid")] = None
    version_num: Annotated[int | None, Field(title="Version Num")] = None
    name: Annotated[str, Field(min_length=1, title="Name")]
    signature: Annotated[str, Field(title="Signature")]
    code: Annotated[str, Field(title="Code")]
    hash: Annotated[str, Field(title="Hash")]
    dependencies: Annotated[
        dict[str, DependencyInfo] | None, Field(title="Dependencies")
    ] = None
    arg_types: Annotated[dict[str, str] | None, Field(title="Arg Types")] = None
    arg_values: Annotated[dict[str, Any] | None, Field(title="Arg Values")] = None
    archived: Annotated[datetime | None, Field(title="Archived")] = None
    custom_id: Annotated[str | None, Field(title="Custom Id")] = None
    prompt_template: Annotated[str | None, Field(title="Prompt Template")] = None
    provider: Annotated[str | None, Field(title="Provider")] = None
    model: Annotated[str | None, Field(title="Model")] = None
    call_params: CommonCallParams | None = None
    is_default: Annotated[bool | None, Field(title="Is Default")] = False
    is_managed: Annotated[bool | None, Field(title="Is Managed")] = False


class GenerationPublic(BaseModel):
    """Generation public model."""

    project_uuid: Annotated[UUID | None, Field(title="Project Uuid")] = None
    version_num: Annotated[int | None, Field(title="Version Num")] = None
    name: Annotated[str, Field(min_length=1, title="Name")]
    signature: Annotated[str, Field(title="Signature")]
    code: Annotated[str, Field(title="Code")]
    hash: Annotated[str, Field(title="Hash")]
    dependencies: Annotated[
        dict[str, DependencyInfo] | None, Field(title="Dependencies")
    ] = None
    arg_types: Annotated[dict[str, str] | None, Field(title="Arg Types")] = None
    arg_values: Annotated[dict[str, Any] | None, Field(title="Arg Values")] = None
    archived: Annotated[datetime | None, Field(title="Archived")] = None
    custom_id: Annotated[str | None, Field(title="Custom Id")] = None
    prompt_template: Annotated[str | None, Field(title="Prompt Template")] = None
    provider: Annotated[str | None, Field(title="Provider")] = None
    model: Annotated[str | None, Field(title="Model")] = None
    call_params: CommonCallParams | None = None
    is_default: Annotated[bool | None, Field(title="Is Default")] = False
    is_managed: Annotated[bool | None, Field(title="Is Managed")] = False
    uuid: Annotated[UUID, Field(title="Uuid")]


class Label(str, Enum):
    """Label enum"""

    PASS_ = "pass"
    FAIL = "fail"


class OrganizationPublic(BaseModel):
    """Organization public model"""

    name: Annotated[str, Field(min_length=1, title="Name")]
    uuid: Annotated[UUID, Field(title="Uuid")]


class ProjectPublic(BaseModel):
    """Project Public Model."""

    name: Annotated[str, Field(title="Name")]
    uuid: Annotated[UUID, Field(title="Uuid")]
    generations: Annotated[
        list[GenerationPublic] | None, Field(title="Generations")
    ] = []
    created_at: Annotated[datetime, Field(title="Created At")]


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

    uuid: Annotated[UUID | None, Field(title="Uuid")] = None
    created_at: Annotated[datetime | None, Field(title="Created At")] = None
    organization_uuid: Annotated[UUID, Field(title="Organization Uuid")]
    label: Label | None = None
    reasoning: Annotated[str | None, Field(title="Reasoning")] = None
    type: EvaluationType | None = EvaluationType.MANUAL
    data: Annotated[dict[str, Any] | None, Field(title="Data")] = None
    assigned_to: Annotated[UUID | None, Field(title="Assigned To")] = None
    project_uuid: Annotated[UUID | None, Field(title="Project Uuid")] = None
    span_uuid: Annotated[UUID | None, Field(title="Span Uuid")] = None
    generation_uuid: Annotated[UUID | None, Field(title="Generation Uuid")] = None


class SpanPublic(BaseModel):
    """Span public model"""

    span_id: Annotated[str, Field(title="Span Id")]
    generation_uuid: Annotated[UUID | None, Field(title="Generation Uuid")] = None
    type: SpanType | None = None
    cost: Annotated[float | None, Field(title="Cost")] = None
    scope: Scope
    input_tokens: Annotated[float | None, Field(title="Input Tokens")] = None
    output_tokens: Annotated[float | None, Field(title="Output Tokens")] = None
    duration_ms: Annotated[float | None, Field(title="Duration Ms")] = None
    data: Annotated[dict[str, Any] | None, Field(title="Data")] = None
    parent_span_id: Annotated[str | None, Field(title="Parent Span Id")] = None
    uuid: Annotated[UUID, Field(title="Uuid")]
    project_uuid: Annotated[UUID, Field(title="Project Uuid")]
    display_name: Annotated[str | None, Field(title="Display Name")] = None
    generation: GenerationPublic | None = None
    annotations: Annotated[list[AnnotationTable], Field(title="Annotations")]
    child_spans: Annotated[list[SpanPublic], Field(title="Child Spans")]
    created_at: Annotated[datetime, Field(title="Created At")]
    version: Annotated[int | None, Field(title="Version")] = None
    status: Annotated[str | None, Field(title="Status")] = None


SpanPublic.model_rebuild()
