"""Test for the serializer_registry module."""

from dataclasses import dataclass

from lilypad.lib._utils.json import fast_jsonable
from lilypad.lib._utils.serializer_registry import register_serializer


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
