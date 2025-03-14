"""The `GenerationService` class for generations."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import desc, select

from ....server.models import GenerationTable
from ....server.schemas import GenerationCreate
from ....server.services.generations import GenerationService as _GenerationService


class GenerationService(_GenerationService):
    """The service ee class for generations."""

    table: type[GenerationTable] = GenerationTable
    create_model: type[GenerationCreate] = GenerationCreate

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

    def find_latest_generation_by_name(
        self, project_uuid: UUID, name: str
    ) -> GenerationTable | None:
        """Find the latest version of a generation by name.

        This performs sorting at the database level for better performance.

        Args:
            project_uuid: The project UUID
            name: The generation name

        Returns:
            The latest version of the generation or None if not found
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
