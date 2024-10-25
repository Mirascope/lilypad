"""LLMFunctionService class"""

from typing import Sequence

from fastapi import HTTPException, status
from sqlmodel import select

from lilypad.models import LLMFunctionCreate
from lilypad.server.models import LLMFunctionTable

from . import BaseService


class LLMFunctionService(BaseService[LLMFunctionTable, LLMFunctionCreate]):
    """LLMFunctionService class"""

    table: type[LLMFunctionTable] = LLMFunctionTable
    create_model: type[LLMFunctionCreate] = LLMFunctionCreate

    def find_records_by_name(
        self, project_id: int, function_name: str
    ) -> Sequence[LLMFunctionTable]:
        """Find record by id"""
        record_tables = self.session.exec(
            select(self.table).where(
                self.table.project_id == project_id,
                self.table.function_name == function_name,
            )
        ).all()
        return record_tables

    def find_record_by_hash(self, version_hash: str) -> LLMFunctionTable:
        """Find record by hash"""
        record_table = self.session.exec(
            select(self.table).where(
                self.table.version_hash == version_hash,
            )
        ).first()
        if not record_table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record for {self.table.__tablename__} not found",
            )
        return record_table
