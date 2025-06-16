"""The `AnnotationService` class for annotations."""

from collections.abc import Sequence
from uuid import UUID

from sqlmodel import and_, case, delete, func, or_, select

from ....server.services.base_organization import BaseOrganizationService
from ...server.models.annotations import AnnotationTable, Label
from ...server.schemas.annotations import AnnotationCreate


class AnnotationService(BaseOrganizationService[AnnotationTable, AnnotationCreate]):
    """The service class for annotations."""

    table: type[AnnotationTable] = AnnotationTable
    create_model: type[AnnotationCreate] = AnnotationCreate

    def find_records_by_project_uuid(
        self, project_uuid: UUID
    ) -> Sequence[AnnotationTable]:
        """Find records."""
        return self.session.exec(
            select(self.table).where(
                self.table.project_uuid == project_uuid,
                self.table.label.is_(None),  # type: ignore
                or_(
                    self.table.assigned_to == self.user.uuid,
                    self.table.assigned_to.is_(None),  # type: ignore
                ),
            )
        ).all()

    def find_metrics_by_function_uuid(self, function_uuid: UUID) -> tuple[int, int]:
        """Find metrics by function.

        Returns:
            A tuple containing (success_count, total_count)
        """
        query_result = self.session.exec(
            select(
                func.sum(case((self.table.label == Label.PASS, 1), else_=0)).label(
                    "success_count"
                ),
                func.count().label("total_count"),
            ).where(
                self.table.function_uuid == function_uuid,
                self.table.label.is_not(None),  # type: ignore
            )
        ).one()

        success_count = query_result[0] if query_result[0] is not None else 0
        total_count = query_result[1]

        return success_count, total_count

    def find_records_by_function_uuid(
        self, function_uuid: UUID
    ) -> Sequence[AnnotationTable]:
        """Find records by function UUID."""
        return self.session.exec(
            select(self.table).where(
                self.table.function_uuid == function_uuid,
                or_(
                    self.table.assigned_to == self.user.uuid,
                    self.table.assigned_to.is_(None),  # type: ignore
                ),
            )
        ).all()

    def find_records_by_span_uuid(self, span_uuid: UUID) -> Sequence[AnnotationTable]:
        """Find records by span UUID."""
        return self.session.exec(
            select(self.table).where(
                self.table.span_uuid == span_uuid,
                or_(
                    self.table.assigned_to == self.user.uuid,
                    self.table.assigned_to.is_(None),  # type: ignore
                ),
            )
        ).all()

    def find_record_by_span_uuid(self, span_uuid: UUID) -> AnnotationTable | None:
        """Find records by function UUID."""
        return self.session.exec(
            select(self.table).where(self.table.span_uuid == span_uuid)
        ).first()

    def check_bulk_duplicates(self, checks: list[dict]) -> list[UUID]:
        """Check for duplicates in bulk and return list of duplicate span_uuids."""
        if not checks:
            return []  # pragma: no cover

        # Build query for all potential duplicates
        conditions = []
        span_uuids: list[UUID] = []  # Keep track of valid span UUIDs

        for check in checks:
            user_uuid = check.get("assigned_to")
            span_uuid = check["span_uuid"]

            if not isinstance(span_uuid, UUID):
                continue  # pragma: no cover

            span_uuids.append(span_uuid)

            if user_uuid is None:
                conditions.append(
                    and_(self.table.span_uuid == span_uuid, self.table.label.is_(None))  # type: ignore
                )
            else:
                conditions.append(
                    and_(
                        or_(
                            self.table.assigned_to == user_uuid,
                            self.table.assigned_to.is_(None),  # type: ignore
                        ),
                        self.table.span_uuid == span_uuid,
                        self.table.label.is_(None),  # type: ignore
                    )
                )

        if not conditions:
            return []  # pragma: no cover

        # Execute single query for all checks
        existing_records = self.session.exec(
            select(self.table).where(or_(*conditions))
        ).all()

        # Map results to span_uuids, ensuring we only include valid UUIDs
        existing_spans = {
            record.span_uuid for record in existing_records if record.span_uuid
        }
        duplicate_spans = [
            span_uuid for span_uuid in span_uuids if span_uuid in existing_spans
        ]

        return duplicate_spans

    def create_bulk_records(
        self, annotations_create: Sequence[AnnotationCreate], project_uuid: UUID
    ) -> list[AnnotationTable]:
        """Create multiple annotation records in bulk."""
        annotations = []
        for annotation in annotations_create:
            assigned_to = annotation.assigned_to if annotation.assigned_to else [None]
            for user_uuid in assigned_to:
                db_annotation = AnnotationTable.model_validate(
                    annotation,
                    update={
                        "organization_uuid": self.user.active_organization_uuid,
                        "project_uuid": project_uuid,
                        "assigned_to": user_uuid,
                    },
                )
                annotations.append(db_annotation)

        self.session.add_all(annotations)
        self.session.commit()

        # Refresh all instances to get generated values
        for annotation in annotations:
            self.session.refresh(annotation)

        return annotations

    def delete_records_by_uuids(self, uuids: Sequence[UUID]) -> bool:
        """Delete records by multiple UUIDs."""
        try:  # pragma: no cover
            self.session.exec(delete(self.table).where(self.table.uuid.in_(uuids)))  # type: ignore  # pragma: no cover
            return True  # pragma: no cover
        except Exception:  # pragma: no cover
            return False  # pragma: no cover
