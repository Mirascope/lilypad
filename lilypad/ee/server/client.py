"""The `lilypad` API client."""

from typing import Any, Literal, TypeVar

from pydantic import BaseModel, Field

from ...server.client import LilypadClient as _LilypadClient
from ..evals.datasets import DataFrame, Dataset

_R = TypeVar("_R", bound=BaseModel)


class NotFoundError(Exception):
    """Raised when an API response has a status code of 404."""

    status_code: Literal[404] = 404


class APIConnectionError(Exception):
    """Raised when an API connection error occurs."""

    ...


class CommitModel(BaseModel):
    """Model for the commit in the response."""

    author: str
    email: str
    id: str
    message: str
    parent_ids: list[str] = Field(default_factory=list)
    root_hash: Any | None = None
    timestamp: str


class DFSchemaField(BaseModel):
    """Model for the DataFrame schema field in the response."""

    changes: Any | None = None
    dtype: str
    metadata: Any | None = None
    name: str


class DFSchema(BaseModel):
    """Model for the DataFrame schema in the response."""

    fields: list[DFSchemaField]
    hash: str
    metadata: Any | None = None


class SizeModel(BaseModel):
    """Model for the size in the response."""

    height: int
    width: int


class SourceModel(BaseModel):
    """Model for the source in the response."""

    schema: DFSchema
    size: SizeModel


class PaginationModel(BaseModel):
    """Model for the pagination in the response."""

    page_number: int
    page_size: int
    total_entries: int
    total_pages: int


class RowDataModel(BaseModel):
    """Model for the row data in the response."""

    id: str
    text: str
    title: str
    url: str


class DataFrameViewOptsModel(BaseModel):
    """Model for the view options in the response."""

    name: str
    value: Any | None = None  # could be bool, str, etc.


class DataFrameViewModel(BaseModel):
    """Model for the view in the response."""

    data: list[RowDataModel]
    opts: list[DataFrameViewOptsModel]
    pagination: PaginationModel
    schema: DFSchema
    size: SizeModel


class DataFrameModel(BaseModel):
    """Model for the data_frame in the response."""

    source: SourceModel
    view: DataFrameViewModel


class RequestParamsModel(BaseModel):
    """Model for the request params in the response."""

    namespace: str
    repo_name: str
    resource: list[str]


class ResourceInfoModel(BaseModel):
    """Model for the resource info in the response."""

    path: str
    version: str


class OxenDatasetResponse(BaseModel):
    """Response model containing the rows from the Oxen DataFrame."""

    commit: CommitModel
    data_frame: DataFrameModel
    derived_resource: Any | None
    oxen_version: str
    request_params: RequestParamsModel
    resource: ResourceInfoModel
    status: str
    status_message: str


def _get_dataset_from_oxen_response(oxen_resp: OxenDatasetResponse) -> Dataset:
    """Parse the OxenDatasetResponse pydantic model into our custom Dataset."""
    # Extract commit info
    commit = {
        "author": oxen_resp.commit.author,
        "email": oxen_resp.commit.email,
        "id": oxen_resp.commit.id,
        "message": oxen_resp.commit.message,
        "timestamp": oxen_resp.commit.timestamp,
        # etc. if needed
    }

    # Build a custom data_frame from the nested objects:
    # We can parse row data from `oxen_resp.data_frame.view.data`
    row_dicts = []
    for row_model in oxen_resp.data_frame.view.data:
        # row_model is a RowDataModel
        row_dicts.append(
            {
                "id": row_model.id,
                "text": row_model.text,
                "title": row_model.title,
                "url": row_model.url,
            }
        )

    # For the "schema", we can store a minimal dict or some more structured data
    schema_dict = {
        "fields": [f.dict() for f in oxen_resp.data_frame.view.schema.fields],
        "hash": oxen_resp.data_frame.view.schema.hash,
        "metadata": oxen_resp.data_frame.view.schema.metadata,
    }

    # For size, let's store height/width
    size_info = {
        "height": oxen_resp.data_frame.view.size.height,
        "width": oxen_resp.data_frame.view.size.width,
    }

    # Construct our custom LilypadDataFrame
    data_frame_obj = DataFrame(rows=row_dicts, schema=schema_dict, size=size_info)

    return Dataset(
        commit_info=commit,
        data_frame=data_frame_obj,
        status=oxen_resp.status,
        status_message=oxen_resp.status_message,
    )


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
            raise ValueError(
                "No project_uuid is set in LilypadClient (cannot fetch dataset)."
            )

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

    def get_datasets(
        self,
        generation_uuid: str | None = None,
        generation_name: str | None = None,
        page_num: int = 1,
        page_size: int = 50,
    ) -> Dataset:
        """Calls the get_dataset_rows method, obtains an OxenDatasetResponse,
        and builds a custom LilypadDataset from it.
        """
        oxen_resp = self.get_dataset_rows(
            generation_uuid=generation_uuid,
            generation_name=generation_name,
            page_num=page_num,
            page_size=page_size,
        )
        # Convert that pydantic model to a LilypadDataset
        lilypad_ds = _get_dataset_from_oxen_response(oxen_resp)
        return lilypad_ds
