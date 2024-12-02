"""The `FunctionService` class for functions."""

from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select

from ..models import FunctionCreate, FunctionTable
from .base import BaseService


class FunctionService(BaseService[FunctionTable, FunctionCreate]):
    """The service class for functions."""

    table: type[FunctionTable] = FunctionTable
    create_model: type[FunctionCreate] = FunctionCreate

    def find_records_by_name(
        self, project_uuid: UUID, name: str
    ) -> Sequence[FunctionTable]:
        """Find record by uuid"""
        record_tables = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.name == name,
            )
        ).all()
        return record_tables

    def find_unique_function_names_by_project_uuid(
        self, project_uuid: UUID
    ) -> Sequence[str]:
        """Find record by uuid"""
        record_tables = self.session.exec(
            select(self.table.name)
            .where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
            )
            .distinct()
        ).all()
        return record_tables

    def find_record_by_hash(self, hash: str) -> FunctionTable:
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
