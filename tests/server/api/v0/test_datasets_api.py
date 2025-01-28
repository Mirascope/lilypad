"""
Tests for the `get_dataset_rows` endpoint in the server's datasets router.
Function-based pytest style.
"""

import pytest
from unittest.mock import patch, MagicMock
from fastapi import status
from fastapi.testclient import TestClient
from uuid import uuid4

from lilypad.server.api.v0.main import api
from lilypad.server.db.session import get_session


@pytest.fixture
def client():
    """
    Create a TestClient for the FastAPI `api` router.
    We'll override dependencies if needed.
    """
    return TestClient(api)


def test_get_dataset_rows_no_params(client):
    """
    If no `generation_uuid` or `generation_name` is provided,
    the endpoint should return 400.
    """
    project_uuid = uuid4()
    response = client.get(f"/v0/projects/{project_uuid}/datasets")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Must provide either 'generation_uuid' or 'generation_name'" in response.text


@patch("lilypad.server.api.v0.routers.datasets.DataFrame")
@patch("lilypad.server.api.v0.routers.datasets._get_oxen_dataset_metadata")
def test_get_dataset_rows_success(
    mock_get_meta, mock_dataframe, client
):
    """
    Test a successful case where the endpoint returns rows from the Oxen DataFrame.
    """
    project_uuid = uuid4()

    # Mock the metadata so we don't worry about the service layer
    mock_meta = MagicMock()
    mock_meta.repo_url = "https://hub.oxen.ai/namespace/repo"
    mock_meta.branch = "main"
    mock_meta.path = "data.csv"
    mock_get_meta.return_value = mock_meta

    # Mock the DataFrame object
    mock_df_instance = MagicMock()
    mock_df_instance.list_page.return_value = [
        {"id": "row1"},
        {"id": "row2"}
    ]
    mock_dataframe.return_value = mock_df_instance

    # Call the endpoint
    response = client.get(f"/v0/projects/{project_uuid}/datasets?generation_uuid=my-gen-uuid&page_num=2&page_size=100")
    assert response.status_code == 200
    data = response.json()
    assert "rows" in data
    assert data["rows"] == [{"id": "row1"}, {"id": "row2"}]

    # Ensure the mocks were called
    mock_get_meta.assert_called_once_with("my-gen-uuid")
    mock_dataframe.assert_called_once()
    mock_df_instance.list_page.assert_called_once_with(2)


@patch("lilypad.server.api.v0.routers.datasets.DataFrame")
@patch("lilypad.server.api.v0.routers.datasets._get_oxen_dataset_metadata")
def test_get_dataset_rows_oxen_exception(
    mock_get_meta, mock_dataframe, client
):
    """
    If constructing DataFrame raises an exception, the endpoint should return 500.
    """
    project_uuid = uuid4()
    mock_get_meta.return_value = MagicMock(
        repo_url="https://hub.oxen.ai/namespace/repo",
        branch="main",
        path="data.csv"
    )

    mock_dataframe.side_effect = Exception("Oxen error!")

    response = client.get(f"/v0/projects/{project_uuid}/datasets?generation_uuid=abc")
    assert response.status_code == 500
    assert "Error initializing Oxen DataFrame" in response.text


def test_get_dataset_rows_mock_datasets_service(client):
    """
    Example of overriding the `DatasetsService` dependency if needed.
    Not strictly required if your real service is tested, but shown here.
    """
    # Optional demonstration of how to override the "datasets_service" dependency
    pass  # Implementation depends on your project structure
