"""Test for the serializer_registry module."""

from dataclasses import dataclass

import pytest

from lilypad._utils.json import fast_jsonable
from lilypad._utils.serializer_registry import register_serializer, get_serializer


@dataclass
class Book:
    title: str
    author: str


@register_serializer(Book)
def _ser_book(b: Book) -> str:
    return f"{b.title} by {b.author}"


def test_global_serializer():
    assert fast_jsonable(Book("Dune", "Herbert")) == "Dune by Herbert"


def test_local_override():
    local = {Book: lambda b: b.title.upper()}
    assert fast_jsonable(Book("Dune", "Herbert"), custom_serializers=local) == "DUNE"


def test_circular_ref():
    a = {}
    a["self"] = a
    assert "<CircularRef dict>" in fast_jsonable(a)


def test_register_duplicate_serializer():
    """Test that registering a serializer for the same type twice raises RuntimeError (line 25)."""

    @dataclass
    class TestClass:
        value: str

    @register_serializer(TestClass)
    def first_serializer(obj: TestClass) -> str:
        return f"first: {obj.value}"

    # Attempting to register a second serializer for the same type should raise RuntimeError
    with pytest.raises(RuntimeError, match="Serializer for TestClass already registered"):

        @register_serializer(TestClass)
        def second_serializer(obj: TestClass) -> str:
            return f"second: {obj.value}"


def test_get_serializer():
    """Test get_serializer function."""

    @dataclass
    class AnotherTestClass:
        name: str

    # Should return None for unregistered types
    assert get_serializer(AnotherTestClass) is None

    # Register a serializer
    @register_serializer(AnotherTestClass)
    def test_serializer(obj: AnotherTestClass) -> str:
        return f"serialized: {obj.name}"

    # Should return the registered serializer
    serializer = get_serializer(AnotherTestClass)
    assert serializer is not None
    assert serializer(AnotherTestClass("test")) == "serialized: test"
