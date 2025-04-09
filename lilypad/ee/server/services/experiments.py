"""Services for managing experiments and their results (EE)."""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError, NoResultFound
from sqlmodel import select

from ....server.services.base_organization import BaseOrganizationService
from ..models.experiments import (
    ExperimentDefinitionTable,
    ExperimentRunTable,
    SampleResultTable,
)
from ..schemas.experiments import ExperimentRunCreate


class ExperimentDefinitionService(
    BaseOrganizationService[ExperimentDefinitionTable, Any]
):
    """Service class for managing Experiment Definitions (EE)."""

    table: type[ExperimentDefinitionTable] = ExperimentDefinitionTable

    def find_or_create_definition(
        self, project_uuid: UUID, name: str
    ) -> ExperimentDefinitionTable:
        """Finds an experiment definition by name or creates it if not found."""
        try:
            definition = self.session.exec(
                select(self.table).where(
                    self.table.organization_uuid == self.user.active_organization_uuid,
                    self.table.project_uuid == project_uuid,
                    self.table.name == name,
                )
            ).one()
            return definition
        except NoResultFound:
            try:
                new_definition = self.table(
                    project_uuid=project_uuid,
                    name=name,
                    organization_uuid=self.user.active_organization_uuid,
                )
                self.session.add(new_definition)
                self.session.flush()
                self.session.refresh(new_definition)
                return new_definition
            except IntegrityError:
                self.session.rollback()
                definition = self.session.exec(
                    select(self.table).where(
                        self.table.organization_uuid
                        == self.user.active_organization_uuid,
                        self.table.project_uuid == project_uuid,
                        self.table.name == name,
                    )
                ).one()
                return definition


class ExperimentRunService(
    BaseOrganizationService[ExperimentRunTable, ExperimentRunCreate]
):
    """Service class for managing Experiment Runs and Sample Results (EE)."""

    table: type[ExperimentRunTable] = ExperimentRunTable
    create_model: type[ExperimentRunCreate] = ExperimentRunCreate

    def create_experiment_run(
        self, project_uuid: UUID, run_data: ExperimentRunCreate, definition_uuid: UUID
    ) -> ExperimentRunTable:
        """Creates an ExperimentRun record and its associated SampleResult records
        within a single database transaction.
        """
        try:
            with self.session.begin_nested():
                run_record = self.table(
                    experiment_definition_uuid=definition_uuid,
                    project_uuid=project_uuid,
                    organization_uuid=self.user.active_organization_uuid,
                    run_timestamp=run_data.run_timestamp or datetime.now(UTC),
                    root_trace_id=run_data.root_trace_id,
                    root_span_id=run_data.root_span_id,
                    num_samples=len(run_data.samples),
                    num_versions=len(run_data.version_names_ordered),
                    version_names_ordered=run_data.version_names_ordered,
                    metric_names_ordered=run_data.metric_names_ordered,
                    status=run_data.status,
                    metadata_=run_data.metadata_,
                )
                self.session.add(run_record)
                self.session.flush()

                if run_record.uuid is None:
                    raise ValueError(
                        "Failed to get UUID for ExperimentRun record after flush."
                    )

                sample_results_to_add: list[SampleResultTable] = []
                for sample_create_data in run_data.samples:
                    sample_result = SampleResultTable(
                        experiment_run_uuid=run_record.uuid,
                        sample_index=sample_create_data.sample_index,
                        version_index=sample_create_data.version_index,
                        version_name=sample_create_data.version_name,
                        inputs_json=sample_create_data.inputs_json,
                        ideal_json=sample_create_data.ideal_json,
                        actual_raw_json=sample_create_data.actual_raw_json,
                        metrics_json=sample_create_data.metrics_json,
                        error=sample_create_data.error,
                        execution_span_id=sample_create_data.execution_span_id,
                    )
                    sample_results_to_add.append(sample_result)

                if sample_results_to_add:
                    self.session.add_all(sample_results_to_add)

                self.session.flush()
                self.session.refresh(run_record)

            return run_record

        except IntegrityError as e:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Database integrity error: {e.orig}",
            )
        except Exception as e:
            self.session.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create experiment run: {e}",
            )

    def find_runs_by_definition_uuid(
        self, definition_uuid: UUID, limit: int = 100, offset: int = 0
    ) -> Sequence[ExperimentRunTable]:
        """Finds experiment runs for a given definition, ordered by timestamp."""
        return self.session.exec(
            select(self.table)
            .where(self.table.experiment_definition_uuid == definition_uuid)
            .order_by(self.table.run_timestamp.desc())
            .limit(limit)
            .offset(offset)
        ).all()

    def find_run_with_results(self, run_uuid: UUID) -> ExperimentRunTable:
        """Finds a specific run and eagerly loads its sample results."""
        from sqlalchemy.orm import selectinload

        run = self.session.exec(
            select(self.table)
            .where(self.table.uuid == run_uuid)
            .options(selectinload(self.table.sample_results))
        ).first()

        if not run or run.organization_uuid != self.user.active_organization_uuid:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Experiment run not found.",
            )
        return run
