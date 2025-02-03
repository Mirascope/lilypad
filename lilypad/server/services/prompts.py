"""The `PromptService` class for prompts."""

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import and_, func, join, select

from ..models import GenerationTable, PromptTable
from ..schemas import PromptCreate
from .base_organization import BaseOrganizationService


class PromptService(BaseOrganizationService[PromptTable, PromptCreate]):
    """The service class for functions."""

    table: type[PromptTable] = PromptTable
    create_model: type[PromptCreate] = PromptCreate

    def find_prompts_by_name(
        self, project_uuid: UUID, name: str
    ) -> Sequence[PromptTable]:
        """Find record by uuid"""
        record_tables = self.session.exec(
            select(self.table)
            .where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.name == name,
                self.table.archived.is_(None),  # type: ignore
            )
            .order_by(self.table.version_num.asc())  # type: ignore
        ).all()
        return record_tables

    def get_next_version(self, project_uuid: UUID, name: str) -> int:
        """Get the next version number for a prompt with this name."""
        count = self.session.exec(
            select(func.count()).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.name == name,
            )
        ).one()

        return count + 1

    def find_prompts_by_signature(
        self, project_uuid: UUID, signature: str
    ) -> Sequence[PromptTable]:
        """Find record by UUID."""
        record_tables = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.signature == signature,
                self.table.archived.is_(None),  # type: ignore
            )
        ).all()
        return record_tables

    def find_unique_prompt_names(self, project_uuid: UUID) -> Sequence[PromptTable]:
        """Find record by UUID, getting latest version for each name."""
        latest_versions = (
            select(
                self.table.name, func.max(self.table.version_num).label("max_version")
            )
            .where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.archived.is_(None),  # type: ignore
            )
            .group_by(self.table.name)
            .subquery()
        )

        record_tables = self.session.exec(
            select(self.table)
            .join(
                latest_versions,
                and_(
                    self.table.name == latest_versions.c.name,
                    self.table.version_num == latest_versions.c.max_version,
                ),
            )
            .where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.archived.is_(None),  # type: ignore
            )
            .order_by(latest_versions.c.max_version.desc())
        ).all()
        return record_tables

    def check_duplicate_prompt(
        self, project_uuid: UUID, prompt_create: PromptCreate
    ) -> PromptTable | None:
        """Find prompt by call params"""
        return self.session.exec(
            select(self.table).where(
                self.table.project_uuid == project_uuid,
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.hash == prompt_create.hash,
                self.table.call_params == prompt_create.call_params,
                self.table.arg_types == prompt_create.arg_types,
                self.table.archived.is_(None),  # type: ignore
            )
        ).first()

    def find_prompt_active_version_by_hash(
        self, project_uuid: UUID, hash: str
    ) -> PromptTable:
        """Find active version of prompt by its hash"""
        record_table = self.session.exec(
            select(self.table).where(
                self.table.project_uuid == project_uuid,
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.hash == hash,
                self.table.is_default,
                self.table.archived.is_(None),  # type: ignore
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
            self.table.archived.is_(None),  # type: ignore
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

    def archive_record_by_name(self, project_uuid: UUID, name: str) -> bool:
        """Archive records by name"""
        record_tables = self.find_prompts_by_name(project_uuid, name)
        archived_date = datetime.now(timezone.utc)
        for record_table in record_tables:
            record_table.archived = archived_date
            self.session.add(record_table)
        self.session.flush()
        return True

    def has_generations_by_name(self, project_uuid: UUID, prompt_name: str) -> bool:
        """Check if any prompts with given name have generations"""
        stmt = (
            select(self.table, GenerationTable)
            .select_from(
                join(
                    self.table,
                    GenerationTable,
                    and_(self.table.uuid == GenerationTable.prompt_uuid),
                )
            )
            .where(
                self.table.project_uuid == project_uuid,
                self.table.name == prompt_name,
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.archived.is_(None),  # type: ignore
                GenerationTable.archived.is_(None),  # type: ignore
            )
            .exists()
        )
        return self.session.exec(select(stmt)).one()

    def has_generations_by_uuid(self, project_uuid: UUID, prompt_uuid: UUID) -> bool:
        """Check if any prompts with given uuid have generations"""
        stmt = (
            select(self.table, GenerationTable)
            .select_from(
                join(
                    self.table,
                    GenerationTable,
                    and_(self.table.uuid == GenerationTable.prompt_uuid),
                )
            )
            .where(
                self.table.project_uuid == project_uuid,
                self.table.uuid == prompt_uuid,
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.archived.is_(None),  # type: ignore
                GenerationTable.archived.is_(None),  # type: ignore
            )
            .exists()
        )
        return self.session.exec(select(stmt)).one()

    def archive_record_by_uuid(self, uuid: UUID) -> bool:
        """Archive record by uuid"""
        record_table = self.find_record_by_uuid(uuid)
        record_table.archived = datetime.now(timezone.utc)
        self.session.add(record_table)
        self.session.flush()
        return True
