"""Provides a high-level Lilypad interface (Dataset) that internally uses Oxen DataFrame,
adjusted for the updated Oxen dataset API that returns an Oxen-style JSON.
"""

from __future__ import annotations

from collections.abc import Callable
from itertools import count
from typing import TYPE_CHECKING, Any
from uuid import UUID

from lilypad._utils import Closure

if TYPE_CHECKING:
    from lilypad.ee.server.client import LilypadClient


class DataFrame:
    """A custom, lightweight DataFrame-like class for Lilypad.
    It stores rows, schema info, etc., but does NOT rely on oxen.data_frame.DataFrame.
    """

    def __init__(self, rows: list[dict[str, Any]]) -> None:
        self.rows = rows
        keys = rows[0].keys() if rows else []
        self._key_size = len(keys)
        self.row_keys = keys

    def list_rows(self) -> list[dict[str, Any]]:
        """Return a list of all rows in this data frame."""
        return self.rows

    def get_row_count(self) -> int:
        """Return how many rows are in this data frame."""
        return len(self.rows)

    def get_column_count(self) -> int:
        """Return how many columns (width) are in this data frame schema."""
        return self._key_size


class Dataset:
    """A custom 'Dataset' object that references commit info and a custom DataFrame."""

    def __init__(
        self,
        data_frame: DataFrame,
    ) -> None:
        self.data_frame = data_frame

    def __repr__(self) -> str:
        """Example string representation showing row/col counts."""
        row_ct = self.data_frame.get_row_count()
        col_ct = self.data_frame.get_column_count()
        return f"<Dataset rows={row_ct} cols={col_ct}>"


def _get_client() -> LilypadClient:
    """Helper function to create a LilypadClient instance."""
    from lilypad.ee.server.client import LilypadClient

    return LilypadClient()


def datasets(*uuids: str | UUID) -> list[Dataset]:
    """Retrieve one or more Datasets using generation UUIDs.
    If only one UUID is provided, returns a single Dataset.
    """
    if not uuids:
        raise ValueError("No UUID provided to 'datasets'.")

    client = _get_client()
    results: list[Dataset] = []

    for gen_uuid in uuids:
        # Convert to string if user passed a UUID object
        uuid_str = str(gen_uuid)
        dataset_rows = []
        for page_num in count(start=1):
            response = client.get_dataset_rows(
                generation_uuid=uuid_str,
                page_num=page_num,
            )
            if not response.rows:
                break
            dataset_rows.extend(response.rows)

        results.append(Dataset(DataFrame(dataset_rows)))

    return results


def datasets_from_name(*names: str) -> list[Dataset]:
    """Retrieve one or more Datasets using generation names.
    If only one name is provided, returns a single Dataset.
    """
    if not names:
        raise ValueError("No name provided to 'datasets_from_name'.")

    client = _get_client()
    results: list[Dataset] = []

    for generation_name in names:
        dataset_rows = []
        for page_num in count(start=1):
            response = client.get_dataset_rows(
                generation_name=generation_name,
                page_num=page_num,
            )
            if not response.rows:
                break
            dataset_rows.extend(response.rows)

        results.append(Dataset(DataFrame(dataset_rows)))

    return results


def datasets_from_fn(*fns: Callable[..., Any]) -> list[Dataset]:
    """Retrieve one or more Datasets from function objects.
    Internally uses a Closure utility to extract a unique hash or signature
    and queries by that as a generation UUID or name.
    """
    if not fns:
        raise ValueError("No function provided to 'datasets_from_fn'.")

    client = _get_client()
    results: list[Dataset] = []

    for fn in fns:
        closure_obj = Closure.from_fn(fn)
        dataset_rows = []
        for page_num in count(start=1):
            response = client.get_dataset_rows(
                generation_hash=closure_obj.hash,
                page_num=page_num,
            )
            if not response.rows:
                break
            dataset_rows.extend(response.rows)

        results.append(Dataset(DataFrame(dataset_rows)))

    return results
