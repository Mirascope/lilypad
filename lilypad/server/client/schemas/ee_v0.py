"""The Schema models for the Lilypad ee_v0 API."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field


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


class Label(str, Enum):
    """Label enum"""

    PASS_ = "pass"
    FAIL = "fail"


class Tier(str, Enum):
    """License tier enum."""

    FREE = "FREE"
    PRO = "PRO"
    TEAM = "TEAM"
    ENTERPRISE = "ENTERPRISE"


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


class AnnotationCreate(BaseModel):
    """Annotation create model."""

    label: Label | None = None
    reasoning: str | None = Field(None, title="Reasoning")
    type: EvaluationType | None = EvaluationType.MANUAL
    data: dict[str, Any] | None = Field(None, title="Data")
    span_uuid: UUID | None = Field(None, title="Span Uuid")
    project_uuid: UUID | None = Field(None, title="Project Uuid")
    generation_uuid: UUID | None = Field(None, title="Generation Uuid")
    assigned_to: list[UUID] | None = Field(None, title="Assigned To")


class AnnotationUpdate(BaseModel):
    """Annotation update model."""

    label: Label | None = None
    reasoning: str | None = Field(None, title="Reasoning")
    type: EvaluationType | None = EvaluationType.MANUAL
    data: dict[str, Any] | None = Field(None, title="Data")
    assigned_to: UUID | None = Field(None, title="Assigned To")


class HTTPValidationError(BaseModel):
    detail: list[ValidationError] | None = Field(None, title="Detail")


class LicenseInfo(BaseModel):
    """Pydantic model for license validation"""

    customer: str = Field(..., title="Customer")
    license_id: str = Field(..., title="License Id")
    expires_at: datetime = Field(..., title="Expires At")
    tier: Tier
    organization_uuid: UUID = Field(..., title="Organization Uuid")


class MessageParam(BaseModel):
    """Message param model agnostic to providers."""

    role: str = Field(..., title="Role")
    content: list[FieldAudioPart | FieldTextPart | FieldImagePart | FieldToolCall] = (
        Field(..., title="Content")
    )


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


class AnnotationPublic(BaseModel):
    """Annotation public model."""

    label: Label | None = None
    reasoning: str | None = Field(None, title="Reasoning")
    type: EvaluationType | None = EvaluationType.MANUAL
    data: dict[str, Any] | None = Field(None, title="Data")
    uuid: UUID = Field(..., title="Uuid")
    project_uuid: UUID = Field(..., title="Project Uuid")
    span_uuid: UUID = Field(..., title="Span Uuid")
    generation_uuid: UUID = Field(..., title="Generation Uuid")
    span: SpanMoreDetails
    assigned_to: UUID | None = Field(..., title="Assigned To")
