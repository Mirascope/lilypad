"""The `lilypad` API client."""

from typing import Any, Literal, TypeVar

from pydantic import BaseModel

from ...server.client import LilypadClient as _LilypadClient
from ...server.schemas import GenerationPublic

_R = TypeVar("_R", bound=BaseModel)


class NotFoundError(Exception):
    """Raised when an API response has a status code of 404."""

    status_code: Literal[404] = 404


class APIConnectionError(Exception):
    """Raised when an API connection error occurs."""

    ...


class DatasetRowsResponse(BaseModel):
    """Response model containing the rows from the Oxen DataFrame."""

    rows: list[dict[str, Any]]
    next_page: int | None = None


class LilypadClient(_LilypadClient):
    """A client for the Lilypad ee API."""

    def get_generations_by_name(self, generation_name: str) -> list[GenerationPublic]:
        """Get generations by name."""
        return self._request(
            "GET",
            f"v0/projects/{self.project_uuid}/generations/name/{generation_name}",
            response_model=list[GenerationPublic],
        )

    def get_dataset_rows(
        self,
        generation_uuid: str | None = None,
        generation_name: str | None = None,
        generation_hash: str | None = None,
        page_num: int = 1,
    ) -> DatasetRowsResponse:
        """Fetch a dataset for a given generation, receiving Oxen-style JSON.

        Returns:
            An DatasetRowsResponse object, which includes commit info, data_frame, etc.
            The actual row data is in data_frame.view.data
        """
        if not self.project_uuid:
            raise ValueError(
                "No project_uuid is set in LilypadClient (cannot fetch dataset)."
            )
        params = {"page_num": page_num}
        if generation_uuid:
            return self._request(
                method="GET",
                endpoint=f"/v0/projects/{self.project_uuid}/generations/{generation_uuid}/datasets",
                response_model=DatasetRowsResponse,
                params=params,
            )
        elif generation_name:
            return self._request(
                method="GET",
                endpoint=f"/v0/projects/{self.project_uuid}/datasets/names/{generation_name}",
                response_model=DatasetRowsResponse,
                params=params,
            )
        elif generation_hash:
            return self._request(
                method="GET",
                endpoint=f"/v0/projects/{self.project_uuid}/datasets/hash/{generation_hash}",
                response_model=DatasetRowsResponse,
                params=params,
            )
        raise ValueError(
            "Must provide either generation_uuid, generation_name, or generation_hash."
        )
