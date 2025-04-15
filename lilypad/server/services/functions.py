"""The `FunctionService` class for functions."""

from collections.abc import Sequence
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import and_, asc, desc, func, select

from ..models import FunctionTable
from ..schemas import FunctionCreate
from .base_organization import BaseOrganizationService


class FunctionService(BaseOrganizationService[FunctionTable, FunctionCreate]):
    """The service class for functions."""

    table: type[FunctionTable] = FunctionTable
    create_model: type[FunctionCreate] = FunctionCreate

    def find_latest_function_by_name(
        self, project_uuid: UUID, name: str
    ) -> FunctionTable | None:
        """Find the latest version of a function by name.

        This performs sorting at the database level for better performance.

        Args:
            project_uuid: The project UUID
            name: The function name

        Returns:
            The latest version of the function or None if not found
        """
        return self.session.exec(
            select(self.table)
            .where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.name == name,
                self.table.archived.is_(None),  # type: ignore
            )
            .order_by(desc(self.table.version_num))
            .limit(1)
        ).first()

    def find_functions_by_name(
        self, project_uuid: UUID, name: str
    ) -> Sequence[FunctionTable]:
        """Find record by uuid"""
        record_tables = self.session.exec(
            select(self.table)
            .where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.name == name,
                self.table.archived.is_(None),  # type: ignore
            )
            .order_by(asc(self.table.version_num))
        ).all()
        return record_tables

    def check_duplicate_managed_function(
        self, project_uuid: UUID, function_create: FunctionCreate
    ) -> FunctionTable | None:
        """Find duplicate function by call params"""
        return self.session.exec(
            select(self.table).where(
                self.table.project_uuid == project_uuid,
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.hash == function_create.hash,
                self.table.prompt_template == function_create.prompt_template,
                self.table.call_params == function_create.call_params,
                self.table.arg_types == function_create.arg_types,
                self.table.provider == function_create.provider,
                self.table.model == function_create.model,
                self.table.archived.is_(None),  # type: ignore
            )
        ).first()

    def find_functions_by_version(
        self, project_uuid: UUID, name: str, version_num: int
    ) -> FunctionTable:
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

    def find_functions_by_signature(
        self, project_uuid: UUID, signature: str
    ) -> Sequence[FunctionTable]:
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

    def find_unique_function_names(self, project_uuid: UUID) -> Sequence[FunctionTable]:
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
        """Get the next version number for a function with this name."""
        count = self.session.exec(
            select(func.count()).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.name == name,
            )
        ).one()

        return count + 1

    def find_unique_function_names_by_project_uuid(
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

    def find_record_by_hash(self, project_uuid: UUID, hash: str) -> FunctionTable:
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
        record_tables = self.find_functions_by_name(project_uuid, name)
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

    def get_functions_by_name_desc_created_at(
        self, project_uuid: UUID, name: str
    ) -> Sequence[FunctionTable]:
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
