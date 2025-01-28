"""Provides a high-level Lilypad interface (Dataset) that internally uses Oxen DataFrame,
adjusted for the updated Oxen dataset API that returns an Oxen-style JSON.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, overload
from uuid import UUID

from lilypad._utils import Closure

if TYPE_CHECKING:
    from lilypad.ee.server.client import LilypadClient


class DataFrame:
    """A custom, lightweight DataFrame-like class for Lilypad.
    It stores rows, schema info, etc., but does NOT rely on oxen.data_frame.DataFrame.
    """

    def __init__(
        self, rows: list[dict[str, Any]], schema: dict[str, Any], size: dict[str, int]
    ) -> None:
        self.rows = rows
        self.schema = schema
        self.size_info = size
        # Add any other fields or logic needed

    def list_rows(self, page: int = 1) -> list[dict[str, Any]]:
        """For demonstration, we simply return all rows.
        Or you could implement pagination logic if desired.
        """
        # If you want, you can use `page` to slice self.rows
        return self.rows

    def get_row_count(self) -> int:
        """Return how many rows are in this data frame."""
        return self.size_info.get("height", len(self.rows))

    def get_column_count(self) -> int:
        """Return how many columns (width) are in this data frame schema."""
        return self.size_info.get("width", 0)


class Dataset:
    """A custom 'Dataset' object that references commit info and a custom DataFrame."""

    def __init__(
        self,
        commit_info: dict[str, Any],
        data_frame: DataFrame,
        status: str,
        status_message: str,
    ) -> None:
        self.commit_info = commit_info
        self.data_frame = data_frame
        self.status = status
        self.status_message = status_message

    def __repr__(self) -> str:
        """Example string representation showing row/col counts + commit id."""
        row_ct = self.data_frame.get_row_count()
        col_ct = self.data_frame.get_column_count()
        commit_id = self.commit_info.get("id", "unknown")
        return f"<Dataset commit_id={commit_id} rows={row_ct} cols={col_ct}>"


def _get_client() -> LilypadClient:
    """Helper function to create a LilypadClient instance."""
    from lilypad.ee.server.client import LilypadClient

    return LilypadClient()


@overload
def datasets(
    __uuid: str | UUID, *, page_num: int = 1, page_size: int = 50
) -> Dataset: ...


@overload
def datasets(
    *__uuids: str | UUID, page_num: int = 1, page_size: int = 50
) -> list[Dataset]: ...


def datasets(
    *uuids: str | UUID, page_num: int = 1, page_size: int = 50
) -> Dataset | list[Dataset]:
    """Retrieve one or more Datasets using generation UUIDs.
    If only one UUID is provided, returns a single Dataset.
    If multiple are provided, returns a list of Datasets.
    """
    if not uuids:
        raise ValueError("No UUID provided to 'datasets'.")

    client = _get_client()
    results: list[Dataset] = []

    for gen_uuid in uuids:
        # Convert to string if user passed a UUID object
        uuid_str = str(gen_uuid)
        ds_obj = client.get_datasets(
            generation_uuid=uuid_str,
            page_num=page_num,
            page_size=page_size,
        )
        results.append(ds_obj)

    return results[0] if len(results) == 1 else results


@overload
def datasets_from_name(
    __name: str, *, page_num: int = 1, page_size: int = 50
) -> Dataset: ...


@overload
def datasets_from_name(
    *__names: str, page_num: int = 1, page_size: int = 50
) -> list[Dataset]: ...


def datasets_from_name(
    *names: str, page_num: int = 1, page_size: int = 50
) -> Dataset | list[Dataset]:
    """Retrieve one or more Datasets using generation names.
    If only one name is provided, returns a single Dataset.
    If multiple are provided, returns a list of Datasets.
    """
    if not names:
        raise ValueError("No name provided to 'datasets_from_name'.")

    client = _get_client()
    results: list[Dataset] = []

    for gen_name in names:
        ds_obj = client.get_datasets(
            generation_name=gen_name,
            page_num=page_num,
            page_size=page_size,
        )
        results.append(ds_obj)

    return results[0] if len(results) == 1 else results


@overload
def datasets_from_fn(
    __fn: Callable[..., Any], *, page_num: int = 1, page_size: int = 50
) -> Dataset: ...


@overload
def datasets_from_fn(
    *__fns: Callable[..., Any], page_num: int = 1, page_size: int = 50
) -> list[Dataset]: ...


def datasets_from_fn(
    *fns: Callable[..., Any], page_num: int = 1, page_size: int = 50
) -> Dataset | list[Dataset]:
    """Retrieve one or more Datasets from function objects.
    Internally uses a Closure utility to extract a unique hash or signature
    and queries by that as a generation UUID or name.
    If only one function is provided, returns a single Dataset.
    If multiple are provided, returns a list of Datasets.
    """
    if not fns:
        raise ValueError("No function provided to 'datasets_from_fn'.")

    client = _get_client()
    results: list[Dataset] = []

    for fn in fns:
        closure_obj = Closure.from_fn(fn)
        ds_obj = client.get_datasets(
            generation_uuid=closure_obj.hash,
            page_num=page_num,
            page_size=page_size,
        )
        results.append(ds_obj)

    return results[0] if len(results) == 1 else results
