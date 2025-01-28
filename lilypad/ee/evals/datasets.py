"""Provides a high-level Lilypad interface (Dataset) that internally uses Oxen DataFrame."""

from oxen.data_frame import DataFrame

from lilypad.server.client import LilypadClient


class Dataset:
    """A Lilypad dataset interface that wraps an Oxen DataFrame internally.

    This allows Lilypad to control the external API while delegating data operations
    to Oxen under the hood.
    """

    def __init__(
        self, remote: str, path: str, branch: str, host: str = "hub.oxen.ai"
    ) -> None:
        """Initialize the Dataset by creating an Oxen DataFrame internally.

        Args:
            remote: The remote repository URL for the Oxen dataset.
            path: The path of the DataFrame file within the repository.
            branch: The branch name of the repository.
            host: The Oxen server host (defaults to "hub.oxen.ai").
        """
        # Store a reference to the internal Oxen DataFrame
        self._df = DataFrame(remote=remote, path=path, branch=branch, host=host)

    def insert(self, row: dict) -> str:
        """Insert a single row into the underlying DataFrame.

        Args:
            row: A dictionary representing the columns and values to insert.

        Returns:
            The unique identifier of the newly inserted row.
        """
        return self._df.insert_row(row)

    def list_page(self, page_num: int = 1) -> list[dict]:
        """List the rows of the DataFrame, paginated.

        Args:
            page_num: The page number to list.

        Returns:
            A list of rows for the specified page.
        """
        return self._df.list_page(page_num)

    def update(self, row_id: str, new_data: dict) -> dict:
        """Update a row in the DataFrame by row identifier.

        Args:
            row_id: The unique identifier of the row to update.
            new_data: A dictionary containing the columns and updated values.

        Returns:
            The updated row as a dictionary.
        """
        return self._df.update_row(row_id, new_data)

    def delete(self, row_id: str) -> None:
        """Delete a row in the DataFrame by row identifier.

        Args:
            row_id: The unique identifier of the row to delete.
        """
        self._df.delete_row(row_id)

    def restore(self) -> None:
        """Unstage any local (uncommitted) changes to the underlying DataFrame."""
        self._df.restore()

    def commit(self, message: str, branch: str | None = None) -> None:
        """Commit any staged changes to the underlying DataFrame.

        Args:
            message: The commit message.
            branch: (Optional) The branch to commit the changes into.
        """
        self._df.commit(message, branch)

    def size(self) -> tuple[int, int]:
        """Return the size of the DataFrame in terms of rows and columns.

        Returns:
            A tuple (rows, columns).
        """
        return self._df.size()

    def __repr__(self) -> str:
        """Custom string representation for debugging.

        Returns:
            A user-friendly string showing the size of the dataset.
        """
        rows, cols = self.size()
        return f"<Dataset rows={rows} cols={cols}>"


def datasets(*identifiers: str, host: str = "hub.oxen.ai") -> Dataset:
    """Fetch a Lilypad Dataset object for the specified generation(s), using Oxen under the hood.

    We currently handle only the first identifier for simplicity.

    Usage:
        ds = datasets("some_generation_uuid")
        # or
        ds = datasets("some_generation_name")

    Then you can operate on `ds` using the Dataset API (insert, update, commit, etc.).

    Args:
        identifiers: One or more generation identifiers (UUIDs or names).
        host: The Oxen server host (defaults to "hub.oxen.ai").

    Returns:
        A Dataset object that internally wraps an Oxen DataFrame.
    """
    if not identifiers:
        raise ValueError("No generation identifier provided.")

    # For demonstration, pick the first identifier
    gen_id = identifiers[0]

    # Attempt to interpret gen_id as a UUID or a name; the server logic will decide
    client = LilypadClient()
    try:
        meta = client.get_dataset_metadata(generation_uuid=gen_id)
    except Exception:
        # If that fails, try generation_name
        meta = client.get_dataset_metadata(generation_name=gen_id)

    # meta should look like: {"repo_url": str, "branch": str, "path": str}
    return Dataset(
        remote=meta["repo_url"], path=meta["path"], branch=meta["branch"], host=host
    )
