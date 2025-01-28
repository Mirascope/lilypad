"""DatasetsService: resolves Generation -> Oxen repository info."""

from typing import Annotated, Any
from uuid import UUID

from fastapi import Depends
from sqlmodel import Session

from ..db import get_session
from ..models.generations import GenerationTable
from .generations import GenerationService


class DatasetsService:
    """Service to handle how a generation maps to Oxen metadata."""

    def __init__(
        self,
        session: Annotated[Session, Depends(get_session)],
        generation_service: Annotated[GenerationService, Depends(GenerationService)],
    ) -> None:
        self.session = session
        self.generation_service = generation_service

    def find_oxen_metadata(
        self,
        project_uuid: UUID,
        generation_uuid: str | None = None,
        generation_name: str | None = None,
    ) -> dict[str, Any] | None:
        """Look up the associated Oxen metadata (repo_url, branch, path)
        for the specified generation.
        """
        generation: GenerationTable | None = None

        # 1. Find the matching generation
        if generation_uuid:
            try:
                gen_uuid = UUID(generation_uuid)
                generation = self.generation_service.find_record_by_uuid(
                    gen_uuid, project_uuid=project_uuid
                )
            except ValueError:
                return None
        elif generation_name:
            gens = self.generation_service.find_generations_by_name(
                project_uuid=project_uuid, name=generation_name
            )
            if not gens:
                return None
            # For example, pick the latest or the first
            generation = gens[0]

        if not generation:
            return None

        # 2. Extract the Oxen repository info
        #    We assume these columns exist in GenerationTable for demonstration
        if (
            not generation.oxen_repo_url
            or not generation.oxen_branch
            or not generation.oxen_path
        ):
            return None

        return {
            "repo_url": generation.oxen_repo_url,
            "branch": generation.oxen_branch,
            "path": generation.oxen_path,
        }
