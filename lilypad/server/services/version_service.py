"""VersionService class"""

from fastapi import HTTPException, status
from sqlmodel import col, func, select

from lilypad.models import VersionCreate
from lilypad.server.models import VersionTable

from . import BaseService


class VersionService(BaseService[VersionTable, VersionCreate]):
    """VersionService class"""

    table: type[VersionTable] = VersionTable
    create_model: type[VersionCreate] = VersionCreate

    def find_non_synced_version_by_hash(
        self, project_id: int, function_hash: str
    ) -> VersionTable | None:
        """Find existing record"""
        existing_version = self.session.exec(
            select(self.table).where(
                self.table.project_id == project_id,
                self.table.fn_params_hash.is_(None),  # type: ignore
                self.table.llm_function_hash == function_hash,
            )
        ).first()
        return existing_version

    def find_synced_active_version(
        self, project_id: int, function_hash: str
    ) -> VersionTable:
        """Find the active version for synced function"""
        version = self.session.exec(
            select(VersionTable).where(
                VersionTable.project_id == project_id,
                VersionTable.is_active,
                VersionTable.llm_function_hash == function_hash,
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
        """Change the active version"""
        active_version = self.find_synced_active_version(
            project_id, new_active_version.llm_function_hash
        )
        if active_version.id == new_active_version.id:
            return active_version
        active_version.is_active = False
        new_active_version.is_active = True
        self.session.add(active_version)
        self.session.add(new_active_version)
        self.session.flush()
        return new_active_version

    def find_synced_verion_by_hashes(
        self, llm_fn_hash: str, fn_params_hash: str
    ) -> VersionTable | None:
        """Find existing record by hashes"""
        existing_version = self.session.exec(
            select(VersionTable).where(
                VersionTable.llm_function_hash == llm_fn_hash,
                VersionTable.fn_params_hash == fn_params_hash,
            )
        ).first()
        return existing_version

    def get_latest_version_count(self, project_id: int, function_name: str) -> int:
        """Get the latest version count"""
        return self.session.exec(
            select(func.count(col(VersionTable.id))).where(
                VersionTable.project_id == project_id,
                VersionTable.function_name == function_name,
            )
        ).one()

    def is_first_prompt_template(self, project_id: int, function_hash: str) -> bool:
        """Get the latest version count"""
        number_of_prompt_templates_for_llm_function = self.session.exec(
            select(func.count(col(VersionTable.id))).where(
                VersionTable.project_id == project_id,
                VersionTable.llm_function_hash == function_hash,
            )
        ).one()
        return not number_of_prompt_templates_for_llm_function > 0
