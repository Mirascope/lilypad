"""The `PromptService` class for prompts."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select

from ..models import PromptCreate, PromptTable
from .base import BaseService


class PromptService(BaseService[PromptTable, PromptCreate]):
    """The service class for functions."""

    table: type[PromptTable] = PromptTable
    create_model: type[PromptCreate] = PromptCreate

    def find_prompt_active_version_by_hash(self, hash: str) -> PromptTable:
        """Find active version of prompt by its hash"""
        record_table = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.hash == hash,
                self.table.is_active,
            )
        ).first()
        if not record_table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record for {self.table.__tablename__} not found",
            )
        return record_table

    def change_active_version(
        self, project_uuid: UUID, new_active_version: PromptTable
    ) -> PromptTable:
        """Change active version of prompt."""
        # Deactivate all currently active versions for the same function
        stmt = select(PromptTable).where(
            PromptTable.project_uuid == project_uuid,
            PromptTable.name == new_active_version.name,
            PromptTable.is_active,
        )
        current_active_versions = self.session.exec(stmt).all()

        for version in current_active_versions:
            version.is_active = False
            self.session.add(version)

        # Activate the new version
        new_active_version.is_active = True
        self.session.add(new_active_version)
        self.session.flush()

        # Refresh to get latest state
        self.session.refresh(new_active_version)
        return new_active_version
