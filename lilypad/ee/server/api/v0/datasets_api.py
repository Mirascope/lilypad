"""API router for Oxen dataset retrieval with separate endpoints by UUID, hash, and name.
We internally use `_get_oxen_dataset_metadata` to determine the dataset path,
branch, and host. Each endpoint returns rows from an Oxen DataFrame.
"""

from __future__ import annotations

import json
import os
import tempfile
from collections.abc import Sequence
from typing import Annotated
from uuid import UUID

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from oxen import DataFrame, RemoteRepo, Workspace
from oxen.auth import config_auth
from pydantic import BaseModel, ConfigDict, field_serializer

from lilypad.server.settings import get_settings

from .....server._utils import get_current_user, validate_api_key_project_no_strict
from .....server.schemas.users import UserPublic
from ....validate import Tier
from ...models.annotations import EvaluationType, Label
from ...require_license import require_license
from ...schemas.annotations import AnnotationPublic
from ...services.annotations_service import AnnotationService

datasets_router = APIRouter()


def _get_repo(
    user: Annotated[UserPublic, Depends(get_current_user)],
) -> RemoteRepo:
    settings = get_settings()
    if not settings.oxen_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Oxen API key",
        )
    config_auth(settings.oxen_api_key, host=settings.oxen_host)
    repo = RemoteRepo(f"{settings.oxen_repo_name}/{user.active_organization_uuid}")
    if not repo.exists():
        repo.create()
    return repo


def _get_or_create_dataset(
    meta: _DatasetMetadata, src: str | None = None
) -> tuple[DataFrame, bool]:
    """Get or create the Oxen DataFrame."""
    try:
        # Eventually replace this with df.exists() once it's implemented
        return DataFrame(
            remote=meta.repo,
            path=os.path.join(meta.dist_dir, meta.src),
            branch=meta.branch,
            host=meta.host,
        ), True
    except Exception:
        if isinstance(meta.repo, RemoteRepo):
            meta.repo.add(src or meta.src, dst_dir=meta.dist_dir)
            meta.repo.commit("initial commit")
    return DataFrame(
        remote=meta.repo,
        path=os.path.join(meta.dist_dir, meta.src),
        branch=meta.branch,
        host=meta.host,
    ), False


class _DatasetMetadata(BaseModel):
    """Metadata for constructing the Oxen DataFrame."""

    repo: RemoteRepo | Workspace | str
    branch: str
    src: str
    dist_dir: str
    host: str

    model_config = ConfigDict(arbitrary_types_allowed=True)


def _get_oxen_dataset_metadata(
    project_uuid: UUID,
    generation_uuid: UUID,
    repo: Annotated[RemoteRepo, Depends(_get_repo)],
) -> _DatasetMetadata:
    """This function should return the dataset metadata needed to construct the Oxen DataFrame.
    It can consult the database or services to figure out:
      - repo
      - branch
      - path
      - host
    depending on whether we received generation_uuid, generation_hash, or generation_name.
    """
    dist_dir = f"{str(project_uuid)}/{str(generation_uuid)}"
    src = "data.parquet"
    return _DatasetMetadata(
        repo=repo,
        branch=get_settings().oxen_branch,
        host=get_settings().oxen_host,
        dist_dir=dist_dir,
        src=src,
    )


class DatasetRow(BaseModel):
    """Dataset row model."""

    uuid: UUID
    input: dict[str, str] | None
    output: str
    label: Label | None
    reasoning: str | None
    type: EvaluationType | None

    @field_serializer("uuid")
    def serialize_uuid(self, uuid: UUID) -> str:
        """Serialize the UUID."""
        return str(uuid)

    @field_serializer("input")
    def serialize_input(self, input: dict[str, str] | None) -> str | None:
        """Serialize the input."""
        if input:
            return json.dumps(input)
        return None

    @classmethod
    def from_annotation(cls, annotation: AnnotationPublic) -> DatasetRow:
        """Return a DatasetRow from an AnnotationPublic model."""
        return DatasetRow(
            uuid=annotation.uuid,
            input=annotation.span.arg_values,
            output=annotation.span.output or "",
            label=annotation.label,
            reasoning=annotation.reasoning,
            type=annotation.type,
        )


class DatasetRowsResponse(BaseModel):
    """Response model containing the rows from the Oxen DataFrame."""

    rows: list[DatasetRow]
    next_page: int | None = None

    @classmethod
    def from_metadata(
        cls, meta: _DatasetMetadata, page_num: int = 1
    ) -> DatasetRowsResponse | None:
        """Return a DatasetRowsResponse from the metadata."""
        df, _ = _get_or_create_dataset(meta)
        # ignore the _oxen_id column
        df.filter_keys.append("_oxen_id")
        rows = df.list_page(page_num)
        dataset_rows = [
            DatasetRow(**{**row, "input": json.loads(row["input"])}) for row in rows
        ]
        response = DatasetRowsResponse(rows=dataset_rows)
        if df.page_size() > page_num:
            response.next_page = page_num + 1
        return response


@datasets_router.post(
    "/projects/{project_uuid}/generations/{generation_uuid}/datasets",
)
@require_license(tier=Tier.ENTERPRISE)
async def create_dataset_rows_by_uuid(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_no_strict)],
    meta: Annotated[_DatasetMetadata, Depends(_get_oxen_dataset_metadata)],
    annotation_service: Annotated[AnnotationService, Depends(AnnotationService)],
    data: Sequence[AnnotationPublic],
) -> bool:
    """Create Oxen DataFrame rows by generation UUID.

    Args:
        match_api_key: A dependency to check the API key.
        meta: A dependency to get the dataset metadata.
        annotation_service: A dependency to get the AnnotationService.
        data: A list of AnnotationPublic models.

    Returns:
        A boolean indicating success.
    """
    data_dicts = [DatasetRow.from_annotation(row).model_dump() for row in data]
    df = pd.DataFrame(data_dicts)
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create file path in temporary directory
        temp_file_path = os.path.join(temp_dir, meta.src)

        # Save DataFrame to Parquet in temporary directory
        df.to_parquet(temp_file_path, index=False)

        oxen_df, exists = _get_or_create_dataset(meta, temp_file_path)
        if exists:
            for row in data:
                oxen_df.insert_row(DatasetRow.from_annotation(row).model_dump())
            oxen_df.commit("add row(s)")
        annotation_service.delete_records_by_uuids([row.uuid for row in data])
        return True


@datasets_router.get(
    "/projects/{project_uuid}/generations/{generation_uuid}/datasets",
    response_model=DatasetRowsResponse,
    summary="Get Oxen dataset rows by generation UUID",
)
@require_license(tier=Tier.ENTERPRISE)
async def get_dataset_rows_by_uuid(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_no_strict)],
    meta: Annotated[_DatasetMetadata, Depends(_get_oxen_dataset_metadata)],
    generation_uuid: UUID,
    page_num: int = 1,
) -> DatasetRowsResponse:
    """Return Oxen DataFrame rows by generation UUID.

    Args:
        match_api_key: A dependency to check the API key.
        meta: A dependency to get the dataset metadata.
        generation_uuid: The generation UUID for the dataset.
        page_num: Which page to retrieve (default 1).

    Returns:
        A JSON response with `rows` as a list of dictionaries.
    """
    try:
        response = DatasetRowsResponse.from_metadata(meta, page_num)
        if response:
            return response
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Not Found dataset for generation_uuid: {generation_uuid}",
        )
    except Exception:
        return DatasetRowsResponse(rows=[], next_page=None)


@datasets_router.get(
    "/projects/{project_uuid}/datasets/hash/{generation_hash}",
    response_model=DatasetRowsResponse,
    summary="Get Oxen dataset rows by generation hash",
)
@require_license(tier=Tier.ENTERPRISE)
async def get_dataset_rows_by_hash(
    match_api_key: Annotated[bool, Depends(validate_api_key_project_no_strict)],
    meta: Annotated[_DatasetMetadata, Depends(_get_oxen_dataset_metadata)],
    generation_hash: str,
    page_num: int = 1,
) -> DatasetRowsResponse:
    """Return Oxen DataFrame rows by generation hash.

    Args:
        match_api_key: A dependency to check the API key.
        meta: A dependency to get the dataset metadata.
        generation_hash: The generation hash for the dataset.
        page_num: Which page to retrieve (default 1).

    Returns:
        A JSON response with `rows` as a list of dictionaries.
    """
    # TODO: We do not currently save the hash in dataset
    raise NotImplementedError("Not implemented yet.")


# @datasets_router.get(
#     "/projects/{project_uuid}/datasets/names/{generation_name}",
#     response_model=DatasetRowsResponse,
#     summary="Get Oxen dataset rows by generation name",
# )
# async def get_dataset_rows_by_name(
#     match_api_key: Annotated[bool, Depends(validate_api_key_project_no_strict)],
#     generation_service: Annotated[GenerationService, Depends(GenerationService)],
#     repo: Annotated[RemoteRepo, Depends(_get_repo)],
#     project_uuid: UUID,
#     generation_name: str,
#     page_num: int = 1,
# ) -> DatasetRowsResponse:
#     """Return Oxen DataFrame rows by generation name.

#     Args:
#         match_api_key: A dependency to check the API key.
#         generation_service: A dependency to get the GenerationService.
#         repo: A dependency to get the RemoteRepo.
#         project_uuid: The project UUID.
#         generation_name: The generation name for the dataset.
#         page_num: Which page to retrieve (default 1).

#     Returns:
#         A JSON response with `rows` as a list of dictionaries.
#     """
#     try:
#         generations = generation_service.get_generations_by_name_desc_created_at(
#             project_uuid, generation_name
#         )
#         if not generations:
#             raise ValueError("No generations found by name.")
#         metas = [
#             _get_oxen_dataset_metadata(
#                 project_uuid=project_uuid,
#                 generation_uuid=generation.uuid,  # pyright: ignore [reportArgumentType]
#                 repo=repo,
#             )
#             for generation in generations
#         ]
#     except Exception as ex:
#         raise HTTPException(
#             status_code=status.HTTP_400_BAD_REQUEST,
#             detail=f"Could not resolve metadata: {ex}",
#         )

#     try:
#         rows = [
#             row
#             for meta in metas
#             if (datasets := DatasetRowsResponse.from_metadata(meta, page_num))
#             for row in datasets.rows
#         ]
#         return DatasetRowsResponse(rows=rows)
#     except Exception as ex:
#         raise HTTPException(
#             status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             detail=f"Error initializing Oxen DataFrame: {ex}",
#         )
