"""The `SpanService` class for spans."""

from collections.abc import Sequence
from uuid import UUID

from sqlmodel import select

from ..models import SpanCreate, SpanTable
from .base import BaseService


class SpanService(BaseService[SpanTable, SpanCreate]):
    """The service class for spans."""

    table: type[SpanTable] = SpanTable
    create_model: type[SpanCreate] = SpanCreate

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
