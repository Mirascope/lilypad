"""API router for Oxen dataset metadata retrieval."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from ..._utils import match_api_key_with_project
from ...db import get_session
from ...services import DatasetsService

datasets_router = APIRouter()

class DatasetMeta(BaseModel):
    """Represents metadata needed to initialize an Oxen DataFrame."""

    repo_url: str
    branch: str
    path: str

@datasets_router.get(
    "/projects/{project_uuid}/datasets",
    response_model=DatasetMeta,
    summary="Get dataset metadata by generation",
)
async def get_dataset_metadata(
    match_api_key: Annotated[bool, Depends(match_api_key_with_project)],
    session: Annotated[Session, Depends(get_session)],
    project_uuid: UUID,
    datasets_service: Annotated[DatasetsService, Depends(DatasetsService)],
    generation_uuid: str | None = None,
    generation_name: str | None = None,
) -> DatasetMeta:
    """Return Oxen dataset metadata for a given generation.
    This metadata (repo_url, branch, path) allows the client
    to construct an Oxen DataFrame without downloading data locally.
    """
    # Validate query params
    if not generation_uuid and not generation_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Must provide either 'generation_uuid' or 'generation_name'."
        )

    # Delegate to service for resolution
    meta = datasets_service.find_oxen_metadata(
        project_uuid=project_uuid,
        generation_uuid=generation_uuid,
        generation_name=generation_name,
    )
    if not meta:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No matching generation or Oxen metadata found."
        )

    return DatasetMeta(**meta)
