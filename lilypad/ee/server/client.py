"""The `lilypad` API client."""

from typing import Any, Literal, TypeVar

from pydantic import BaseModel, Field

from ...server.client import LilypadClient as _LilypadClient

_R = TypeVar("_R", bound=BaseModel)


class NotFoundError(Exception):
    """Raised when an API response has a status code of 404."""

    status_code: Literal[404] = 404


class APIConnectionError(Exception):
    """Raised when an API connection error occurs."""

    ...


# -----------------------------------------------------
# Pydantic models representing the Oxen-style response
# -----------------------------------------------------

# 1) The nested classes (similar to your server definitions).
class CommitModel(BaseModel):
    author: str
    email: str
    id: str
    message: str
    parent_ids: list[str] = Field(default_factory=list)
    root_hash: Any | None = None
    timestamp: str

class DFSchemaField(BaseModel):
    changes: Any | None = None
    dtype: str
    metadata: Any | None = None
    name: str

class DFSchema(BaseModel):
    fields: list[DFSchemaField]
    hash: str
    metadata: Any | None = None

class SizeModel(BaseModel):
    height: int
    width: int

class SourceModel(BaseModel):
    schema: DFSchema
    size: SizeModel

class PaginationModel(BaseModel):
    page_number: int
    page_size: int
    total_entries: int
    total_pages: int

class RowDataModel(BaseModel):
    id: str
    text: str
    title: str
    url: str

class DataFrameViewOptsModel(BaseModel):
    name: str
    value: Any | None = None  # could be bool, str, etc.

class DataFrameViewModel(BaseModel):
    data: list[RowDataModel]
    opts: list[DataFrameViewOptsModel]
    pagination: PaginationModel
    schema: DFSchema
    size: SizeModel

class DataFrameModel(BaseModel):
    source: SourceModel
    view: DataFrameViewModel

class RequestParamsModel(BaseModel):
    namespace: str
    repo_name: str
    resource: list[str]

class ResourceInfoModel(BaseModel):
    path: str
    version: str

# 2) The top-level response for /datasets.
class OxenDatasetResponse(BaseModel):
    commit: CommitModel
    data_frame: DataFrameModel
    derived_resource: Any | None
    oxen_version: str
    request_params: RequestParamsModel
    resource: ResourceInfoModel
    status: str
    status_message: str


class LilypadClient(_LilypadClient):
    """A client for the Lilypad ee API."""

    def get_dataset_rows(
        self,
        generation_uuid: str | None = None,
        generation_name: str | None = None,
        page_num: int = 1,
        page_size: int = 50,
    ) -> OxenDatasetResponse:
        """Fetch a dataset for a given generation, receiving Oxen-style JSON.

        Returns:
            An OxenDatasetResponse object, which includes commit info, data_frame, etc.
            The actual row data is in data_frame.view.data
        """
        if not self.project_uuid:
            raise ValueError("No project_uuid is set in LilypadClient (cannot fetch dataset).")

        params: dict[str, Any] = {}
        if generation_uuid:
            params["generation_uuid"] = generation_uuid
        if generation_name:
            params["generation_name"] = generation_name
        params["page_num"] = page_num
        params["page_size"] = page_size

        # Use our OxenDatasetResponse as the response_model so it's validated
        result = self._request(
            method="GET",
            endpoint=f"/v0/projects/{self.project_uuid}/datasets",
            response_model=OxenDatasetResponse,
            params=params,
        )
        # now result is an OxenDatasetResponse pydantic object
        return result
