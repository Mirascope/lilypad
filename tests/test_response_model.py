"""Tests for the response_model decorator."""

import pytest
from pydantic import BaseModel

from lilypad.response_model import response_model


@response_model()
class MyResponseModel(BaseModel):
    """A response model for a book recommendation."""

    name: str


def test_response_model_methods_exist():
    """Test the response_model and examples methods are present."""
    assert hasattr(MyResponseModel, "response_model")
    assert callable(MyResponseModel.response_model)
    assert hasattr(MyResponseModel, "examples")
    assert callable(MyResponseModel.examples)


def test_response_model_methods():
    """Test the response_model and examples methods."""
    assert MyResponseModel.response_model() is MyResponseModel
    with pytest.raises(ValueError):
        MyResponseModel.examples()
