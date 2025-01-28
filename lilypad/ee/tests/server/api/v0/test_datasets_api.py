"""unitest for datasets api"""

from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi.testclient import TestClient


def test_get_dataset_rows_no_params(client: TestClient) -> None:
    """If neither 'generation_uuid' nor 'generation_name' is provided,
    the endpoint should return a 400 Bad Request.
    """
    project_uuid = uuid4()
    response = client.get(f"/projects/{project_uuid}/datasets")
    assert response.status_code == 400, response.text
    assert "Must provide either 'generation_uuid' or 'generation_name'" in response.text


@patch("lilypad.ee.server.api.v0.datasets_api.DataFrame")
@patch("lilypad.ee.server.api.v0.datasets_api._get_oxen_dataset_metadata")
def test_get_dataset_rows_success(
    mock_get_meta: MagicMock, mock_dataframe: MagicMock, client: TestClient
) -> None:
    """Test a successful case: _get_oxen_dataset_metadata and DataFrame
    should be called, and the endpoint should return rows with 200 OK.
    """
    project_uuid = uuid4()

    # Mock metadata object
    mock_meta = MagicMock()
    mock_meta.repo_url = "https://hub.oxen.ai/my-namespace/my-repo"
    mock_meta.branch = "main"
    mock_meta.path = "data.csv"
    mock_meta.host = "hub.oxen.ai"
    mock_get_meta.return_value = mock_meta

    # Mock DataFrame
    mock_df_instance = MagicMock()
    mock_df_instance.list_page.return_value = [
        {"id": "row1"},
        {"id": "row2"},
    ]
    mock_dataframe.return_value = mock_df_instance

    # Call the endpoint with generation_uuid and pagination params
    response = client.get(
        f"/projects/{project_uuid}/datasets?generation_uuid=abc&page_num=2&page_size=100"
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "rows" in data
    assert data["rows"] == [{"id": "row1"}, {"id": "row2"}]

    # Check that mocks were invoked correctly
    mock_get_meta.assert_called_once_with("abc")
    mock_dataframe.assert_called_once_with(
        remote="https://hub.oxen.ai/my-namespace/my-repo",
        path="data.csv",
        branch="main",
        host="hub.oxen.ai",
    )
    mock_df_instance.list_page.assert_called_once_with(2)


@patch("lilypad.ee.server.api.v0.datasets_api.DataFrame")
@patch("lilypad.ee.server.api.v0.datasets_api._get_oxen_dataset_metadata")
def test_get_dataset_rows_oxen_exception(
    mock_get_meta: MagicMock, mock_dataframe: MagicMock, client: TestClient
) -> None:
    """If DataFrame constructor raises an exception, the endpoint should return 500."""
    project_uuid = uuid4()
    mock_meta = MagicMock()
    mock_meta.repo_url = "https://hub.oxen.ai/my-namespace/my-repo"
    mock_meta.branch = "main"
    mock_meta.path = "data.csv"
    mock_meta.host = "hub.oxen.ai"
    mock_get_meta.return_value = mock_meta

    # Force DataFrame(...) to raise an exception
    mock_dataframe.side_effect = Exception("Oxen error!")

    response = client.get(f"/projects/{project_uuid}/datasets?generation_uuid=foo")
    assert response.status_code == 500, response.text
    assert "Error initializing Oxen DataFrame: Oxen error!" in response.text
