"""The `GenerationService` class for generations."""

from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import func, select

from ..models import GenerationCreate, GenerationTable
from .base import BaseService


class GenerationService(BaseService[GenerationTable, GenerationCreate]):
    """The service class for generations."""

    table: type[GenerationTable] = GenerationTable
    create_model: type[GenerationCreate] = GenerationCreate

    def find_generations_by_name(
        self, project_uuid: UUID, name: str
    ) -> Sequence[GenerationTable]:
        """Find record by uuid"""
        record_tables = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.name == name,
            )
        ).all()
        return record_tables

    def get_next_version(self, project_uuid: UUID, name: str) -> int:
        """Get the next version number for a generation with this name."""
        count = self.session.exec(
            select(func.count()).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.name == name,
            )
        ).one()

        return count + 1

    def find_unique_generation_names_by_project_uuid(
        self, project_uuid: UUID
    ) -> Sequence[str]:
        """Find record by UUID."""
        record_tables = self.session.exec(
            select(self.table.name)
            .where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
            )
            .distinct()
        ).all()
        return record_tables

    def find_record_by_hash(self, hash: str) -> GenerationTable:
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
