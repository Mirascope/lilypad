"""
API router for Oxen dataset retrieval.

"""

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session

from oxen import DataFrame

from ..._utils import match_api_key_with_project
from ...db import get_session
from ...services import DatasetsService

datasets_router = APIRouter()

class _DatasetMetadata(BaseModel):
    repo_url: str
    branch: str
    path: str
    host: str = "hub.oxen.ai"

def _get_oxen_dataset_metadata(generation_uuid: str | None) -> _DatasetMetadata:
    ...
    # This function should return the metadata for the given generation
    # using the rules of path and branch, etc.

class DatasetRowsResponse(BaseModel):
    """Response model containing the rows from the Oxen DataFrame."""

    rows: list[dict[str, Any]]


@datasets_router.get(
    "/projects/{project_uuid}/datasets",
    response_model=DatasetRowsResponse,
    summary="Get Oxen dataset rows by generation",
)
async def get_dataset_rows(
    match_api_key: Annotated[bool, Depends(match_api_key_with_project)],
    session: Annotated[Session, Depends(get_session)],
    project_uuid: UUID,
    datasets_service: Annotated[DatasetsService, Depends(DatasetsService)],
    page_num: int = 1,
    page_size: int = 50,
    generation_uuid: str | None = None,
    generation_name: str | None = None,
) -> DatasetRowsResponse:
    """
    Return actual rows from an Oxen DataFrame for a given generation.

    Args:
        project_uuid: The project containing the generation/dataset.
        page_num: (Optional) The page to list. Defaults to 1.
        page_size: (Optional) The number of rows per page. Defaults to 50.
        generation_uuid: (Optional) The generation UUID.
        generation_name: (Optional) The generation name.

    Returns:
        A JSON response with `rows` as a list of dictionaries, each representing a row.
    """

    # Get the Oxen metadata for the generation
    # TODO: Get generation_uuid from the query params or the path

    meta = _get_oxen_dataset_metadata(generation_uuid)
    try:
        df = DataFrame(
            remote=meta.repo_url,
            path=meta.path,
            branch=meta.branch,
            host=meta.host,
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing Oxen DataFrame: {ex}"
        )

    rows = df.list_page(page_num)

    return DatasetRowsResponse(rows=rows)
