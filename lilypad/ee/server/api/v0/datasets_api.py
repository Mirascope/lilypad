"""API router for Oxen dataset retrieval with separate endpoints by UUID, hash, and name.
We internally use `_get_oxen_dataset_metadata` to determine the dataset path,
branch, and host. Each endpoint returns rows from an Oxen DataFrame.
"""

from __future__ import annotations

from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from oxen import DataFrame
from pydantic import BaseModel
from sqlmodel import Session

from lilypad.server._utils import match_api_key_with_project
from lilypad.server.db import get_session
from lilypad.server.services import GenerationService
from lilypad.server.settings import get_settings

from ... import validate_license

validate_license()
datasets_router = APIRouter()


class _DatasetMetadata(BaseModel):
    """Metadata for constructing the Oxen DataFrame."""

    repo: str
    branch: str
    path: str
    host: str = "hub.oxen.ai"


def _get_oxen_dataset_metadata(
    project_uuid: UUID,
    generation_uuid: UUID,
) -> _DatasetMetadata:
    """This function should return the dataset metadata needed to construct the Oxen DataFrame.
    It can consult the database or services to figure out:
      - repo
      - branch
      - path
      - host
    depending on whether we received generation_uuid, generation_hash, or generation_name.
    """
    repo_name = get_settings().oxen_repo_name
    return _DatasetMetadata(
        repo=repo_name,  # pyright: ignore [reportArgumentType]
        branch=get_settings().oxen_branch,
        host=get_settings().oxen_host,
        path=f"{str(project_uuid)}/{str(generation_uuid)}.csv",
    )


class DatasetRowsResponse(BaseModel):
    """Response model containing the rows from the Oxen DataFrame."""

    rows: list[dict[str, Any]]
    next_page: int | None = None

    @classmethod
    def from_metadata(
        cls, meta: _DatasetMetadata, page_num: int = 1
    ) -> DatasetRowsResponse | None:
        """Return a DatasetRowsResponse from the metadata."""
        try:
            df = DataFrame(
                remote=meta.repo,
                path=meta.path,
                branch=meta.branch,
                host=meta.host,
            )
        except Exception:
            return None
        # ignore the _oxen_id column
        df.filter_keys.append("_oxen_id")
        rows = df.list_page(page_num)

        response = DatasetRowsResponse(rows=rows)
        if df.page_size() > page_num:
            response.next_page = page_num + 1
        return response


@datasets_router.get(
    "/projects/{project_uuid}/datasets/{generation_uuid}",
    response_model=DatasetRowsResponse,
    summary="Get Oxen dataset rows by generation UUID",
)
async def get_dataset_rows_by_uuid(
    match_api_key: Annotated[bool, Depends(match_api_key_with_project)],
    session: Annotated[Session, Depends(get_session)],
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
    project_uuid: UUID,
    generation_uuid: UUID,
    page_num: int = 1,
) -> DatasetRowsResponse:
    """Return Oxen DataFrame rows by generation UUID.

    Args:
        match_api_key: A dependency to check the API key.
        session: A dependency to get the database session.
        generation_service: A dependency to get the GenerationService.
        project_uuid: The project UUID.
        generation_uuid: The generation UUID for the dataset.
        page_num: Which page to retrieve (default 1).

    Returns:
        A JSON response with `rows` as a list of dictionaries.
    """
    try:
        generation = generation_service.find_record_by_uuid(
            generation_uuid, project_uuid=project_uuid
        )
        meta = _get_oxen_dataset_metadata(
            project_uuid=project_uuid,
            generation_uuid=generation.uuid,  # pyright: ignore [reportArgumentType]
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not resolve metadata: {ex}",
        )

    try:
        response = DatasetRowsResponse.from_metadata(meta, page_num)
        if response:
            return response
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not Found dataset for generation_uuid: {generation_uuid}",
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing Oxen DataFrame: {ex}",
        )


@datasets_router.get(
    "/projects/{project_uuid}/datasets/hash/{generation_hash}",
    response_model=DatasetRowsResponse,
    summary="Get Oxen dataset rows by generation hash",
)
async def get_dataset_rows_by_hash(
    match_api_key: Annotated[bool, Depends(match_api_key_with_project)],
    session: Annotated[Session, Depends(get_session)],
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
    project_uuid: UUID,
    generation_hash: str,
    page_num: int = 1,
) -> DatasetRowsResponse:
    """Return Oxen DataFrame rows by generation hash.

    Args:
        match_api_key: A dependency to check the API key.
        session: A dependency to get the database session.
        generation_service: A dependency to get the GenerationService.
        project_uuid: The project UUID.
        generation_hash: The generation hash for the dataset.
        page_num: Which page to retrieve (default 1).

    Returns:
        A JSON response with `rows` as a list of dictionaries.
    """
    try:
        generation = generation_service.find_record_by_hash(
            project_uuid, generation_hash
        )
        meta = _get_oxen_dataset_metadata(
            project_uuid=project_uuid,
            generation_uuid=generation.uuid,  # pyright: ignore [reportArgumentType]
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not resolve metadata: {ex}",
        )

    try:
        response = DatasetRowsResponse.from_metadata(meta, page_num)
        if response:
            return response
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not Found dataset for generation_hash: {generation_hash}",
        )
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing Oxen DataFrame: {ex}",
        )


@datasets_router.get(
    "/projects/{project_uuid}/datasets/names/{generation_name}",
    response_model=DatasetRowsResponse,
    summary="Get Oxen dataset rows by generation name",
)
async def get_dataset_rows_by_name(
    match_api_key: Annotated[bool, Depends(match_api_key_with_project)],
    session: Annotated[Session, Depends(get_session)],
    generation_service: Annotated[GenerationService, Depends(GenerationService)],
    project_uuid: UUID,
    generation_name: str,
    page_num: int = 1,
) -> DatasetRowsResponse:
    """Return Oxen DataFrame rows by generation name.

    Args:
        match_api_key: A dependency to check the API key.
        session: A dependency to get the database session.
        generation_service: A dependency to get the GenerationService.
        project_uuid: The project UUID.
        generation_name: The generation name for the dataset.
        page_num: Which page to retrieve (default 1).

    Returns:
        A JSON response with `rows` as a list of dictionaries.
    """
    try:
        generations = generation_service.get_generations_by_name_desc_created_at(
            project_uuid, generation_name
        )
        if not generations:
            raise ValueError("No generations found by name.")
        metas = [
            _get_oxen_dataset_metadata(
                project_uuid=project_uuid,
                generation_uuid=generation.uuid,  # pyright: ignore [reportArgumentType]
            )
            for generation in generations
        ]
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not resolve metadata: {ex}",
        )

    try:
        rows = [
            row
            for meta in metas
            if (datasets := DatasetRowsResponse.from_metadata(meta, page_num))
            for row in datasets.rows
        ]
        return DatasetRowsResponse(rows=rows)
    except Exception as ex:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error initializing Oxen DataFrame: {ex}",
        )
