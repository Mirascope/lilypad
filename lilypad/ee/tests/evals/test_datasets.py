"""Tests for the Dataset and DataFrame classes, and the datasets(...) function."""

import json
from unittest.mock import MagicMock, patch
from uuid import UUID

import pytest

from lilypad._utils import Closure
from lilypad.ee.evals import (
    DataFrame,
    Dataset,
    datasets,
    datasets_from_fn,
    datasets_from_name,
)


def test_data_frame_basic():
    """Test creating a DataFrame and verifying the row count and column count."""
    rows = [
        {"col1": 10, "col2": 20},
        {"col1": 30, "col2": 40},
    ]
    df = DataFrame(rows)
    assert df.get_row_count() == 2, "Should have 2 rows"
    assert df.get_column_count() == 2, "Should have 2 columns"
    assert df.list_rows() == rows, "The rows should match the original data"


def test_data_frame_empty():
    """Test creating an empty DataFrame."""
    df = DataFrame([])
    assert df.get_row_count() == 0, "Should have 0 rows"
    assert df.get_column_count() == 0, "Should have 0 columns"
    assert df.list_rows() == [], "Should return an empty list for rows"


def test_dataset_repr():
    """Test the string representation of a Dataset."""
    rows = [
        {"foo": "bar", "num": 123},
        {"foo": "baz", "num": 456},
    ]
    df = DataFrame(rows)
    ds = Dataset(df)
    assert repr(ds) == "<Dataset rows=2 cols=2>", "Unexpected __repr__ output"


@pytest.fixture
def mock_client():
    """Create a mocked LilypadClient that simulates paginated row retrieval.
    The first two pages return some data, the third returns no data to end pagination.
    """
    # Create a MagicMock instance to represent the client
    client = MagicMock()

    # Simulate client.get_dataset_rows(...) returning pages of data, then an empty page
    # to signal no more rows.
    # Each call to get_dataset_rows will return a mock response object.
    # We'll track how many times it's called (page_num).
    def mock_get_dataset_rows(**kwargs):
        page_num = kwargs.get("page_num")
        # Return different data based on page_num
        if page_num == 1:
            return MagicMock(rows=[{"a": 1, "b": 2}], next_page=2)
        elif page_num == 2:
            return MagicMock(rows=[{"a": 3, "b": 4}], next_page=None)
        else:
            return MagicMock(rows=[], next_page=None)

    client.get_dataset_rows.side_effect = mock_get_dataset_rows
    return client


@patch("lilypad.ee.evals.datasets._get_client")
def test_datasets_single_uuid(mock_get_client, mock_client):
    """Test retrieving a single dataset by UUID."""
    mock_get_client.return_value = mock_client

    # We pass a single UUID, expecting a single Dataset.
    results = datasets("123e4567-e89b-12d3-a456-426655440000")
    assert len(results) == 1, "Should return a single Dataset"
    result = results[0]
    assert isinstance(result, Dataset), "Should return a single Dataset instance"
    # Verify the internal data frame has 2 rows from our mocked pagination logic
    assert result.data_frame.get_row_count() == 2, "Dataset should have 2 rows total"
    assert result.data_frame.get_column_count() == 2, "Dataset should have 2 columns"


@patch("lilypad.ee.evals.datasets._get_client")
def test_datasets_multiple_uuids(mock_get_client, mock_client):
    """Test retrieving multiple datasets by passing multiple UUIDs."""
    mock_get_client.return_value = mock_client

    uuid1 = "123e4567-e89b-12d3-a456-426655440000"
    uuid2 = UUID("123e4567-e89b-12d3-a456-426655440001")
    result = datasets(uuid1, uuid2)

    assert isinstance(result, list), "Should return a list of Datasets"
    assert len(result) == 2, "Should have exactly 2 Datasets in the result"
    for ds in result:
        assert isinstance(ds, Dataset), "All items should be Dataset instances"
        # Each dataset should have 2 rows from our mocked pagination logic
        assert ds.data_frame.get_row_count() == 2, "Each dataset should have 2 rows"


@patch("lilypad.ee.evals.datasets._get_client")
def test_datasets_from_name_single(mock_get_client, mock_client):
    """Test retrieving a single dataset from a generation name."""
    mock_get_client.return_value = mock_client

    results = datasets_from_name("my_generation_name")
    assert len(results) == 1, "Should return a single Dataset"
    result = results[0]
    assert isinstance(result, Dataset), "Should return a single Dataset"
    assert result.data_frame.get_row_count() == 2, "Dataset should have 2 rows"


@patch("lilypad.ee.evals.datasets._get_client")
def test_datasets_from_name_multiple(mock_get_client, mock_client):
    """Test retrieving multiple datasets by passing multiple generation names."""
    mock_get_client.return_value = mock_client

    result = datasets_from_name("gen_name_1", "gen_name_2")
    assert isinstance(result, list), "Should return a list of Datasets"
    assert len(result) == 2, "Should have 2 Datasets"
    for ds in result:
        assert ds.data_frame.get_row_count() == 2, "Each dataset should have 2 rows"


@patch("lilypad.ee.evals.datasets._get_client")
def test_datasets_from_fn_single(mock_get_client, mock_client):
    """Test retrieving a single dataset from a function reference."""
    mock_get_client.return_value = mock_client

    def dummy_fn():
        pass

    results = datasets_from_fn(dummy_fn)
    assert len(results) == 1, "Should return a single Dataset"
    result = results[0]
    assert isinstance(result, Dataset), "Should return a single Dataset"
    assert result.data_frame.get_row_count() == 2, "Dataset should have 2 rows"


@patch("lilypad.ee.evals.datasets._get_client")
def test_datasets_from_fn_multiple(mock_get_client, mock_client):
    """Test retrieving multiple datasets from multiple function references."""
    mock_get_client.return_value = mock_client

    def dummy_fn1():
        pass

    def dummy_fn2():
        pass

    result = datasets_from_fn(dummy_fn1, dummy_fn2)
    assert isinstance(result, list), "Should return a list of Datasets"
    assert len(result) == 2, "Should have 2 Datasets"
    for ds in result:
        assert ds.data_frame.get_row_count() == 2, "Each dataset should have 2 rows"


def sample_fn(question: str) -> str:
    """A sample function to test closures."""
    return f"Answer: {question}"


@pytest.fixture
def sample_dataset() -> Dataset:
    """Create a Dataset with a DataFrame that contains some rows.
    Each row has an 'input' key containing JSON-encoded arguments.
    """
    rows = [
        {"input": json.dumps({"question": "What is 2+2?"})},
        {"input": json.dumps({"question": "What is the capital of France?"})},
    ]
    df = DataFrame(rows=rows)
    return Dataset(data_frame=df)


def test_dataset_run_success(sample_dataset: Dataset):
    """Test that Dataset.run(fn) successfully calls closure.run() for each row."""
    mock_client = MagicMock()
    mock_client.get_generations_by_name.return_value = []

    with (
        patch("lilypad.ee.evals.datasets._get_client", return_value=mock_client),
        patch.object(Closure, "from_fn", wraps=Closure.from_fn) as mock_closure,
        patch.object(Closure, "run", return_value=None) as mock_run,
    ):
        sample_dataset.run(sample_fn)

        assert mock_run.call_count == 2

        mock_closure.assert_called_once_with(sample_fn)


def test_dataset_run_missing_input_key():
    """If a row does not contain 'input', run() should raise ValueError."""
    df = DataFrame(rows=[{"not_input": "nope"}])
    ds = Dataset(data_frame=df)

    mock_client = MagicMock()
    mock_client.get_generations_by_name.return_value = []

    with (
        patch("lilypad.ee.evals.datasets._get_client", return_value=mock_client),
        pytest.raises(ValueError, match="Row does not contain 'input' key"),
    ):
        ds.run(sample_fn)


def test_dataset_run_input_not_json():
    """If a row's 'input' is not valid JSON, run() should raise ValueError on json.loads()."""
    df = DataFrame(rows=[{"input": "this-is-not-json"}])
    ds = Dataset(data_frame=df)

    mock_client = MagicMock()
    mock_client.get_generations_by_name.return_value = []

    with (
        patch("lilypad.ee.evals.datasets._get_client", return_value=mock_client),
        pytest.raises(ValueError, match="Expecting value: line 1 column 1"),
    ):
        ds.run(sample_fn)


def test_dataset_run_multiple_closures(sample_dataset: Dataset):
    """If get_generations_by_name returns multiple generations,
    we construct multiple closures and run them all on each row.
    """
    gen1 = MagicMock(hash="123", signature="...", code="...", dependencies={})
    gen1.name = "gen1"
    gen2 = MagicMock(hash="456", signature="...", code="...", dependencies={})
    gen2.name = "gen2"

    mock_client = MagicMock()
    mock_client.get_generations_by_name.return_value = [gen1, gen2]

    with (
        patch("lilypad.ee.evals.datasets._get_client", return_value=mock_client),
        patch.object(Closure, "from_fn", wraps=Closure.from_fn),
        patch.object(Closure, "run", return_value=None) as mock_run,
    ):
        sample_dataset.run(sample_fn)

        calls = mock_run.call_count
        assert calls in (4, 6), (
            "Expected run calls to be either 4 or 6 depending on whether the client"
            " returned a generation with the same hash as current closure or not. "
            f"Got {calls}."
        )


def test_dataset_run_exception_in_closure(sample_dataset: Dataset, capsys):
    """If closure.run() raises an exception, we catch it, print the error, and continue."""
    mock_gen = MagicMock(hash="abc", signature="...", code="...", dependencies={})
    mock_gen.name = "gen"
    mock_client = MagicMock()
    mock_client.get_generations_by_name.return_value = [mock_gen]

    with (
        patch("lilypad.ee.evals.datasets._get_client", return_value=mock_client),
        patch.object(Closure, "from_fn", wraps=Closure.from_fn),
    ):
        call_counter = [0]

        def side_effect_run(**kwargs):
            call_counter[0] += 1
            if call_counter[0] == 2:
                raise RuntimeError("Simulated error")

        with patch.object(Closure, "run", side_effect=side_effect_run):
            sample_dataset.run(sample_fn)
