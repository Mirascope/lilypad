"""Service for managing deployments."""

from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlmodel import desc, select

from lilypad.ee.server.models.deployments import DeploymentTable
from lilypad.ee.server.schemas.deployments import DeploymentCreate
from lilypad.server.models import GenerationTable
from lilypad.server.services.base_organization import BaseOrganizationService


class DeploymentService(BaseOrganizationService[DeploymentTable, DeploymentCreate]):
    """Service for managing deployments."""

    table: type[DeploymentTable] = DeploymentTable
    create_model: type[DeploymentCreate] = DeploymentCreate

    def deploy_generation(
        self, environment_uuid: UUID, generation_uuid: UUID, notes: str | None = None
    ) -> DeploymentTable:
        """Deploy a generation to an environment.

        This creates a new active deployment and deactivates any existing ones.
        """
        # Deactivate any existing active deployments for this environment
        existing_deployments = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.environment_uuid == environment_uuid,
                self.table.is_active is True,
            )
        ).all()

        for deployment in existing_deployments:
            deployment.is_active = False
            self.session.add(deployment)

        # Get the latest revision number
        latest = self.session.exec(
            select(self.table)
            .where(self.table.environment_uuid == environment_uuid)
            .order_by(desc(self.table.revision))
        ).first()

        revision = (latest.revision + 1) if latest else 1

        # Create new active deployment
        deployment = self.create_record(
            DeploymentCreate(
                environment_uuid=environment_uuid,
                generation_uuid=generation_uuid,
                is_active=True,
                revision=revision,
                notes=notes,
            )
        )

        return deployment

    def get_active_deployment(self, environment_uuid: UUID) -> DeploymentTable:
        """Get the active deployment for an environment."""
        deployment = self.session.exec(
            select(self.table).where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.environment_uuid == environment_uuid,
                self.table.is_active is True,
            )
        ).first()

        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No active deployment found for this environment",
            )

        return deployment

    def get_generation_for_environment(self, environment_uuid: UUID) -> GenerationTable:
        """Get the currently active generation for an environment."""
        deployment = self.get_active_deployment(environment_uuid)

        generation = self.session.exec(
            select(GenerationTable).where(
                GenerationTable.uuid == deployment.generation_uuid
            )
        ).first()

        if not generation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Generation not found for this deployment",
            )

        return generation

    def get_deployment_history(
        self, environment_uuid: UUID
    ) -> Sequence[DeploymentTable]:
        """Get deployment history for an environment."""
        return self.session.exec(
            select(self.table)
            .where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.environment_uuid == environment_uuid,
            )
            .order_by(desc(self.table.revision))
        ).all()
