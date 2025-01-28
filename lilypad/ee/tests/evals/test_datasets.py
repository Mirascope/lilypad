"""Tests for the LilypadClient and Dataset/DataFrame integration
using the updated Oxen dataset API code.
"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest

from lilypad._utils import Closure
from lilypad.ee.evals import Dataset
from lilypad.ee.evals.datasets import (
    DataFrame,
    datasets,
    datasets_from_fn,
    datasets_from_name,
)
from lilypad.ee.server.client import (
    CommitModel,
    DataFrameModel,
    DataFrameViewModel,
    DFSchema,
    DFSchemaField,
    LilypadClient,
    NotFoundError,
    OxenDatasetResponse,
    PaginationModel,
    RequestParamsModel,
    ResourceInfoModel,
    RowDataModel,
    SizeModel,
    SourceModel,
    _get_dataset_from_oxen_response,
)


@pytest.fixture
def sample_oxen_response() -> OxenDatasetResponse:
    """Create a sample OxenDatasetResponse for testing."""
    commit = CommitModel(
        author="Test Author",
        email="author@test.com",
        id="abcdef123",
        message="Test commit message",
        parent_ids=[],
        root_hash=None,
        timestamp="2025-01-01T00:00:00Z",
    )

    schema_fields = [
        DFSchemaField(changes=None, dtype="str", metadata=None, name="id"),
        DFSchemaField(changes=None, dtype="str", metadata=None, name="text"),
        DFSchemaField(changes=None, dtype="str", metadata=None, name="title"),
        DFSchemaField(changes=None, dtype="str", metadata=None, name="url"),
    ]
    view_schema = DFSchema(fields=schema_fields, hash="viewhash", metadata=None)
    source_schema = DFSchema(fields=schema_fields, hash="sourcehash", metadata=None)

    row_data_models = [
        RowDataModel(id="row1", text="hello", title="Title1", url="http://test1"),
        RowDataModel(id="row2", text="world", title="Title2", url="http://test2"),
    ]
    pagination = PaginationModel(
        page_number=1, page_size=2, total_entries=2, total_pages=1
    )
    view_size = SizeModel(height=2, width=4)
    source_size = SizeModel(height=10, width=4)

    data_frame_view = DataFrameViewModel(
        data=row_data_models,
        opts=[],
        pagination=pagination,
        schema=view_schema,
        size=view_size,
    )
    source_model = SourceModel(schema=source_schema, size=source_size)
    data_frame_model = DataFrameModel(source=source_model, view=data_frame_view)

    req_params = RequestParamsModel(
        namespace="ox",
        repo_name="SimpleWikipedia",
        resource=["main", "dataset.parquet"],
    )
    resource_info = ResourceInfoModel(path="dataset.parquet", version="main")

    return OxenDatasetResponse(
        commit=commit,
        data_frame=data_frame_model,
        derived_resource=None,
        oxen_version="0.22.2",
        request_params=req_params,
        resource=resource_info,
        status="success",
        status_message="All good",
    )


def test_get_dataset_from_oxen_response(
    sample_oxen_response: OxenDatasetResponse,
) -> None:
    """Test the internal _get_dataset_from_oxen_response function to ensure
    it returns a valid Dataset object populated with the right fields.
    """
    ds = _get_dataset_from_oxen_response(sample_oxen_response)
    assert isinstance(ds, Dataset)
    # Check commit info
    assert ds.commit_info["author"] == "Test Author"
    assert ds.commit_info["id"] == "abcdef123"
    # Check row count
    assert ds.data_frame.get_row_count() == 2
    # Check columns
    assert ds.data_frame.get_column_count() == 4
    # Check status
    assert ds.status == "success"
    assert ds.status_message == "All good"
    # Check the row data
    first_row = ds.data_frame.rows[0]
    assert first_row["id"] == "row1"
    assert first_row["title"] == "Title1"


def test_dataframe_list_rows() -> None:
    """Simple test for DataFrame to verify the list_rows method and size logic."""
    rows = [
        {"id": "1", "text": "alpha"},
        {"id": "2", "text": "beta"},
    ]
    schema = {"fields": [], "hash": "dummy", "metadata": None}
    size_info = {"height": 2, "width": 2}
    df = DataFrame(rows, schema, size_info)
    assert df.list_rows() == rows
    assert df.get_row_count() == 2
    assert df.get_column_count() == 2


def test_dataset_repr(sample_oxen_response: OxenDatasetResponse) -> None:
    """Test the __repr__ method of Dataset for debugging info."""
    ds = _get_dataset_from_oxen_response(sample_oxen_response)
    rep_str = repr(ds)
    assert "<Dataset commit_id=abcdef123 rows=2 cols=4>" in rep_str


@pytest.fixture
def client() -> LilypadClient:
    """Provide a LilypadClient instance for tests.
    We can override the ._request method with mocks as needed.
    """
    # We'll simulate that the project_uuid is set
    c = LilypadClient(timeout=2)
    c.project_uuid = uuid4()  # pretend we've set it
    return c


def test_lilypad_client_get_dataset_rows_success(
    client: LilypadClient, sample_oxen_response: OxenDatasetResponse
) -> None:
    """Test that get_dataset_rows returns an OxenDatasetResponse with valid data
    when the server is successful.
    """
    with patch.object(
        client, "_request", return_value=sample_oxen_response
    ) as mock_req:
        resp = client.get_dataset_rows(
            generation_uuid="some-gen-id", page_num=1, page_size=10
        )
        # Check that we got an OxenDatasetResponse
        assert isinstance(resp, OxenDatasetResponse)
        # Check fields
        assert resp.status == "success"
        mock_req.assert_called_once()


def test_lilypad_client_get_dataset_rows_no_project_uuid() -> None:
    """Test that if project_uuid is not set, we get a ValueError."""
    c = LilypadClient(timeout=2)
    with pytest.raises(ValueError, match="No project_uuid is set"):
        c.get_dataset_rows(generation_uuid="some-gen-id")


def test_lilypad_client_get_dataset_rows_not_found(client: LilypadClient) -> None:
    """If the server returns a 404, we want a NotFoundError raised."""
    with (
        patch.object(client, "_request", side_effect=NotFoundError("Not found!")),
        pytest.raises(NotFoundError),
    ):
        client.get_dataset_rows(generation_uuid="some-gen-id")


def test_lilypad_client_get_dataset_rows_connection_error(
    client: LilypadClient,
) -> None:
    """If there's a connection error, ensure an APIConnectionError is raised."""
    from requests.exceptions import ConnectionError

    with (
        patch.object(client, "_request", side_effect=ConnectionError()),
        pytest.raises(ConnectionError),
    ):
        client.get_dataset_rows(generation_uuid="some-gen-id")


def test_lilypad_client_get_datasets_success(
    client: LilypadClient, sample_oxen_response: OxenDatasetResponse
) -> None:
    """Test get_datasets() calls get_dataset_rows under the hood,
    then returns a custom Dataset.
    """
    with patch.object(
        client, "get_dataset_rows", return_value=sample_oxen_response
    ) as mock_gdr:
        ds_obj = client.get_datasets(generation_uuid="test-gen")
        # ds_obj should be a Dataset
        assert isinstance(ds_obj, Dataset)
        assert ds_obj.data_frame.get_row_count() == 2
        mock_gdr.assert_called_once_with(
            generation_uuid="test-gen", generation_name=None, page_num=1, page_size=50
        )


@pytest.fixture
def mock_dataset() -> Dataset:
    """A simple fixture that returns a dummy Dataset object."""
    return Dataset(
        commit_info={"id": "fake-commit-id"},
        data_frame=None,  # Normally this would be a DataFrame object
        status="success",
        status_message="OK",
    )


def dummy_fn():
    """A dummy function for testing Closure.from_fn usage."""
    return "hello"


#
# tests for datasets
#
def test_datasets_no_input():
    """If no UUIDs are provided, it should raise a ValueError."""
    with pytest.raises(ValueError, match="No UUID provided to 'datasets'"):
        datasets()


@patch.object(LilypadClient, "get_datasets")
def test_datasets_single(mock_get_datasets, mock_dataset):
    """Test a single UUID -> returns a single Dataset."""
    mock_get_datasets.return_value = mock_dataset

    test_uuid = str(uuid4())
    ds = datasets(test_uuid)

    # We expect a single Dataset, not a list
    assert isinstance(ds, Dataset)
    mock_get_datasets.assert_called_once_with(
        generation_uuid=test_uuid,
        page_num=1,
        page_size=50,
    )


@patch.object(LilypadClient, "get_datasets")
def test_datasets_multiple(mock_get_datasets, mock_dataset):
    """Test multiple UUIDs -> returns a list of Datasets."""
    # Suppose each call returns a distinct dataset object
    mock_get_datasets.side_effect = [mock_dataset, mock_dataset]

    uuid1 = str(uuid4())
    uuid2 = str(uuid4())
    ds_list = datasets(uuid1, uuid2, page_num=2, page_size=20)

    # We expect a list of Dataset
    assert isinstance(ds_list, list)
    assert len(ds_list) == 2
    for item in ds_list:
        assert isinstance(item, Dataset)

    # Check calls
    assert mock_get_datasets.call_count == 2
    mock_get_datasets.assert_any_call(
        generation_uuid=uuid1,
        page_num=2,
        page_size=20,
    )
    mock_get_datasets.assert_any_call(
        generation_uuid=uuid2,
        page_num=2,
        page_size=20,
    )


#
# tests for datasets_from_name
#
def test_datasets_from_name_no_input():
    """If no names are provided, it should raise a ValueError."""
    with pytest.raises(ValueError, match="No name provided to 'datasets_from_name'"):
        datasets_from_name()


@patch.object(LilypadClient, "get_datasets")
def test_datasets_from_name_single(mock_get_datasets, mock_dataset):
    """Test a single name -> returns a single Dataset."""
    mock_get_datasets.return_value = mock_dataset

    gen_name = "my_generation"
    ds = datasets_from_name(gen_name, page_num=3, page_size=10)

    assert isinstance(ds, Dataset)
    mock_get_datasets.assert_called_once_with(
        generation_name=gen_name,
        page_num=3,
        page_size=10,
    )


@patch.object(LilypadClient, "get_datasets")
def test_datasets_from_name_multiple(mock_get_datasets, mock_dataset):
    """Test multiple names -> returns a list of Datasets."""
    mock_get_datasets.side_effect = [mock_dataset, mock_dataset, mock_dataset]

    ds_list = datasets_from_name("name1", "name2", "name3")

    assert isinstance(ds_list, list)
    assert len(ds_list) == 3

    # Check calls
    assert mock_get_datasets.call_count == 3


#
# tests for datasets_from_fn
#
def test_datasets_from_fn_no_input():
    """If no functions are provided, it should raise a ValueError."""
    with pytest.raises(ValueError, match="No function provided to 'datasets_from_fn'"):
        datasets_from_fn()


@patch.object(LilypadClient, "get_datasets")
@patch.object(Closure, "from_fn")
def test_datasets_from_fn_single(mock_closure_from_fn, mock_get_datasets, mock_dataset):
    """Test a single function -> returns a single Dataset."""
    # Mock the closure hash
    mock_closure_from_fn.return_value = MagicMock(hash="fn-hash-123")
    mock_get_datasets.return_value = mock_dataset

    def dummy():
        pass

    ds = datasets_from_fn(dummy, page_num=1, page_size=5)

    # single dataset
    assert isinstance(ds, Dataset)

    # from_fn should be called once
    mock_closure_from_fn.assert_called_once_with(dummy)
    # get_datasets should be called with generation_uuid = closure.hash
    mock_get_datasets.assert_called_once_with(
        generation_uuid="fn-hash-123",
        page_num=1,
        page_size=5,
    )


@patch.object(LilypadClient, "get_datasets")
@patch.object(Closure, "from_fn")
def test_datasets_from_fn_multiple(
    mock_closure_from_fn, mock_get_datasets, mock_dataset
):
    """Test multiple functions -> returns a list of Datasets."""
    # Suppose we have two closure hashes
    mock_closure_from_fn.side_effect = [
        MagicMock(hash="hash1"),
        MagicMock(hash="hash2"),
    ]
    mock_get_datasets.side_effect = [mock_dataset, mock_dataset]

    def fn1():
        pass

    def fn2():
        pass

    ds_list = datasets_from_fn(fn1, fn2)

    assert isinstance(ds_list, list)
    assert len(ds_list) == 2

    # from_fn called for each function
    assert mock_closure_from_fn.call_count == 2
    # get_datasets called for each hash
    assert mock_get_datasets.call_count == 2
