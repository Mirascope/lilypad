"""The Schema models for the Lilypad v0 API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


class APIKeyCreate(BaseModel):
    """API key create model"""

    name: str = Field(..., min_length=1, title="Name")
    expires_at: datetime | None = Field(None, title="Expires At")
    project_uuid: UUID = Field(..., title="Project Uuid")
    key_hash: str | None = Field(None, title="Key Hash")


class AggregateMetrics(BaseModel):
    """Aggregated metrics for spans"""

    total_cost: float = Field(..., title="Total Cost")
    total_input_tokens: float = Field(..., title="Total Input Tokens")
    total_output_tokens: float = Field(..., title="Total Output Tokens")
    average_duration_ms: float = Field(..., title="Average Duration Ms")
    span_count: int = Field(..., title="Span Count")
    start_date: datetime | None = Field(..., title="Start Date")
    end_date: datetime | None = Field(..., title="End Date")
    generation_uuid: UUID | None = Field(..., title="Generation Uuid")


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


class CreateUserOrganizationToken(BaseModel):
    token: str = Field(..., title="Token")


class DependencyInfo(BaseModel):
    version: str = Field(..., title="Version")
    extras: list[str] | None = Field(..., title="Extras")


class EvaluationType(str, Enum):
    """Evaluation type enum"""

    MANUAL = "manual"
    VERIFIED = "verified"
    EDITED = "edited"


class Event(BaseModel):
    """Event model."""

    name: str = Field(..., title="Name")
    type: str = Field(..., title="Type")
    message: str = Field(..., title="Message")
    timestamp: datetime = Field(..., title="Timestamp")


class GenerationCreate(BaseModel):
    """Generation create model."""

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


class GenerationUpdate(BaseModel):
    """Generation update model."""


class Label(str, Enum):
    """Label enum"""

    PASS_ = "pass"
    FAIL = "fail"


class OrganizationInviteCreate(BaseModel):
    """OrganizationInvite create model"""

    invited_by: UUID = Field(..., title="Invited By")
    email: str = Field(..., min_length=1, title="Email")
    expires_at: datetime | None = Field(None, title="Expires At")
    token: str | None = Field(None, title="Token")
    resend_email_id: str | None = Field(None, title="Resend Email Id")
    organization_uuid: UUID | None = Field(None, title="Organization Uuid")


class OrganizationPublic(BaseModel):
    """Organization public model"""

    name: str = Field(..., min_length=1, title="Name")
    uuid: UUID = Field(..., title="Uuid")


class OrganizationUpdate(BaseModel):
    """Organization update model"""

    name: str = Field(..., min_length=1, title="Name")


class ProjectCreate(BaseModel):
    """Project Create Model."""

    name: str = Field(..., title="Name")


class ProjectPublic(BaseModel):
    """Project Public Model."""

    name: str = Field(..., title="Name")
    uuid: UUID = Field(..., title="Uuid")
    generations: list[GenerationPublic] | None = Field([], title="Generations")
    created_at: datetime = Field(..., title="Created At")


class Provider(str, Enum):
    """Provider name enum"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"


class Scope(str, Enum):
    """Instrumentation Scope name of the span"""

    LILYPAD = "lilypad"
    LLM = "llm"


class SettingsPublic(BaseModel):
    remote_client_url: str = Field(..., title="Remote Client Url")
    remote_api_url: str = Field(..., title="Remote Api Url")
    github_client_id: str = Field(..., title="Github Client Id")
    google_client_id: str = Field(..., title="Google Client Id")
    environment: str = Field(..., title="Environment")
    experimental: bool = Field(..., title="Experimental")


class SpanType(str, Enum):
    """Span type"""

    GENERATION = "generation"
    TRACE = "trace"


class TimeFrame(str, Enum):
    """Timeframe for aggregation"""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    LIFETIME = "lifetime"


class UserRole(str, Enum):
    """User role enum."""

    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"


class ValidationError(BaseModel):
    loc: list[str | int] = Field(..., title="Location")
    msg: str = Field(..., title="Message")
    type: str = Field(..., title="Error Type")


class FieldAudioPart(BaseModel):
    """Image part model."""

    type: Literal["audio"] = Field(..., title="Type")
    media_type: str = Field(..., title="Media Type")
    audio: str = Field(..., title="Audio")


class FieldImagePart(BaseModel):
    """Image part model."""

    type: Literal["image"] = Field(..., title="Type")
    media_type: str = Field(..., title="Media Type")
    image: str = Field(..., title="Image")
    detail: str | None = Field(..., title="Detail")


class FieldTextPart(BaseModel):
    """Text part model."""

    type: Literal["text"] = Field(..., title="Type")
    text: str = Field(..., title="Text")


class FieldToolCall(BaseModel):
    """Image part model."""

    type: Literal["tool_call"] = Field(..., title="Type")
    name: str = Field(..., title="Name")
    arguments: dict[str, Any] = Field(..., title="Arguments")


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


class HTTPValidationError(BaseModel):
    detail: list[ValidationError] | None = Field(None, title="Detail")


class MessageParam(BaseModel):
    """Message param model agnostic to providers."""

    role: str = Field(..., title="Role")
    content: list[FieldAudioPart | FieldTextPart | FieldImagePart | FieldToolCall] = (
        Field(..., title="Content")
    )


class PlaygroundParameters(BaseModel):
    """Playground parameters model."""

    arg_values: dict[str, Any] = Field(..., title="Arg Values")
    provider: Provider
    model: str = Field(..., title="Model")
    generation: GenerationCreate | None = None


class SpanMoreDetails(BaseModel):
    """Span more details model."""

    uuid: UUID = Field(..., title="Uuid")
    project_uuid: UUID | None = Field(None, title="Project Uuid")
    generation_uuid: UUID | None = Field(None, title="Generation Uuid")
    display_name: str = Field(..., title="Display Name")
    provider: str = Field(..., title="Provider")
    model: str = Field(..., title="Model")
    input_tokens: float | None = Field(None, title="Input Tokens")
    output_tokens: float | None = Field(None, title="Output Tokens")
    duration_ms: float | None = Field(None, title="Duration Ms")
    signature: str | None = Field(None, title="Signature")
    code: str | None = Field(None, title="Code")
    arg_values: dict[str, Any] | None = Field(None, title="Arg Values")
    output: str | None = Field(None, title="Output")
    messages: list[MessageParam] = Field(..., title="Messages")
    data: dict[str, Any] = Field(..., title="Data")
    cost: float | None = Field(None, title="Cost")
    template: str | None = Field(None, title="Template")
    status: str | None = Field(None, title="Status")
    events: list[Event] | None = Field(None, title="Events")


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


class UserOrganizationPublic(BaseModel):
    """UserOrganization public model"""

    role: UserRole
    user_uuid: UUID = Field(..., title="User Uuid")
    uuid: UUID = Field(..., title="Uuid")
    organization_uuid: UUID = Field(..., title="Organization Uuid")
    organization: OrganizationPublic


class UserOrganizationTable(BaseModel):
    """UserOrganization table."""

    uuid: UUID | None = Field(None, title="Uuid")
    created_at: datetime | None = Field(None, title="Created At")
    organization_uuid: UUID = Field(..., title="Organization Uuid")
    role: UserRole
    user_uuid: UUID = Field(..., title="User Uuid")


class UserOrganizationUpdate(BaseModel):
    """UserOrganization update model"""

    role: UserRole


class UserPublic(BaseModel):
    """User public model"""

    first_name: str = Field(..., min_length=1, title="First Name")
    last_name: str | None = Field(None, title="Last Name")
    email: str = Field(..., min_length=1, title="Email")
    active_organization_uuid: UUID | None = Field(
        None, title="Active Organization Uuid"
    )
    keys: dict[str, str] | None = Field(None, title="Keys")
    uuid: UUID = Field(..., title="Uuid")
    access_token: str | None = Field(None, title="Access Token")
    user_organizations: list[UserOrganizationPublic] | None = Field(
        None, title="User Organizations"
    )


class APIKeyPublic(BaseModel):
    """API key public model"""

    name: str = Field(..., min_length=1, title="Name")
    expires_at: datetime | None = Field(None, title="Expires At")
    project_uuid: UUID = Field(..., title="Project Uuid")
    uuid: UUID = Field(..., title="Uuid")
    key_hash: str = Field(..., title="Key Hash")
    user: UserPublic
    project: ProjectPublic


class OrganizationInvitePublic(BaseModel):
    """OrganizationInvite public model"""

    invited_by: UUID = Field(..., title="Invited By")
    email: str = Field(..., min_length=1, title="Email")
    expires_at: datetime | None = Field(None, title="Expires At")
    uuid: UUID = Field(..., title="Uuid")
    organization_uuid: UUID = Field(..., title="Organization Uuid")
    user: UserPublic
    resend_email_id: str = Field(..., title="Resend Email Id")
    invite_link: str | None = Field(None, title="Invite Link")


SpanPublic.model_rebuild()
