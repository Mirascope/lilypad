"""The `SpanService` class for spans."""

from collections.abc import Sequence

from sqlmodel import select

from ..models import SpanCreate, SpanTable
from .base import BaseService


class SpanService(BaseService[SpanTable, SpanCreate]):
    """The service class for spans."""

    table: type[SpanTable] = SpanTable
    create_model: type[SpanCreate] = SpanCreate

    def find_records_by_version_id(
        self, project_id: int, version_id: int
    ) -> Sequence[SpanTable]:
        """Find spans by version id"""
        return self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_id == project_id,
                self.table.version_id == version_id,
            )
        ).all()
