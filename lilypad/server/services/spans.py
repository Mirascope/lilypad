"""The `SpanService` class for spans."""

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy.orm import selectinload
from sqlmodel import and_, delete, select

from ..models import GenerationTable, SpanTable
from ..schemas import SpanCreate
from .base_organization import BaseOrganizationService


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
