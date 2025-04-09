"""Pydantic schemas for experiments (EE)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from ..models.experiments import (
    ExperimentDefinitionBase,
    ExperimentRunBase,
    SampleResultBase,
)


class SampleResultCreate(BaseModel):
    """Schema for creating a sample result within an experiment run payload."""

    sample_index: int
    version_index: int
    version_name: str
    inputs_json: str
    ideal_json: str
    actual_raw_json: str | None = None
    metrics_json: str | None = None
    error: str | None = None
    execution_span_id: str | None = None


class SampleResultPublic(SampleResultBase):
    """Public schema for sample results."""

    uuid: UUID
    created_at: datetime


class ExperimentRunCreate(BaseModel):
    """Schema for creating an experiment run (payload from SDK)."""

    experiment_name: str
    run_timestamp: datetime | None = None
    root_trace_id: str | None = None
    root_span_id: str | None = None
    version_names_ordered: list[str]
    metric_names_ordered: list[str]
    status: str | None = None
    metadata_: dict | None = Field(default=None, alias="metadata")
    samples: list[SampleResultCreate]


class ExperimentRunSummaryPublic(ExperimentRunBase):  # NEW Schema for lists
    """Public schema for experiment run summaries (excluding detailed samples)."""

    uuid: UUID
    organization_uuid: UUID
    created_at: datetime


class ExperimentRunPublic(ExperimentRunBase):
    """Public schema for a single experiment run including sample results."""

    uuid: UUID
    organization_uuid: UUID
    created_at: datetime
    sample_results: list[SampleResultPublic] = []  # Include sample results


class ExperimentDefinitionCreate(ExperimentDefinitionBase):
    """Schema for creating experiment definitions."""

    pass


class ExperimentDefinitionPublic(ExperimentDefinitionBase):
    """Public schema for experiment definitions."""

    uuid: UUID
    organization_uuid: UUID
    created_at: datetime
