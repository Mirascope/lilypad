"""The `PromptService` class for prompts."""

from fastapi import HTTPException, status
from sqlmodel import select

from ..models import PromptCreate, PromptTable
from .base import BaseService


class PromptService(BaseService[PromptTable, PromptCreate]):
    """The service class for functions."""

    table: type[PromptTable] = PromptTable
    create_model: type[PromptCreate] = PromptCreate

    def find_record_by_hash(self, hash: str) -> PromptTable:
        """Find record by hash"""
        record_table = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.hash == hash,
            )
        ).first()
        if not record_table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record for {self.table.__tablename__} not found",
            )
        return record_table
