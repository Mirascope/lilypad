"""Test cases for the LilypadClient class"""

from unittest.mock import patch

import pytest

from lilypad.server.client import APIConnectionError, LilypadClient, NotFoundError
from lilypad.server.models import ProjectPublic, Scope, SpanPublic


@pytest.fixture
def client():
    """Test client fixture"""
    return LilypadClient(base_url="http://test", timeout=1)


@pytest.fixture
def mock_project_response():
    """Mock project response"""
    return {
        "id": 1,
        "name": "Test Project",
        "created_at": "2024-01-01T00:00:00",
        "functions": [],
        "prompts": [],
        "versions": [],
    }


@pytest.fixture
def mock_spans_response():
    """Mock spans response"""
    return [
        {
            "id": "span-1",
            "project_id": 1,
            "version_id": 1,
            "version_num": 1,
            "scope": "lilypad",  # Changed from "LILYPAD" to "lilypad" to match Enum
            "data": {},
            "parent_span_id": None,
            "created_at": "2024-01-01T00:00:00",
            "display_name": "test_function",
            "version": None,
            "child_spans": [],
        }
    ]


def test_client_initialization():
    """Test client initialization"""
    client = LilypadClient(base_url="http://test", timeout=1)
    assert client.base_url == "http://test"
    assert client.timeout == 1


@pytest.mark.parametrize(
    "method,args,mock_response",
    [
        ("get_health", [], {"status": "ok"}),
        (
            "post_project",
            ["Test Project"],
            {
                "id": 1,
                "name": "Test Project",
                "created_at": "2024-01-01T00:00:00",
                "functions": [],
                "prompts": [],
                "versions": [],
            },
        ),
        (
            "post_traces",
            [],
            [
                {
                    "id": "span-1",
                    "project_id": 1,
                    "version_id": 1,
                    "version_num": 1,
                    "scope": "lilypad",  # Changed from "LILYPAD" to "lilypad"
                    "data": {},
                    "parent_span_id": None,
                    "created_at": "2024-01-01T00:00:00",
                    "display_name": "test_function",
                    "version": None,
                    "child_spans": [],
                }
            ],
        ),
    ],
)
def test_request_methods(client, method, args, mock_response):
    """Test request methods"""
    with patch("requests.Session.request") as mock_request:
        mock_request.return_value.status_code = 200
        mock_request.return_value.json.return_value = mock_response

        result = getattr(client, method)(*args)

        mock_request.assert_called_once()
        assert result is not None
        if method == "post_project":
            assert isinstance(result, ProjectPublic)
        elif method == "post_traces":
            assert isinstance(result, list)
            assert all(isinstance(span, SpanPublic) for span in result)
            assert all(isinstance(span.scope, Scope) for span in result)
            # 追加: scopeの値が正しいEnumであることを確認
            assert result[0].scope == Scope.LILYPAD


def test_request_timeout(client):
    """Test request timeout handling"""
    with patch("requests.Session.request") as mock_request:
        mock_request.side_effect = TimeoutError()

        with pytest.raises(TimeoutError):
            client._request("GET", "/test")


def test_request_not_found(client):
    """Test 404 handling"""
    with patch("requests.Session.request") as mock_request:
        mock_request.return_value.status_code = 404
        mock_request.return_value.raise_for_status.side_effect = NotFoundError()

        with pytest.raises(NotFoundError):
            client._request("GET", "/test")


def test_request_connection_error(client):
    """Test connection error handling"""
    with patch("requests.Session.request") as mock_request:
        mock_request.side_effect = ConnectionError()

        with pytest.raises(APIConnectionError):
            client._request("GET", "/test")