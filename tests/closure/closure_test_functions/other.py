"""Other functions used in the main closure test functions."""

from collections.abc import Callable
from functools import wraps

from lilypad.closure import Closure


def imported_fn() -> str:
    return "Hello, world!"


def imported_sub_fn() -> str:
    return imported_fn()


class ImportedClass:
    def __call__(self) -> str:
        return "Hello, world!"


class FnInsideClass:
    def __call__(self) -> str:
        return imported_fn()


class SubFnInsideClass:
    def __call__(self) -> str:
        return imported_sub_fn()


class SelfFnClass:
    def fn(self) -> str:
        return "Hello, world!"

    def __call__(self) -> str:
        return self.fn()


def imported_decorator(fn: Callable) -> Callable[[], Closure]:
    @wraps(fn)
    def inner() -> Closure:
        return Closure.from_fn(fn)

    return inner
