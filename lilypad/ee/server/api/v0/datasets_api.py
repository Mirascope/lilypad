"""API router for Oxen dataset retrieval with separate endpoints by UUID, hash, and name.
We internally use `_get_oxen_dataset_metadata` to determine the dataset path,
branch, and host. Each endpoint returns rows from an Oxen DataFrame.
"""

import io
import json
import math
import os
from collections.abc import Sequence
from typing import Annotated, Optional, cast
from uuid import UUID

import oxen
import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, status
from oxen import RemoteRepo, Workspace
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

PAGE_SIZE: int = 100


class _DatasetMetadata(BaseModel):
    """Metadata for constructing the Oxen DataFrame."""

    repo: RemoteRepo | Workspace | str
    branch: str
    src: str
    dist_dir: str
    host: str

    model_config = ConfigDict(arbitrary_types_allowed=True)

    @property
    def namespace(self) -> str:
        """Return the namespace for the dataset."""
        return self.identifier.split(":")[0]

    @property
    def repo_id(self) -> str:
        """Return the repo_id for the dataset."""
        return self.identifier.split(":")[1]

    @property
    def identifier(self) -> str:
        """Return the identifier for the dataset."""
        if isinstance(self.repo, RemoteRepo):
            return self.repo.identifier
        elif isinstance(self.repo, Workspace):
            return self.repo._repo.identifier
        else:
            return self.repo.replace("/", ":")

    @property
    def url(self) -> str:
        """Return the URL for the dataset."""
        return f"oxen://{self.identifier}@{self.branch}/{self.dist_dir}/{self.src}"


def _get_repo(
    user: Annotated[UserPublic, Depends(get_current_user)],
) -> RemoteRepo:
    settings = get_settings()
    if settings.oxen_api_key:
        config_auth(settings.oxen_api_key, host=settings.oxen_host)
    repo = RemoteRepo(
        f"{settings.oxen_repo_name}/{user.active_organization_uuid}",
        host=settings.oxen_host,
    )
    if not repo.exists():
        repo.create()
    return repo


def _get_dataset(meta: _DatasetMetadata, src: str | None = None) -> pd.DataFrame | None:
    """Get or create the Oxen DataFrame."""
    fs = oxen.OxenFS(meta.namespace, meta.repo_id)
    try:
        with fs.open(os.path.join(meta.dist_dir, meta.src), "rb") as f:
            parquet_data = cast(bytes, f.read())
    except AttributeError:
        # file not found
        return None
    buffer = io.BytesIO(parquet_data)
    df = pd.read_parquet(buffer)
    return df


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
    def from_annotation(cls, annotation: AnnotationPublic) -> "DatasetRow":
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
    ) -> Optional["DatasetRowsResponse"]:
        """Return a DatasetRowsResponse from the metadata."""
        df = _get_dataset(meta)

        if df is None:
            return None

        if "_oxen_id" in df.columns:
            df = df.drop(columns=["_oxen_id"])

        # Calculate the start and end index for the page
        start_index = (page_num - 1) * PAGE_SIZE
        end_index = start_index + PAGE_SIZE

        rows = df.iloc[start_index:end_index].to_dict(orient="records")

        dataset_rows = [
            DatasetRow(**{**row, "input": json.loads(row["input"])}) for row in rows
        ]
        response = DatasetRowsResponse(rows=dataset_rows)

        total_pages = math.ceil(len(df) / PAGE_SIZE)
        if page_num < total_pages:
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
    df = _get_dataset(meta)

    if df is None:
        df = pd.DataFrame(columns=pd.Index(list(DatasetRow.model_fields.keys())))

    for row in data:
        df.loc[len(df)] = DatasetRow.from_annotation(row).model_dump()
    df.to_parquet(meta.url, index=False)
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
