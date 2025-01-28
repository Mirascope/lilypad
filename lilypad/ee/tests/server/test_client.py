"""Tests for the LilypadClient class in lilypad.ee.server.client."""

from unittest.mock import patch

import pytest

from lilypad.ee.server.client import (
    APIConnectionError,
    DatasetRowsResponse,
    LilypadClient,
    NotFoundError,
)
from lilypad.ee.server.client import LilypadClient as BaseLilypadClient


def test_get_dataset_rows_no_project_uuid():
    """Test that calling get_dataset_rows without a project UUID raises a ValueError."""
    client = LilypadClient()
    client.project_uuid = None  # Explicitly ensure it's not set

    with pytest.raises(ValueError, match="No project_uuid is set in LilypadClient"):
        client.get_dataset_rows(generation_uuid="some-uuid")


@patch.object(BaseLilypadClient, "_request")
def test_get_dataset_rows_with_generation_uuid(mock_request):
    """Test get_dataset_rows with a generation_uuid, ensuring the correct endpoint and response_model."""
    # Set up the mock return value to simulate the API response
    mock_request.return_value = DatasetRowsResponse(rows=[{"col1": "val1"}])

    client = LilypadClient()
    client.project_uuid = "test-project-uuid"

    response = client.get_dataset_rows(generation_uuid="test-uuid", page_num=2)

    assert isinstance(
        response, DatasetRowsResponse
    ), "Should return a DatasetRowsResponse object"
    assert response.rows == [{"col1": "val1"}], "Should match the mocked rows"

    # Verify the _request call was made with correct arguments
    mock_request.assert_called_once()
    call_args, call_kwargs = mock_request.call_args
    assert call_kwargs["method"] == "GET", "Method should be GET"
    assert (
        call_kwargs["endpoint"] == "/v0/projects/test-project-uuid/datasets/test-uuid"
    )
    assert call_kwargs["response_model"] is DatasetRowsResponse
    assert call_kwargs["params"] == {"page_num": 2}, "Should pass page_num in params"


@patch.object(BaseLilypadClient, "_request")
def test_get_dataset_rows_with_generation_name(mock_request):
    """Test get_dataset_rows with a generation_name, ensuring the correct endpoint and response_model."""
    mock_request.return_value = DatasetRowsResponse(rows=[{"col2": 123}])

    client = LilypadClient()
    client.project_uuid = "test-project-uuid"

    response = client.get_dataset_rows(generation_name="my-gen-name", page_num=3)

    assert response.rows == [{"col2": 123}], "Should match the mocked rows"

    mock_request.assert_called_once()
    call_args, call_kwargs = mock_request.call_args
    assert (
        call_kwargs["endpoint"]
        == "/v0/projects/test-project-uuid/datasets/names/my-gen-name"
    )
    assert call_kwargs["params"] == {"page_num": 3}, "Should pass page_num in params"


@patch.object(BaseLilypadClient, "_request")
def test_get_dataset_rows_with_generation_hash(mock_request):
    """Test get_dataset_rows with a generation_hash, ensuring the correct endpoint and response_model."""
    mock_request.return_value = DatasetRowsResponse(rows=[{"hash_col": "some-hash"}])

    client = LilypadClient()
    client.project_uuid = "test-project-uuid"

    response = client.get_dataset_rows(generation_hash="abcdef1234")

    assert response.rows == [{"hash_col": "some-hash"}]

    mock_request.assert_called_once()
    call_args, call_kwargs = mock_request.call_args
    assert (
        call_kwargs["endpoint"]
        == "/v0/projects/test-project-uuid/datasets/hash/abcdef1234"
    )


def test_get_dataset_rows_no_params():
    """Test get_dataset_rows with no generation_uuid, generation_name, or generation_hash.
    Expect a ValueError.
    """
    client = LilypadClient()
    client.project_uuid = "test-project-uuid"

    with pytest.raises(ValueError, match="Must provide either generation_uuid"):
        client.get_dataset_rows()


@patch.object(BaseLilypadClient, "_request")
def test_get_dataset_rows_connection_error(mock_request):
    """Test get_dataset_rows handling an APIConnectionError from the underlying _request."""
    mock_request.side_effect = APIConnectionError("Simulated connection error")

    client = LilypadClient()
    client.project_uuid = "test-project-uuid"

    with pytest.raises(APIConnectionError, match="Simulated connection error"):
        client.get_dataset_rows(generation_uuid="any-uuid")


@patch.object(BaseLilypadClient, "_request")
def test_get_dataset_rows_not_found_error(mock_request):
    """Test get_dataset_rows handling a NotFoundError from the underlying _request."""
    mock_request.side_effect = NotFoundError("Resource not found")

    client = LilypadClient()
    client.project_uuid = "test-project-uuid"

    with pytest.raises(NotFoundError, match="Resource not found"):
        client.get_dataset_rows(generation_name="missing-gen-name")
