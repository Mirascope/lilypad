"""Tests for the Dataset class and the datasets() function."""

import pytest
from unittest.mock import patch, MagicMock

from lilypad.server.client import LilypadClient
from oxen.data_frame import DataFrame
from lilypad.evals import Dataset, datasets


@pytest.fixture
def mock_dataframe():
    """
    Fixture that patches the DataFrame constructor and returns a MagicMock.

    Yields:
        A tuple (mock_df, mock_constructor) where:
          - mock_df is the MagicMock instance returned when DataFrame is constructed
          - mock_constructor is the patched constructor function
    """
    mock_df_instance = MagicMock(spec=DataFrame)
    with patch("lilypad.evals.datasets.DataFrame", return_value=mock_df_instance) as mock_ctor:
        yield mock_df_instance, mock_ctor


@pytest.fixture
def default_args():
    """Provides default arguments for Dataset initialization."""
    return {
        "remote": "https://hub.oxen.ai/namespace/repo",
        "path": "data/train.csv",
        "branch": "main",
        "host": "hub.oxen.ai",
    }


def test_dataset_init(mock_dataframe, default_args):
    """
    Test that the Dataset constructor creates an internal DataFrame instance
    with the correct arguments.
    """
    mock_df_instance, mock_ctor = mock_dataframe
    ds = Dataset(**default_args)
    mock_ctor.assert_called_once_with(
        remote=default_args["remote"],
        path=default_args["path"],
        branch=default_args["branch"],
        host=default_args["host"]
    )
    assert ds._df is mock_df_instance, "Dataset._df should store the mock DataFrame instance."


def test_dataset_insert(mock_dataframe, default_args):
    """
    Test that insert() calls insert_row() on the internal DataFrame.
    """
    mock_df_instance, _ = mock_dataframe
    ds = Dataset(**default_args)
    row_data = {"name": "Alice", "age": 30}
    ds.insert(row_data)
    mock_df_instance.insert_row.assert_called_once_with(row_data)


def test_dataset_list_page(mock_dataframe, default_args):
    """
    Test that list_page() calls list_page() on the internal DataFrame.
    """
    mock_df_instance, _ = mock_dataframe
    ds = Dataset(**default_args)
    ds.list_page(page_num=3)
    mock_df_instance.list_page.assert_called_once_with(3)


def test_dataset_update(mock_dataframe, default_args):
    """
    Test that update() calls update_row() on the internal DataFrame.
    """
    mock_df_instance, _ = mock_dataframe
    ds = Dataset(**default_args)
    ds.update("row_id", {"age": 31})
    mock_df_instance.update_row.assert_called_once_with("row_id", {"age": 31})


def test_dataset_delete(mock_dataframe, default_args):
    """
    Test that delete() calls delete_row() on the internal DataFrame.
    """
    mock_df_instance, _ = mock_dataframe
    ds = Dataset(**default_args)
    ds.delete("row_123")
    mock_df_instance.delete_row.assert_called_once_with("row_123")


def test_dataset_restore(mock_dataframe, default_args):
    """
    Test that restore() calls restore() on the internal DataFrame.
    """
    mock_df_instance, _ = mock_dataframe
    ds = Dataset(**default_args)
    ds.restore()
    mock_df_instance.restore.assert_called_once()


def test_dataset_commit(mock_dataframe, default_args):
    """
    Test that commit() calls commit() on the internal DataFrame.
    """
    mock_df_instance, _ = mock_dataframe
    ds = Dataset(**default_args)
    ds.commit("Test commit", branch="dev")
    mock_df_instance.commit.assert_called_once_with("Test commit", "dev")


def test_dataset_size(mock_dataframe, default_args):
    """
    Test that size() calls size() on the internal DataFrame and returns the result.
    """
    mock_df_instance, _ = mock_dataframe
    mock_df_instance.size.return_value = (100, 5)
    ds = Dataset(**default_args)
    result = ds.size()
    mock_df_instance.size.assert_called_once()
    assert result == (100, 5), "size() should return (100, 5)."


def test_dataset_repr(mock_dataframe, default_args):
    """
    Test the __repr__ method for Dataset instances.
    """
    mock_df_instance, _ = mock_dataframe
    mock_df_instance.size.return_value = (50, 3)
    ds = Dataset(**default_args)
    representation = repr(ds)
    assert "Dataset rows=50 cols=3" in representation, (
        "The __repr__ should include the row and column count."
    )


@pytest.fixture
def mock_lilypad_client():
    """
    Fixture that patches the usage of LilypadClient inside lilypad.evals.datasets,
    ensuring no real HTTP calls occur.

    Yields:
        A MagicMock instance for LilypadClient.
    """
    mock_client_instance = MagicMock(spec=LilypadClient)
    # Patch it at the location it's used: "lilypad.evals.datasets.LilypadClient"
    with patch("lilypad.evals.datasets.LilypadClient", return_value=mock_client_instance):
        yield mock_client_instance


@pytest.fixture
def mock_meta():
    """Provides default dataset metadata returned by LilypadClient."""
    return {
        "repo_url": "https://hub.oxen.ai/namespace/repo",
        "branch": "main",
        "path": "data/train.csv"
    }


def test_datasets_no_identifiers():
    """
    Test that calling datasets() with no identifiers raises a ValueError.
    """
    with pytest.raises(ValueError, match="No generation identifier provided"):
        datasets()


def test_datasets_generation_uuid_first(mock_lilypad_client, mock_dataframe, mock_meta):
    """
    Test that datasets() tries generation_uuid first, then stops if successful.
    """
    mock_df_instance, mock_ctor = mock_dataframe
    # On the first call, pretend success for generation_uuid
    mock_lilypad_client.get_dataset_metadata.side_effect = [mock_meta]

    ds = datasets("uuid_123")  # Should pass generation_uuid="uuid_123"
    # Validate the first call was with generation_uuid
    mock_lilypad_client.get_dataset_metadata.assert_any_call(generation_uuid="uuid_123")

    # Check that it never attempts generation_name
    calls = mock_lilypad_client.get_dataset_metadata.mock_calls
    assert len(calls) == 1, "Should only call get_dataset_metadata once (UUID)."

    mock_ctor.assert_called_once_with(
        remote=mock_meta["repo_url"],
        path=mock_meta["path"],
        branch=mock_meta["branch"],
        host="hub.oxen.ai"
    )
    # Check that the dataset internally stored the mock DataFrame
    assert ds._df is mock_df_instance


def test_datasets_generation_name_fallback(mock_lilypad_client, mock_dataframe, mock_meta):
    """
    Test that datasets() falls back to generation_name if generation_uuid fails.
    """
    mock_df_instance, mock_ctor = mock_dataframe
    # On first call, raise an Exception (UUID not found),
    # second call returns mock_meta (treat as generation_name).
    mock_lilypad_client.get_dataset_metadata.side_effect = [
        Exception("UUID not found"),
        mock_meta,
    ]

    ds = datasets("gen_name")

    calls = mock_lilypad_client.get_dataset_metadata.mock_calls
    # We should see 2 calls: first with generation_uuid, second with generation_name
    assert len(calls) == 2, "Should try generation_uuid first, then generation_name."

    mock_ctor.assert_called_once_with(
        remote=mock_meta["repo_url"],
        path=mock_meta["path"],
        branch=mock_meta["branch"],
        host="hub.oxen.ai"
    )
    assert ds._df is mock_df_instance


def test_datasets_returns_dataset_instance(mock_lilypad_client, mock_dataframe, mock_meta):
    """
    Test that datasets() returns a Dataset instance using the retrieved metadata.
    """
    mock_lilypad_client.get_dataset_metadata.return_value = mock_meta
    mock_df_instance, mock_ctor = mock_dataframe

    ds = datasets("my_generation_id")
    assert isinstance(ds, Dataset), "datasets() should return a Dataset instance."
    mock_ctor.assert_called_once_with(
        remote=mock_meta["repo_url"],
        path=mock_meta["path"],
        branch=mock_meta["branch"],
        host="hub.oxen.ai"
    )
    assert ds._df is mock_df_instance
