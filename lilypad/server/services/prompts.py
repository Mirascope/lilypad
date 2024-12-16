"""The `PromptService` class for prompts."""

from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select

from ..models import PromptCreate, PromptTable
from .base import BaseService


class PromptService(BaseService[PromptTable, PromptCreate]):
    """The service class for functions."""

    table: type[PromptTable] = PromptTable
    create_model: type[PromptCreate] = PromptCreate

    def find_records_by_name(
        self, project_uuid: UUID, name: str
    ) -> Sequence[PromptTable]:
        """Find record by uuid"""
        record_tables = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.name == name,
            )
        ).all()
        return record_tables

    def find_prompts_by_signature(
        self, project_uuid: UUID, signature: str
    ) -> Sequence[PromptTable]:
        """Find record by UUID."""
        record_tables = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.signature == signature,
            )
        ).all()
        return record_tables

    def find_unique_prompt_names(self, project_uuid: UUID) -> Sequence[str]:
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

    def find_prompt_by_call_params(
        self, prompt_create: PromptCreate
    ) -> PromptTable | None:
        """Find prompt by call params"""
        return self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.hash == prompt_create.hash,
                self.table.call_params == prompt_create.call_params,
            )
        ).first()

    def find_prompt_active_version_by_hash(self, hash: str) -> PromptTable:
        """Find active version of prompt by its hash"""
        record_table = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.hash == hash,
                self.table.is_default,
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
        stmt = select(self.table).where(
            self.table.project_uuid == project_uuid,
            self.table.name == new_active_version.name,
            self.table.signature == new_active_version.signature,
            self.table.is_default,
        )
        current_active_versions = self.session.exec(stmt).all()

        for version in current_active_versions:
            version.is_default = False
            self.session.add(version)

        # Activate the new version
        new_active_version.is_default = True
        self.session.add(new_active_version)
        self.session.flush()

        # Refresh to get latest state
        self.session.refresh(new_active_version)
        return new_active_version
