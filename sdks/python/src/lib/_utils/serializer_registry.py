"""Serializer registry for custom serialization functions."""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, TypeVar, Callable
from threading import RLock

_lock = RLock()

T = TypeVar("T")

_serializer_registry: dict[type[Any], Callable[[Any], str]] = {}

SerializerMap = dict[type[Any], Callable[[Any], str]]


def register_serializer(type_: type[T]) -> Callable[[Callable[[T], str]], Callable[[T], str]]:
    """Decorator that registers *type_* to be serialized by *fn*."""

    def decorator(fn: Callable[[T], str]) -> Callable[[T], str]:
        with _lock:
            if type_ in _serializer_registry:
                raise RuntimeError(f"Serializer for {type_.__name__} already registered")
            _serializer_registry[type_] = fn
        return fn

    return decorator


def get_serializer(type_: type[Any]) -> Callable[[Any], str] | None:
    """Return a custom serializer for *type_* if one has been registered."""
    return _serializer_registry.get(type_)


SERIALIZER_REGISTRY = MappingProxyType(_serializer_registry)

__all__ = ["get_serializer", "register_serializer", "SERIALIZER_REGISTRY", "SerializerMap"]
