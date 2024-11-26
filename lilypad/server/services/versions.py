"""The `VersionService` class for versions."""

from collections.abc import Sequence

from fastapi import HTTPException, status
from sqlmodel import col, func, select

from ..models import VersionCreate, VersionTable
from .base import BaseService


class VersionService(BaseService[VersionTable, VersionCreate]):
    """The service class for versions."""

    table: type[VersionTable] = VersionTable
    create_model: type[VersionCreate] = VersionCreate

    def find_versions_by_function_name(
        self, project_id: int, function_name: str
    ) -> Sequence[VersionTable]:
        """Find versions by function name"""
        return self.session.exec(
            select(self.table).where(
                self.table.project_id == project_id,
                self.table.function_name == function_name,
            )
        ).all()

    def find_prompt_version_by_id(
        self, project_id: int, function_id: int, prompt_id: int
    ) -> VersionTable | None:
        """Find function version by hash"""
        return self.session.exec(
            select(self.table).where(
                self.table.project_id == project_id,
                self.table.function_id == function_id,
                self.table.prompt_id == prompt_id,
            )
        ).first()

    def find_function_version_by_hash(
        self, project_id: int, hash: str
    ) -> VersionTable | None:
        """Find function version by hash"""
        return self.session.exec(
            select(self.table).where(
                self.table.project_id == project_id,
                self.table.prompt_hash.is_(None),  # pyright: ignore [reportAttributeAccessIssue, reportOptionalMemberAccess]
                self.table.function_hash == hash,
            )
        ).first()

    def find_prompt_versions_by_hash(
        self, project_id: int, function_hash: str, prompt_hash: str
    ) -> Sequence[VersionTable]:
        """Find prompt versions by hash

        We can have multiple versions if the prompt_hash is the same, but call params
        are different.
        """
        return self.session.exec(
            select(self.table).where(
                self.table.project_id == project_id,
                self.table.function_hash == function_hash,
                self.table.prompt_hash == prompt_hash,
            )
        ).all()

    def find_prompt_active_version(
        self, project_id: int, function_hash: str
    ) -> VersionTable:
        """Find the active version for a prompt"""
        version = self.session.exec(
            select(VersionTable).where(
                VersionTable.project_id == project_id,
                VersionTable.is_active,
                VersionTable.function_hash == function_hash,
            )
        ).first()

        if not version:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Active version not found"
            )
        return version

    def change_active_version(
        self, project_id: int, new_active_version: VersionTable
    ) -> VersionTable:
        """Change the active version for a function, deactivating any currently active versions.

        Args:
            project_id: The project ID
            new_active_version: The version to make active

        Returns:
            The newly activated version
        """
        # Deactivate all currently active versions for the same function
        stmt = select(VersionTable).where(
            VersionTable.project_id == project_id,
            VersionTable.function_name == new_active_version.function_name,
            VersionTable.is_active,
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

    def get_function_version_count(self, project_id: int, function_name: str) -> int:
        """Get the count of function versions"""
        return self.session.exec(
            select(func.count(col(VersionTable.id))).where(
                VersionTable.project_id == project_id,
                VersionTable.function_name == function_name,
            )
        ).one()
