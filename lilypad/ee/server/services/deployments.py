"""Service for managing deployments."""

import time
from collections.abc import Sequence
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlmodel import desc, select

from ....server.models import GenerationTable
from ....server.services.base_organization import BaseOrganizationService
from ..models import DeploymentTable
from ..schemas import DeploymentCreate


class DeploymentService(BaseOrganizationService[DeploymentTable, DeploymentCreate]):
    """Service for managing deployments."""

    table: type[DeploymentTable] = DeploymentTable
    create_model: type[DeploymentCreate] = DeploymentCreate

    def deploy_generation(
        self, environment_uuid: UUID, generation_uuid: UUID, notes: str | None = None
    ) -> DeploymentTable:
        """Deploy a generation to an environment using a transaction with row-level locking
        and retry mechanism to handle constraint violations (e.g., partial unique index conflicts).
        This creates a new active deployment and deactivates any existing ones.
        """
        max_retries = 3
        attempt = 0
        while attempt < max_retries:
            try:
                with self.session.begin():
                    # Deactivate any existing active deployments for this environment
                    existing_deployments = self.session.exec(
                        select(self.table).where(
                            self.table.organization_uuid
                            == self.user.active_organization_uuid,
                            self.table.environment_uuid == environment_uuid,
                            self.table.is_active is True,  # Use explicit equality check
                        )
                    ).all()

                    for deployment in existing_deployments:
                        deployment.is_active = False
                        self.session.add(deployment)

                    # Get the latest revision number with a row-level lock
                    latest = self.session.exec(
                        select(self.table)
                        .where(self.table.environment_uuid == environment_uuid)
                        .order_by(desc(self.table.version_num))
                        .with_for_update()  # Lock the row to prevent race conditions
                    ).first()

                    version_num = (latest.version_num + 1) if latest else 1

                    # Create new active deployment
                    deployment = self.create_record(
                        DeploymentCreate(
                            environment_uuid=environment_uuid,
                            generation_uuid=generation_uuid,
                            is_active=True,
                            version_num=version_num,
                            notes=notes,
                        )
                    )
                return deployment

            except IntegrityError:
                # Roll back the session and retry if a constraint violation occurs
                self.session.rollback()
                attempt += 1
                if attempt < max_retries:
                    time.sleep(0.1)

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Conflict occurred while deploying generation. Please try again.",
        )

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
            .order_by(desc(self.table.version_num))
        ).all()

    def get_specific_deployment(
        self, project_uuid: UUID, environment_uuid: UUID, generation_name: str
    ) -> DeploymentTable | None:
        """Get a specific deployment for an environment and generation combination."""
        return self.session.exec(
            select(self.table)
            .join(GenerationTable, self.table.generation)  # pyright: ignore [reportArgumentType]
            .where(
                self.table.organization_uuid == self.user.active_organization_uuid,
                self.table.environment_uuid == environment_uuid,
                self.table.project_uuid == project_uuid,
                GenerationTable.name == generation_name,
            )
            .order_by(desc(GenerationTable.version_num))
        ).first()
