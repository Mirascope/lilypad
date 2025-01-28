"""Provides a high-level Lilypad interface (Dataset) that internally uses Oxen DataFrame,
adjusted for the updated Oxen dataset API that returns an Oxen-style JSON.
"""

from __future__ import annotations

from typing import Any


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
