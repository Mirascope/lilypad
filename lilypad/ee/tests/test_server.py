"""Test cases for the LilypadClient class related to Oxen dataset rows."""

from unittest.mock import patch

import pytest
from requests import Timeout

from lilypad.ee.server.client import OxenDatasetResponse
from lilypad.server.client import (
    NotFoundError,
)
from lilypad.ee.server.client import LilypadClient


@pytest.fixture
def client():
    """Test client fixture with a sample base_url and small timeout."""
    client = LilypadClient(base_url="http://testserver", timeout=1)
    client.project_uuid = "fake-project-uuid"
    return client


@pytest.fixture
def mock_oxen_dataset_response():
    """Mock response that matches the OxenDatasetResponse schema.
    The nested fields (commit, data_frame, etc.) are partial stubs.
    Adjust as needed for your real use-case.
    """
    return {
        "commit": {
            "author": "Test Author",
            "email": "author@example.com",
            "id": "abcd1234",
            "message": "Adding smol dataset",
            "parent_ids": ["ec0e7b6465f631c9a245691d5b682ab2"],
            "root_hash": None,
            "timestamp": "2024-11-29T22:22:16.339175Z",
        },
        "data_frame": {
            "source": {
                "schema": {
                    "fields": [
                        {
                            "changes": None,
                            "dtype": "str",
                            "metadata": None,
                            "name": "id",
                        },
                        {
                            "changes": None,
                            "dtype": "str",
                            "metadata": None,
                            "name": "text",
                        },
                    ],
                    "hash": "123abc",
                    "metadata": None,
                },
                "size": {
                    "height": 3,
                    "width": 2
                },
            },
            "view": {
                "data": [
                    {
                        "id": "101",
                        "text": "Hello world",
                        "title": "Greeting",
                        "url": "https://example.com/hello"
                    },
                    {
                        "id": "202",
                        "text": "Another row",
                        "title": "Row2",
                        "url": "https://example.com/row2"
                    }
                ],
                "opts": [
                    {"name": "filter", "value": None},
                    {"name": "sort_by", "value": "id"}
                ],
                "pagination": {
                    "page_number": 1,
                    "page_size": 50,
                    "total_entries": 100,
                    "total_pages": 2
                },
                "schema": {
                    "fields": [
                        {
                            "changes": None,
                            "dtype": "str",
                            "metadata": None,
                            "name": "id",
                        },
                        {
                            "changes": None,
                            "dtype": "str",
                            "metadata": None,
                            "name": "text",
                        },
                        {
                            "changes": None,
                            "dtype": "str",
                            "metadata": None,
                            "name": "title",
                        },
                        {
                            "changes": None,
                            "dtype": "str",
                            "metadata": None,
                            "name": "url",
                        },
                    ],
                    "hash": "456def",
                    "metadata": None,
                },
                "size": {
                    "height": 2,
                    "width": 4
                }
            },
        },
        "derived_resource": None,
        "oxen_version": "0.22.2",
        "request_params": {
            "namespace": "ox",
            "repo_name": "TestRepo",
            "resource": ["main", "my_data.parquet"]
        },
        "resource": {
            "path": "my_data.parquet",
            "version": "main"
        },
        "status": "success",
        "status_message": "resource_found"
    }


def test_get_dataset_rows_success(client, mock_oxen_dataset_response):
    """Test that get_dataset_rows() successfully returns
    OxenDatasetResponse and we can parse nested fields.
    """
    with patch("requests.Session.request") as mock_request:
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = mock_oxen_dataset_response

        # Simulate retrieval
        generation_uuid = "fake-gen-id"
        resp = client.get_dataset_rows(generation_uuid=generation_uuid)

        mock_request.assert_called_once()
        assert isinstance(resp, OxenDatasetResponse)

        # Check top-level fields
        assert resp.status == "success"
        assert resp.status_message == "resource_found"
        assert resp.commit.id == "abcd1234"
        assert resp.data_frame.source.size.height == 3

        # Check row data
        data_rows = resp.data_frame.view.data
        assert len(data_rows) == 2
        assert data_rows[0].id == "101"
        assert data_rows[0].text == "Hello world"


def test_get_dataset_rows_404(client):
    """Test that a 404 from the server raises NotFoundError
    """
    with patch("requests.Session.request") as mock_request:
        mock_request.return_value.status_code = 404
        # .raise_for_status() triggers an HTTPError
        mock_request.return_value.raise_for_status.side_effect = NotFoundError()

        with pytest.raises(NotFoundError):
            client.get_dataset_rows(generation_uuid="non-existent")


def test_get_dataset_rows_timeout(client):
    """Test that a timeout from the server is handled.
    """
    with patch("requests.Session.request") as mock_request:
        # raise python's Timeout (or requests.exceptions.Timeout)
        mock_request.side_effect = Timeout()

        with pytest.raises(Timeout):
            client.get_dataset_rows(generation_uuid="some-gen")
