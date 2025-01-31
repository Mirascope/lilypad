"""Tests for the dataset retrieval API endpoints.
Using function-based pytest style with mocking and FastAPI TestClient.
"""

from collections.abc import Generator
from unittest.mock import MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from lilypad.server.models import GenerationTable, ProjectTable
from lilypad.server.services import GenerationService
from lilypad.server.settings import Settings


@pytest.fixture
def mock_generation_service() -> MagicMock:
    """Fixture that returns a mock for GenerationService.
    We will patch its methods (find_record_by_uuid, find_generations_by_name, etc.) as needed.
    """
    return MagicMock(spec=GenerationService)


@pytest.fixture
def mock_get_settings() -> Generator[Settings, None, None]:
    """Fixture that returns a mock for get_settings."""
    settings = Settings(oxen_repo_name="dummy")
    with patch(
        "lilypad.ee.server.api.v0.datasets_api.get_settings", return_value=settings
    ):
        yield settings


def test_get_dataset_rows_by_uuid_success(
    client: TestClient,
    test_project: ProjectTable,
    test_generation: GenerationTable,
    mock_get_settings: Settings,
):
    """Test a successful request to get_dataset_rows_by_uuid."""
    from lilypad.ee.server.api.v0.datasets_api import DatasetRowsResponse

    with patch.object(
        DatasetRowsResponse,
        "from_metadata",
        return_value=DatasetRowsResponse(rows=[{"col1": "val1"}, {"col1": "val2"}]),
    ):
        response = client.get(
            f"/projects/{test_project.uuid}/datasets/{test_generation.uuid}"
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # The endpoint returns DatasetRowsResponse
    assert "rows" in data
    assert len(data["rows"]) == 2
    assert data["rows"][0] == {"col1": "val1"}


def test_get_dataset_rows_by_uuid_not_found(
    client: TestClient,
    test_project: ProjectTable,
    test_generation: GenerationTable,
    mock_get_settings: Settings,
):
    """If generation_service.find_record_by_uuid raises an exception,
    we expect a 400 BAD REQUEST.
    """
    uuid = uuid4()
    response = client.get(f"/projects/{test_project.uuid}/datasets/{uuid}")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Could not resolve metadata" in response.text


def test_get_dataset_rows_by_uuid_dataframe_error(
    client: TestClient,
    test_project: ProjectTable,
    test_generation: GenerationTable,
    mock_get_settings: Settings,
):
    """If DataFrame.list_page raises an exception, we expect a 500 INTERNAL SERVER ERROR."""
    from lilypad.ee.server.api.v0.datasets_api import DatasetRowsResponse

    with patch.object(
        DatasetRowsResponse, "from_metadata", side_effect=Exception("DataFrame error!")
    ):
        response = client.get(
            f"/projects/{test_project.uuid}/datasets/{test_generation.uuid}"
        )
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "Error initializing Oxen DataFrame: DataFrame error!" in response.text


def test_get_dataset_rows_by_hash_success(
    client: TestClient,
    test_project: ProjectTable,
    test_generation: GenerationTable,
    mock_get_settings: Settings,
):
    """Test retrieving rows via generation hash."""
    from lilypad.ee.server.api.v0.datasets_api import DatasetRowsResponse

    with patch.object(
        DatasetRowsResponse,
        "from_metadata",
        return_value=DatasetRowsResponse(rows=[{"row": "hash_val"}]),
    ):
        response = client.get(
            f"/projects/{test_project.uuid}/datasets/hash/{test_generation.hash}"
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "rows" in data
    assert data["rows"] == [{"row": "hash_val"}]


def test_get_dataset_rows_by_hash_error(
    client: TestClient,
    test_project: ProjectTable,
    test_generation: GenerationTable,
    mock_get_settings: Settings,
):
    """If we cannot resolve the hash or the DataFrame fails, we expect a 400 or 500 error."""
    generation_hash = uuid4()

    response = client.get(
        f"/projects/{test_project.uuid}/datasets/hash/{generation_hash}"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "Could not resolve metadata" in response.text


def test_get_dataset_rows_by_name_success(
    client: TestClient,
    test_project: ProjectTable,
    test_generation: GenerationTable,
    mock_get_settings: Settings,
):
    """Test retrieving dataset rows by generation name."""
    from lilypad.ee.server.api.v0.datasets_api import DatasetRowsResponse

    rows_gen1 = DatasetRowsResponse(rows=[{"id": "g1_r1"}, {"id": "g1_r2"}])
    rows_gen2 = DatasetRowsResponse(rows=[{"id": "g2_r1"}])

    with patch.object(
        DatasetRowsResponse, "from_metadata", side_effect=[rows_gen1, rows_gen2]
    ):
        response = client.get(
            f"/projects/{test_project.uuid}/datasets/names/{test_generation.name}"
        )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "rows" in data
    assert len(data["rows"]) == 3
    assert data == {
        "next_page": None,
        "rows": [{"id": "g1_r1"}, {"id": "g1_r2"}, {"id": "g2_r1"}],
    }


def test_get_dataset_rows_by_name_error(
    client: TestClient,
    test_project: ProjectTable,
    test_generation: GenerationTable,
    mock_get_settings: Settings,
):
    """If the generation_service fails to find the name, we expect a 400 error."""
    response = client.get(f"/projects/{test_project.uuid}/datasets/names/invalid-name")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert "No generations found by name." in response.text
