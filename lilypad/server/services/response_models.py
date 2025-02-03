"""The `ResponseModelService` class for response models."""

from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import select

from ..models.response_models import ResponseModelTable
from ..schemas.response_models import ResponseModelCreate
from .base_organization import BaseOrganizationService


class ResponseModelService(
    BaseOrganizationService[ResponseModelTable, ResponseModelCreate]
):
    """The service class for response models."""

    table: type[ResponseModelTable] = ResponseModelTable
    create_model: type[ResponseModelCreate] = ResponseModelCreate

    def find_response_model_active_version_by_hash(
        self, project_uuid: UUID, response_model_hash: str
    ) -> ResponseModelTable:
        """Find active version of response model by its hash."""
        record_table = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.project_uuid == project_uuid,
                self.table.hash == response_model_hash,
                self.table.is_active,
            )
        ).first()
        if not record_table:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Active version for hash '{response_model_hash}' not found.",
            )
        return record_table

    def change_active_version(
        self, project_uuid: UUID, new_active_version: ResponseModelTable
    ) -> ResponseModelTable:
        """Change active version of response model."""
        stmt = select(self.table).where(
            self.table.project_uuid == project_uuid,
            self.table.name == new_active_version.name,
            self.table.is_active,
        )
        current_active_versions = self.session.exec(stmt).all()

        for version in current_active_versions:
            version.is_active = False
            self.session.add(version)

        new_active_version.is_active = True
        self.session.add(new_active_version)
        self.session.flush()
        self.session.refresh(new_active_version)
        return new_active_version
