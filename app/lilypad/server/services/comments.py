"""The `CommentService` class for comments."""

from collections.abc import Sequence
from uuid import UUID

from sqlmodel import asc, select

from ..models.comments import CommentTable
from ..schemas.comments import CommentCreate
from .base_organization import BaseOrganizationService


class CommentService(BaseOrganizationService[CommentTable, CommentCreate]):
    """The service class for comments."""

    table: type[CommentTable] = CommentTable
    create_model: type[CommentCreate] = CommentCreate

    def find_by_spans(self, span_uuid: UUID) -> Sequence[CommentTable]:
        """Find all comments by span and organization."""
        return self.session.exec(
            select(self.table)
            .where(
                self.table.span_uuid == span_uuid,
                self.table.organization_uuid == self.user.active_organization_uuid,
            )
            .order_by(asc(self.table.created_at))
        ).all()
