"""The `GenerationService` class for generations."""

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import desc
from sqlmodel import and_, func, select

from ..models import GenerationTable
from ..schemas import GenerationCreate
from .base_organization import BaseOrganizationService


class GenerationService(BaseOrganizationService[GenerationTable, GenerationCreate]):
    """The service class for generations."""

    table: type[GenerationTable] = GenerationTable
    create_model: type[GenerationCreate] = GenerationCreate

    def find_generations_by_name(
        self, project_uuid: UUID, name: str
    ) -> Sequence[GenerationTable]:
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

    def check_duplicate_managed_generation(
        self, project_uuid: UUID, generation_create: GenerationCreate
    ) -> GenerationTable | None:
        """Find duplicate generation by call params"""
        return self.session.exec(
            select(self.table).where(
                self.table.project_uuid == project_uuid,
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.hash == generation_create.hash,
                self.table.call_params == generation_create.call_params,
                self.table.arg_types == generation_create.arg_types,
                self.table.archived.is_(None),  # type: ignore
            )
        ).first()

    def find_generations_by_signature(
        self, project_uuid: UUID, signature: str
    ) -> Sequence[GenerationTable]:
        """Find record by signature."""
        record_tables = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.signature == signature,
                self.table.archived.is_(None),  # type: ignore
            )
        ).all()
        return record_tables

    def find_generations_by_version(
        self, project_uuid: UUID, name: str, version_num: int
    ) -> GenerationTable:
        """Find record by version"""
        record_table = self.session.exec(
            select(self.table)
            .where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.name == name,
                self.table.version_num == version_num,
                self.table.archived.is_(None),  # type: ignore
            )
            .order_by(self.table.version_num.asc())  # type: ignore
        ).first()
        if not record_table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record for {self.table.__tablename__} not found",
            )
        return record_table

    def find_unique_generation_names(
        self, project_uuid: UUID
    ) -> Sequence[GenerationTable]:
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
                self.table.archived.is_(None),  # type: ignore
            )
            .distinct()
        ).all()
        return record_tables

    def find_record_by_hash(self, project_uuid: UUID, hash: str) -> GenerationTable:
        """Find record by hash"""
        record_table = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.hash == hash,
                self.table.archived.is_(None),  # type: ignore
            )
        ).first()
        if not record_table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Record for {self.table.__tablename__} not found",
            )
        return record_table

    def archive_record_by_name(self, project_uuid: UUID, name: str) -> bool:
        """Archive records by name"""
        record_tables = self.find_generations_by_name(project_uuid, name)
        archived_date = datetime.now(timezone.utc)
        for record_table in record_tables:
            record_table.archived = archived_date
            self.session.add(record_table)
        self.session.flush()
        return True

    def archive_record_by_uuid(self, uuid: UUID) -> bool:
        """Archive record by uuid"""
        record_table = self.find_record_by_uuid(uuid)
        record_table.archived = datetime.now(timezone.utc)
        self.session.add(record_table)
        self.session.flush()
        return True

    def get_generations_by_name_desc_created_at(
        self, project_uuid: UUID, name: str
    ) -> Sequence[GenerationTable]:
        """Find record by name, ordered by created_at descending."""
        record_tables = (
            self.session.exec(
                select(self.table)
                .where(
                    self.table.organization_uuid == self.user.active_organization_uuid,
                    self.table.project_uuid == project_uuid,
                    self.table.name == name,
                    self.table.archived.is_(None),  # type: ignore
                )
                .order_by(desc(self.table.created_at), self.table.version_num.asc())  # pyright: ignore [reportOptionalMemberAccess, reportAttributeAccessIssue, reportArgumentType]
            )
        ).all()

        return record_tables
