"""The `SpanService` class for spans."""

from collections.abc import Sequence
from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import TextClause
from sqlalchemy.orm import selectinload
from sqlmodel import and_, delete, func, select, text

from ..models import GenerationTable, SpanTable
from ..schemas import SpanCreate
from .base_organization import BaseOrganizationService


class TimeFrame(str, Enum):
    """Timeframe for aggregation"""

    DAY = "day"
    WEEK = "week"
    MONTH = "month"
    LIFETIME = "lifetime"


class AggregateMetrics(BaseModel):
    """Aggregated metrics for spans"""

    total_cost: float
    total_input_tokens: float
    total_output_tokens: float
    average_duration_ms: float
    span_count: int
    start_date: datetime | None
    end_date: datetime | None


class SpanService(BaseOrganizationService[SpanTable, SpanCreate]):
    """The service class for spans."""

    table: type[SpanTable] = SpanTable
    create_model: type[SpanCreate] = SpanCreate

    def find_all_no_parent_spans(self, project_uuid: UUID) -> Sequence[SpanTable]:
        """Get all spans.
        Child spans are not lazy loaded to avoid N+1 queries.
        """
        return self.session.exec(
            select(SpanTable)
            .where(
                SpanTable.project_uuid == project_uuid,
                SpanTable.parent_span_id.is_(None),  # type: ignore
            )
            .options(selectinload(SpanTable.child_spans, recursion_depth=-1))  # pyright: ignore [reportArgumentType]
        ).all()

    def find_records_by_generation_uuid(
        self, project_uuid: UUID, generation_uuid: UUID
    ) -> Sequence[SpanTable]:
        """Find spans by version uuid"""
        return self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.generation_uuid == generation_uuid,
            )
        ).all()

    def _get_date_trunc(self, timeframe: TimeFrame) -> TextClause | None:
        """Get the appropriate date truncation for the timeframe"""
        if timeframe == TimeFrame.LIFETIME:
            return None
        return text(f"date_trunc('{timeframe.value}', created_at)")

    def find_aggregate_data_by_generation_uuid(
        self, project_uuid: UUID, generation_uuid: UUID
    ) -> Sequence[SpanTable]:
        """Find spans by version uuid"""
        return self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.generation_uuid == generation_uuid,
            )
        ).all()

    def get_aggregated_metrics(
        self, project_uuid: UUID, generation_uuid: UUID, timeframe: TimeFrame
    ) -> list[AggregateMetrics]:
        """Get aggregated metrics for spans grouped by the specified timeframe"""
        # Base query with common filters
        query = select(
            func.sum(self.table.cost).label("total_cost"),
            func.sum(self.table.input_tokens).label("total_input_tokens"),
            func.sum(self.table.output_tokens).label("total_output_tokens"),
            func.avg(self.table.duration_ms).label("average_duration_ms"),
            func.count().label("span_count"),
        ).where(  # pyright: ignore[reportCallIssue]
            self.table.organization_uuid == self.user.active_organization_uuid,
            self.table.project_uuid == project_uuid,
            self.table.generation_uuid == generation_uuid,
        )
        # Add time-based grouping if not lifetime
        date_trunc = self._get_date_trunc(timeframe)
        if date_trunc is not None:
            if timeframe == TimeFrame.DAY:
                # For daily grouping, we can use DATE(created_at)
                date_group = func.date(self.table.created_at).label("period_start")
            else:
                # For week and month, we need to extract the relevant parts
                if timeframe == TimeFrame.WEEK:
                    date_group = func.date_trunc("week", self.table.created_at).label(
                        "period_start"
                    )
                else:  # month
                    date_group = func.date_trunc("month", self.table.created_at).label(
                        "period_start"
                    )

            query = query.add_columns(date_group)
            query = query.group_by(date_group)
            query = query.order_by(date_group)

        results = self.session.exec(query).all()
        # Transform results into the expected format
        metrics: list[AggregateMetrics] = []
        for row in results:
            metric = AggregateMetrics(
                total_cost=float(row.total_cost or 0),
                total_input_tokens=float(row.total_input_tokens or 0),
                total_output_tokens=float(row.total_output_tokens or 0),
                average_duration_ms=float(row.average_duration_ms or 0),
                span_count=row.span_count,
                start_date=getattr(row, "period_start", None),
                end_date=None,  # Can be calculated if needed based on timeframe
            )
            metrics.append(metric)
        return metrics

    def delete_records_by_generation_name(
        self, project_uuid: UUID, generation_name: str
    ) -> bool:
        """Delete all spans by generation name"""
        delete_stmt = delete(self.table).where(
            and_(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.generation_uuid.in_(  # type: ignore
                    select(GenerationTable.uuid).where(
                        GenerationTable.name == generation_name
                    )
                ),
            )
        )

        self.session.exec(delete_stmt)  # type: ignore
        self.session.flush()
        return True

    def create_bulk_records(
        self, spans_create: Sequence[SpanCreate], project_uuid: UUID
    ) -> list[SpanTable]:
        """Create multiple annotation records in bulk."""
        spans = []
        for span_create in spans_create:
            span = self.table.model_validate(
                span_create,
                update={
                    "organization_uuid": self.user.active_organization_uuid,
                    "user_uuid": self.user.uuid,
                    "project_uuid": project_uuid,
                },
            )
            spans.append(span)

        self.session.add_all(spans)
        self.session.commit()
        return spans

    def delete_records_by_generation_uuid(
        self, project_uuid: UUID, generation_uuid: UUID
    ) -> bool:
        """Delete all spans by generation uuid"""
        delete_stmt = delete(self.table).where(
            and_(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.generation_uuid == generation_uuid,
            )
        )
        self.session.exec(delete_stmt)  # type: ignore
        self.session.flush()
        return True
