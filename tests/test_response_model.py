"""Tests for the response_model decorator."""

from unittest.mock import patch
from uuid import uuid4

import pytest
from pydantic import BaseModel

from lilypad.response_models import response_model
from lilypad.server.models.response_models import ResponseModelPublic


@pytest.fixture
def mock_model_response() -> ResponseModelPublic:
    """Fixture that returns a mock VersionPublic instance"""
    return ResponseModelPublic(
        uuid=uuid4(),
        hash="test_hash",
        project_uuid=uuid4(),
        name="test",
        signature="",
        code="",
        dependencies={},
        schema_data={
            "additionalProperties": True,
            "properties": {
                "name": {"title": "Name", "type": "string"},
                "age": {
                    "description": "The age of the user.",
                    "title": "Age",
                    "type": "integer",
                },
            },
            "required": ["name", "age"],
            "title": "Userinforesponsemodel",
            "type": "object",
        },
        examples=[{"name": "foo", "age": 30}, {"name": "bar", "age": 50}],
        is_active=False,
    )


@pytest.fixture
def mock_prompt_client(mock_model_response: ResponseModelPublic):
    """Fixture that mocks the prompt module's LilypadClient"""
    with patch("lilypad.response_models.lilypad_client") as mock:
        mock.get_response_model_active_version.return_value = mock_model_response
        yield mock


class MyResponseModelBase(BaseModel):
    """A base response model for a book recommendation."""


@response_model()
class MyResponseModel(MyResponseModelBase):
    """A response model for a book recommendation."""

    name: str


def test_response_model_methods_exist():
    """Test the response_model and examples methods are present."""
    assert hasattr(MyResponseModel, "response_model")
    assert callable(MyResponseModel.response_model)
    assert hasattr(MyResponseModel, "examples")
    assert callable(MyResponseModel.examples)


def test_response_model_methods(mock_prompt_client, mock_model_response):
    """Test the response_model and examples methods."""
    assert (
        MyResponseModel.response_model().model_json_schema()
    ), mock_model_response.schema_data
    assert MyResponseModel.examples() == [
        {"age": 30, "name": "foo"},
        {"age": 50, "name": "bar"},
    ]
