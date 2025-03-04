"""The `AnnotationService` class for annotations."""

from collections.abc import Sequence
from uuid import UUID

from sqlmodel import and_, delete, or_, select

from ....server.services.base_organization import BaseOrganizationService
from ...server.models import AnnotationTable
from ...server.schemas import AnnotationCreate


class AnnotationService(BaseOrganizationService[AnnotationTable, AnnotationCreate]):
    """The service class for annotations."""

    table: type[AnnotationTable] = AnnotationTable
    create_model: type[AnnotationCreate] = AnnotationCreate

    def find_records_by_generation_uuid(
        self, generation_uuid: UUID
    ) -> Sequence[AnnotationTable]:
        """Find records by generation UUID."""
        return self.session.exec(
            select(self.table).where(
                self.table.generation_uuid == generation_uuid,
                or_(
                    self.table.assigned_to == self.user.uuid,
                    self.table.assigned_to.is_(None),  # type: ignore
                ),
            )
        ).all()

    def find_record_by_span_uuid(self, span_uuid: UUID) -> AnnotationTable | None:
        """Find records by generation UUID."""
        return self.session.exec(
            select(self.table).where(self.table.span_uuid == span_uuid)
        ).first()

    def check_bulk_duplicates(self, checks: list[dict]) -> list[UUID]:
        """Check for duplicates in bulk and return list of duplicate span_uuids."""
        if not checks:
            return []

        # Build query for all potential duplicates
        conditions = []
        span_uuids: list[UUID] = []  # Keep track of valid span UUIDs

        for check in checks:
            user_uuid = check.get("assigned_to")
            span_uuid = check["span_uuid"]

            if not isinstance(span_uuid, UUID):
                continue

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
            return []

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
        try:
            self.session.exec(delete(self.table).where(self.table.uuid.in_(uuids)))  # type: ignore
            return True
        except Exception:
            return False
