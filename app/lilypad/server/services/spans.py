"""The `SpanService` class for spans."""

import logging
from collections.abc import Sequence
from datetime import date, datetime
from enum import Enum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy import TextClause
from sqlalchemy.orm import selectinload
from sqlmodel import and_, delete, func, select, text

from ..models.functions import FunctionTable
from ..models.organizations import OrganizationTable
from ..models.spans import SpanTable, SpanTagLink
from ..schemas.spans import SpanCreate, SpanUpdate
from .base_organization import BaseOrganizationService
from .billing import BillingService, _CustomerNotFound
from .tags import TagService

logger = logging.getLogger(__name__)


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

    def count_no_parent_spans(self, project_uuid: UUID) -> int:
        """Return the *total* number of root‑level spans for a project.

        Unlike :py:meth:`find_no_parent_spans` this query only counts rows and
        therefore avoids the overhead of eager‑loading child spans.
        """
        stmt = (
            select(func.count())
            .select_from(self.table)
            .where(
                self.table.project_uuid == project_uuid,
                self.table.parent_span_id.is_(None),  # type: ignore [comparison‑overlap]
            )
        )

        return self.session.exec(stmt).one()

    def find_all_no_parent_spans(
        self,
        project_uuid: UUID,
        *,
        limit: int | None = None,
        offset: int = 0,
        order: Literal["asc", "desc"] = "desc",
    ) -> Sequence[SpanTable]:
        """Find all root spans for a project."""
        stmt = (
            select(self.table)
            .where(
                self.table.project_uuid == project_uuid,
                self.table.parent_span_id.is_(None),  # type: ignore [comparison‑overlap]
            )
            .order_by(
                self.table.created_at.asc()  # pyright: ignore [reportAttributeAccessIssue]
                if order == "asc"
                else self.table.created_at.desc()  # pyright: ignore [reportAttributeAccessIssue]                                         )
            )
            .offset(offset)
            .options(
                selectinload(self.table.child_spans, recursion_depth=-1)  # pyright: ignore [reportArgumentType]
            )
        )

        if limit is not None:
            stmt = stmt.limit(limit)

        return self.session.exec(stmt).all()

    def find_root_parent_span(
        self,
        span_id: str,
    ) -> SpanTable | None:
        """Find the root parent span (parent with no parent) for a given span UUID in a single query using SQLModel."""
        root_span_query = text("""
            WITH RECURSIVE span_hierarchy AS (
                -- Base case: start with the specified span
                SELECT uuid, span_id, parent_span_id, created_at, project_uuid
                FROM spans
                WHERE span_id = :span_id
                
                UNION ALL
                
                -- Recursive case: join with parent spans
                SELECT s.uuid, s.span_id, s.parent_span_id, s.created_at, s.project_uuid
                FROM spans s
                JOIN span_hierarchy sh ON s.span_id = sh.parent_span_id
            )
            -- Select the root span (where parent_span_id is NULL)
            SELECT uuid
            FROM span_hierarchy
            WHERE parent_span_id IS NULL
            LIMIT 1
        """).bindparams(span_id=span_id)

        result = self.session.exec(root_span_query).first()  # type: ignore

        if not result:
            return None

        root_span = self.session.exec(
            select(self.table).where(self.table.uuid == result.uuid)
        ).first()

        return root_span

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

    def get_record_by_span_id(self, project_uuid: UUID, span_id: str) -> SpanTable:
        """Find spans by span id"""
        return self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.span_id == span_id,
                self.table.parent_span_id.is_(None),  # type: ignore
            )
        ).one_or_none()

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
        self,
        spans_create: Sequence[SpanCreate],
        billing_service: BillingService | None,
        project_uuid: UUID,
        organization_uuid: UUID,
    ) -> list[SpanTable]:
        """Create multiple annotation records in bulk."""
        spans_to_add = []
        tag_service = TagService(self.session, self.user)

        for span_create in spans_create:
            db_span = self.table.model_validate(
                span_create,
                update={
                    "organization_uuid": organization_uuid,
                    "user_uuid": self.user.uuid,
                    "project_uuid": project_uuid,
                },
            )
            spans_to_add.append(db_span)

            otel_attributes = db_span.data.get("attributes", {})
            if (
                trace_tag_names := otel_attributes.get("lilypad.trace.tags")
            ) and isinstance(trace_tag_names, list):
                if not hasattr(db_span, "_temp_links_to_add"):
                    db_span._temp_links_to_add = []  # type: ignore
                for tag_name in trace_tag_names:
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

        if billing_service:
            try:
                self._report_span_usage_with_retry(
                    billing_service, organization_uuid, len(spans_to_add)
                )
            except Exception as e:
                # if reporting fails, we don't want to fail the entire span creation
                logger.error("Error reporting span usage: %s", e)

        return spans_to_add

    def _report_span_usage_with_retry(
        self, billing_service: BillingService, organization_uuid: UUID, quantity: int
    ) -> None:
        """Report span usage to Stripe with retry logic."""
        try:
            billing_service.report_span_usage(organization_uuid, quantity=quantity)
        except _CustomerNotFound:
            # We don't expect this to happen, but if it does, we need to create a customer
            logger.info(f"Creating customer for organization {organization_uuid}")
            organization = self.session.exec(
                select(OrganizationTable).where(
                    OrganizationTable.uuid == organization_uuid
                )
            ).first()

            if not organization:
                logger.error(f"Organization {organization_uuid} not found")
                return

            email = self.user.email

            billing_service.create_customer(organization, email)

            billing_service.report_span_usage(organization_uuid, quantity=quantity)

    def get_spans_since(
        self, project_uuid: UUID, since: datetime
    ) -> Sequence[SpanTable]:
        """Get spans created since the given timestamp.

        Args:
            project_uuid: The project UUID
            since: Get spans created after this timestamp

        Returns:
            List of spans created since the timestamp
        """
        stmt = (
            select(self.table)
            .where(
                self.table.project_uuid == project_uuid,
                self.table.created_at > since,
                self.table.parent_span_id.is_(None),  # pyright: ignore [reportOptionalMemberAccess, reportAttributeAccessIssue]
            )
            .order_by(self.table.created_at.desc())  # pyright: ignore [reportAttributeAccessIssue]
            .options(
                selectinload(
                    self.table.child_spans,
                    recursion_depth=-1,  # pyright: ignore [reportArgumentType]
                )  # Load all children
            )
        )

        return self.session.exec(stmt).all()

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
                tag = tag_service.find_or_create_tag(name, span.project_uuid)  # pyright: ignore [reportArgumentType]
                target_tag_uuids.add(tag.uuid)  # pyright: ignore [reportArgumentType]
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
                    SpanTagLink.span_uuid == span.uuid,  # pyright: ignore [reportArgumentType]
                    SpanTagLink.tag_uuid.in_(to_remove),  # type: ignore
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

    def count_records_by_function_uuid(
        self, project_uuid: UUID, function_uuid: UUID
    ) -> int:
        """Count root-level spans for a function (fast COUNT(*))."""
        stmt = (
            select(func.count())
            .select_from(self.table)
            .where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.function_uuid == function_uuid,
                self.table.parent_span_id.is_(None),  # type: ignore
            )
        )
        return self.session.exec(stmt).one()

    def find_records_by_function_uuid_paged(
        self,
        project_uuid: UUID,
        function_uuid: UUID,
        *,
        limit: int,
        offset: int = 0,
        order: str = "desc",
    ) -> Sequence[SpanTable]:
        """Find root-level spans for a function with pagination + dynamic sort."""
        stmt = (
            select(self.table)
            .where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.function_uuid == function_uuid,
                self.table.parent_span_id.is_(None),  # type: ignore
            )
            .order_by(
                self.table.created_at.asc()  # pyright: ignore [reportAttributeAccessIssue]
                if order == "asc"
                else self.table.created_at.desc()  # pyright: ignore [reportAttributeAccessIssue]                                         )
            )
            .limit(limit)
            .offset(offset)
        )
        return self.session.exec(stmt).all()
