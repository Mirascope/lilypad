"""Database models for experiments, runs, and sample results (EE)."""

from datetime import datetime
from typing import TYPE_CHECKING, ClassVar
from uuid import UUID

from sqlalchemy import JSON, Column, Index, Text, UniqueConstraint
from sqlmodel import Field, Relationship, SQLModel

from ....server.models.base_organization_sql_model import BaseOrganizationSQLModel
from ....server.models.base_sql_model import BaseSQLModel, get_json_column
from ....server.models.table_names import (
    EXPERIMENT_DEFINITION_TABLE_NAME,
    EXPERIMENT_RUN_TABLE_NAME,
    PROJECT_TABLE_NAME,
    SAMPLE_RESULT_TABLE_NAME,
)

if TYPE_CHECKING:
    from ....server.models.projects import ProjectTable


class ExperimentDefinitionBase(SQLModel):
    """Base model for experiment definitions."""

    project_uuid: UUID = Field(
        foreign_key=f"{PROJECT_TABLE_NAME}.uuid", index=True, ondelete="CASCADE"
    )
    name: str = Field(index=True, nullable=False)
    description: str | None = Field(default=None, sa_column=Column(Text))
    target_function_name: str | None = Field(default=None, index=True)


class ExperimentDefinitionTable(
    ExperimentDefinitionBase, BaseOrganizationSQLModel, table=True
):
    """Table for storing experiment definitions (EE)."""

    __tablename__: ClassVar[str] = EXPERIMENT_DEFINITION_TABLE_NAME
    __table_args__ = (
        UniqueConstraint(
            "organization_uuid", "project_uuid", "name", name="uq_exp_org_proj_name"
        ),
    )

    project: "ProjectTable" = Relationship(back_populates="experiment_definitions")
    runs: list["ExperimentRunTable"] = Relationship(back_populates="definition")


class ExperimentRunBase(SQLModel):
    """Base model for experiment runs."""

    experiment_definition_uuid: UUID = Field(
        foreign_key=f"{EXPERIMENT_DEFINITION_TABLE_NAME}.uuid",
        index=True,
        ondelete="CASCADE",
    )
    project_uuid: UUID = Field(
        foreign_key=f"{PROJECT_TABLE_NAME}.uuid", index=True, ondelete="CASCADE"
    )
    run_timestamp: datetime = Field(
        default_factory=datetime.utcnow, nullable=False, index=True
    )
    root_trace_id: str | None = Field(default=None, index=True)
    root_span_id: str | None = Field(default=None, index=True)
    num_samples: int = Field(nullable=False)
    num_versions: int = Field(nullable=False)
    version_names_ordered: list[str] = Field(sa_column=get_json_column(), default=[])
    metric_names_ordered: list[str] = Field(sa_column=get_json_column(), default=[])
    status: str | None = Field(default=None, index=True)
    metadata_: dict | None = Field(
        default=None, sa_column=Column("metadata", JSON), alias="metadata"
    )


class ExperimentRunTable(ExperimentRunBase, BaseOrganizationSQLModel, table=True):
    """Table for storing individual experiment runs (EE)."""

    __tablename__: ClassVar[str] = EXPERIMENT_RUN_TABLE_NAME

    definition: "ExperimentDefinitionTable" = Relationship(back_populates="runs")
    sample_results: list["SampleResultTable"] = Relationship(back_populates="run")


class SampleResultBase(SQLModel):
    """Base model for sample results within an experiment run."""

    experiment_run_uuid: UUID = Field(
        foreign_key=f"{EXPERIMENT_RUN_TABLE_NAME}.uuid", index=True, ondelete="CASCADE"
    )
    sample_index: int = Field(nullable=False, index=True)
    version_index: int = Field(nullable=False, index=True)
    version_name: str = Field(nullable=False)
    inputs_json: str = Field(sa_column=Column(Text, nullable=False))
    ideal_json: str = Field(sa_column=Column(Text, nullable=False))
    actual_raw_json: str | None = Field(
        sa_column=Column(Text, nullable=True), default=None
    )
    metrics_json: str | None = Field(
        sa_column=Column(Text, nullable=True), default=None
    )
    error: str | None = Field(sa_column=Column(Text, nullable=True), default=None)
    execution_span_id: str | None = Field(default=None, index=True)


class SampleResultTable(SampleResultBase, BaseSQLModel, table=True):
    """Table for storing results of each version on each sample (EE)."""

    __tablename__: ClassVar[str] = SAMPLE_RESULT_TABLE_NAME
    __table_args__ = (
        Index(
            "ix_sample_result_run_sample_version",
            "experiment_run_uuid",
            "sample_index",
            "version_index",
        ),
    )

    run: "ExperimentRunTable" = Relationship(back_populates="sample_results")
