"""The `SpanService` class for spans."""

from collections.abc import Sequence
from datetime import date, datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import TextClause
from sqlalchemy.orm import selectinload
from sqlmodel import and_, delete, func, select, text

from ..models import FunctionTable, SpanTable, SpanTagLink
from ..schemas.spans import SpanCreate, SpanUpdate
from .base_organization import BaseOrganizationService
from .tags import TagService


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
    function_uuid: UUID | None


class SpanService(BaseOrganizationService[SpanTable, SpanCreate]):
    """The service class for spans."""

    table: type[SpanTable] = SpanTable
    create_model: type[SpanCreate] = SpanCreate

    def find_all_no_parent_spans(self, project_uuid: UUID) -> Sequence[SpanTable]:
        """Get all spans.
        Child spans are not lazy loaded to avoid N+1 queries.
        """
        return self.session.exec(
            select(self.table)
            .where(
                self.table.project_uuid == project_uuid,
                self.table.parent_span_id.is_(None),  # type: ignore
            )
            .options(selectinload(self.table.child_spans, recursion_depth=-1))  # pyright: ignore [reportArgumentType]
        ).all()

    def find_records_by_function_uuid(
        self, project_uuid: UUID, function_uuid: UUID
    ) -> Sequence[SpanTable]:
        """Find spans by version uuid"""
        return self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.function_uuid == function_uuid,
                self.table.parent_span_id.is_(None),  # type: ignore
            )
        ).all()

    def get_record_by_span_id(self, project_uuid: UUID, spand_id: str) -> SpanTable:
        """Find spans by spand id"""
        return self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.span_id == spand_id,
                self.table.parent_span_id.is_(None),  # type: ignore
            )
        ).one_or_none()

    def update_tags(self, uuid: UUID, span_update: SpanUpdate) -> SpanTable:
        """Updates a record based on the uuid, efficiently syncing with span_update.tags"""
        record_table = self.find_record_by_uuid(uuid)

        # Only update tags if span_update.tags is not None
        if span_update.tags is not None:
            # Get existing tag links
            existing_links = self.session.exec(
                select(SpanTagLink).where(SpanTagLink.span_uuid == uuid)
            ).all()

            existing_tag_uuids = {link.tag_uuid for link in existing_links}

            new_tag_uuids = {tag.uuid for tag in span_update.tags}

            to_add = new_tag_uuids - existing_tag_uuids
            to_remove = existing_tag_uuids - new_tag_uuids

            if to_remove:
                delete_statement = delete(SpanTagLink).where(
                    SpanTagLink.span_uuid == uuid,  # pyright: ignore [reportArgumentType]
                    SpanTagLink.tag_uuid.in_(to_remove),  # type: ignore
                )
                self.session.connection().execute(delete_statement)

            # Add links that need to be added
            for tag_uuid in to_add:
                new_link = SpanTagLink(
                    span_uuid=uuid, tag_uuid=tag_uuid, created_by=self.user.uuid
                )
                self.session.add(new_link)

        self.session.flush()
        return record_table

    def _get_date_trunc(self, timeframe: TimeFrame) -> TextClause | None:
        """Get the appropriate date truncation for the timeframe"""
        if timeframe == TimeFrame.LIFETIME:
            return None
        return text(f"date_trunc('{timeframe.value}', created_at)")

    def find_aggregate_data_by_function_uuid(
        self, project_uuid: UUID, function_uuid: UUID
    ) -> Sequence[SpanTable]:
        """Find spans by version uuid"""
        return self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.function_uuid == function_uuid,
            )
        ).all()

    def get_aggregated_metrics(
        self,
        project_uuid: UUID,
        function_uuid: UUID | None = None,
        time_frame: TimeFrame = TimeFrame.LIFETIME,
    ) -> list[AggregateMetrics]:
        """Get aggregated metrics for spans grouped by the specified timeframe

        Parameters:
        - project_uuid: Project to get metrics for
        - function_uuid: Optional specific function to filter by
        - time_frame: Time period to group by (DAY, WEEK, MONTH, LIFETIME)

        Returns:
        - List of aggregated metrics, optionally grouped by function
        """
        # Base query with common filters
        base_filters = [
            self.table.organization_uuid == self.user.active_organization_uuid,
            self.table.project_uuid == project_uuid,
        ]

        columns = [
            func.sum(self.table.cost).label("total_cost"),
            func.sum(self.table.input_tokens).label("total_input_tokens"),
            func.sum(self.table.output_tokens).label("total_output_tokens"),
            func.avg(self.table.duration_ms).label("average_duration_ms"),
            func.count().label("span_count"),
        ]

        group_by_columns = []
        date_group = None

        if function_uuid is not None:
            base_filters.append(self.table.function_uuid == function_uuid)
        else:
            columns.append(self.table.function_uuid.label("function_uuid"))  # type: ignore
            group_by_columns.append(self.table.function_uuid)
            base_filters.append(self.table.parent_span_id.is_(None))  # type: ignore

        # Add time-based grouping if not lifetime
        date_trunc = self._get_date_trunc(time_frame)

        if date_trunc is not None:
            if time_frame == TimeFrame.DAY:
                date_group = func.date(self.table.created_at).label("period_start")
            elif time_frame == TimeFrame.WEEK:
                date_group = func.date_trunc("week", self.table.created_at).label(
                    "period_start"
                )
            elif time_frame == TimeFrame.MONTH:
                date_group = func.date_trunc("month", self.table.created_at).label(
                    "period_start"
                )

            if date_group is not None:
                columns.append(date_group)
                group_by_columns.append(date_group)

        # Build the final query
        query = select(*columns).where(*base_filters)

        if group_by_columns:
            query = query.group_by(*group_by_columns)

        if date_group is not None:
            query = query.order_by(date_group)

        results = self.session.exec(query).all()

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
                function_uuid=function_uuid or getattr(row, "function_uuid", None),
            )
            metrics.append(metric)

        return metrics

    def delete_records_by_function_name(
        self, project_uuid: UUID, function_name: str
    ) -> bool:
        """Delete all spans by function name"""
        delete_stmt = delete(self.table).where(
            and_(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.function_uuid.in_(  # type: ignore
                    select(FunctionTable.uuid).where(
                        FunctionTable.name == function_name
                    )
                ),
            )
        )

        self.session.exec(delete_stmt)  # type: ignore
        self.session.flush()
        return True

    def count_by_current_month(self) -> int:
        """Count the number of spans created in the current month"""
        # Get first and last day of current month
        today = datetime.now()
        start_of_month = date(today.year, today.month, 1)

        # Calculate first day of next month
        if today.month == 12:
            end_of_month = date(today.year + 1, 1, 1)
        else:
            end_of_month = date(today.year, today.month + 1, 1)

        query = (
            select(func.count())
            .select_from(self.table)
            .where(
                self.table.created_at >= start_of_month,
                self.table.created_at < end_of_month,
                self.table.organization_uuid == self.user.active_organization_uuid,
            )
        )

        count = self.session.exec(query).one()
        return count

    def create_bulk_records(
        self, spans_create: Sequence[SpanCreate], project_uuid: UUID
    ) -> list[SpanTable]:
        """Create multiple annotation records in bulk."""
        spans_to_add = []
        tag_service = TagService(self.session, self.user)

        for span_create in spans_create:
            db_span = self.table.model_validate(
                span_create,
                update={
                    "organization_uuid": self.user.active_organization_uuid,
                    "user_uuid": self.user.uuid,
                    "project_uuid": project_uuid,
                },
            )
            spans_to_add.append(db_span)

            otel_attributes = db_span.data.get("attributes", {})
            if (
                decorator_tag_names := otel_attributes.get("lilypad.decorator.tags")
            ) and isinstance(decorator_tag_names, list):
                if not hasattr(db_span, "_temp_links_to_add"):
                    db_span._temp_links_to_add = []  # type: ignore
                for tag_name in decorator_tag_names:
                    if isinstance(tag_name, str):
                        tag = tag_service.find_or_create_tag(tag_name, project_uuid)
                        db_span._temp_links_to_add.append(tag.uuid)  # type: ignore

        self.session.add_all(spans_to_add)
        self.session.flush()

        final_links_to_add = []
        for db_span in spans_to_add:
            if hasattr(db_span, "_temp_links_to_add") and db_span.uuid:
                for tag_uuid in db_span._temp_links_to_add:  # type: ignore
                    final_links_to_add.append(
                        SpanTagLink(
                            span_uuid=db_span.uuid,
                            tag_uuid=tag_uuid,
                            created_by=self.user.uuid,
                        )
                    )
                del db_span._temp_links_to_add  # type: ignore

        if final_links_to_add:
            self.session.add_all(final_links_to_add)
            self.session.flush()

        return spans_to_add

    def delete_records_by_function_uuid(
        self, project_uuid: UUID, function_uuid: UUID
    ) -> bool:
        """Delete all spans by function uuid"""
        delete_stmt = delete(self.table).where(
            and_(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.function_uuid == function_uuid,
            )
        )
        self.session.exec(delete_stmt)  # type: ignore
        self.session.flush()
        return True

    async def update_span(
        self,
        span_uuid: UUID,
        update_data: SpanUpdate,
        user_uuid: UUID,
    ) -> SpanTable:
        """Update a span record by UUID"""
        span_to_update = self.find_record_by_uuid(span_uuid)

        tags_modified = self._sync_span_tags(span_to_update, update_data, user_uuid)
        other_fields_modified = False
        if tags_modified or other_fields_modified:
            self.session.commit()
            self.session.refresh(span_to_update)
        return span_to_update

    def _sync_span_tags(
        self, span: SpanTable, span_update: SpanUpdate, user_uuid: UUID
    ) -> bool:
        target_tag_uuids: set[UUID] = set()
        if span_update.tags_by_uuid is not None:
            target_tag_uuids.update(span_update.tags_by_uuid)
        elif span_update.tags_by_name is not None:
            tag_service = TagService(self.session, self.user)
            for name in span_update.tags_by_name:
                tag = tag_service.find_or_create_tag(name, span.project_uuid)
                target_tag_uuids.add(tag.uuid)
        else:
            return False

        existing_links = self.session.exec(
            select(SpanTagLink).where(SpanTagLink.span_uuid == span.uuid)
        ).all()
        existing_tag_uuids = {link.tag_uuid for link in existing_links if link.tag_uuid}
        to_add = target_tag_uuids - existing_tag_uuids
        to_remove = existing_tag_uuids - target_tag_uuids
        modified = False
        if to_remove:
            self.session.exec(
                delete(SpanTagLink).where(
                    SpanTagLink.span_uuid == span.uuid,
                    SpanTagLink.tag_uuid.in_(to_remove),
                )
            )
            modified = True
        for tag_uuid in to_add:
            self.session.add(
                SpanTagLink(
                    span_uuid=span.uuid, tag_uuid=tag_uuid, created_by=user_uuid
                )
            )
            modified = True
        return modified
