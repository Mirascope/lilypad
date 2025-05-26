"""Utilities for Python functions"""

import types
import inspect
from typing import (
    Any,
    Union,
    TypeVar,
    ParamSpec,
    TypeAlias,
    get_args,
    get_origin,
)
from functools import cache
from collections.abc import Callable

_P = ParamSpec("_P")
_R = TypeVar("_R")

MAP_STANDARD_TYPES = {
    "List": "list",
    "Dict": "dict",
    "Set": "set",
    "Tuple": "tuple",
    "NoneType": "None",
}


@cache
def get_signature(fn: Callable) -> inspect.Signature:
    return inspect.signature(fn)


def _get_type_str(type_hint: Any) -> str:
    """Convert a type hint to its string representation.
    Handles both traditional Optional/Union syntax and new | operator syntax.
    """
    # Handle primitive types and None
    if type_hint is type(None):  # noqa
        return "None"  # Instead of "NoneType"
    if type_hint in (str, int, float, bool):
        return type_hint.__name__

    # Get the origin type
    origin = get_origin(type_hint)
    if origin is None:
        # Handle non-generic types
        if hasattr(type_hint, "__name__"):
            return type_hint.__name__
        return str(type_hint)

    # Handle Optional types (from both syntaxes)
    args = get_args(type_hint)
    if (origin is Union or origin is types.UnionType) and len(args) == 2 and type(None) in args:
        other_type = next(arg for arg in args if arg is not type(None))
        return f"Optional[{_get_type_str(other_type)}]"

    # Handle Union types (both traditional and | operator)
    if origin is Union or origin is types.UnionType:
        formatted_args = [_get_type_str(arg) for arg in args]
        return f"Union[{', '.join(formatted_args)}]"

    # Handle other generic types (List, Dict, etc)
    args_str = ", ".join(_get_type_str(arg) for arg in args)
    if not args:
        return origin.__name__

    return f"{origin.__name__}[{args_str}]"


ArgTypes: TypeAlias = dict[str, str]
ArgValues: TypeAlias = dict[str, Any]


def inspect_arguments(fn: Callable, *args: Any, **kwargs: Any) -> tuple[ArgTypes, ArgValues]:
    """Inspect a function's arguments and their values.
    Returns type information and values for all arguments.
    """
    sig = get_signature(fn)
    params = sig.parameters
    bound_args = sig.bind(*args, **kwargs)
    bound_args.apply_defaults()

    arg_types = {}
    arg_values = {}

    for name, param in params.items():
        if name in bound_args.arguments:
            value = bound_args.arguments[name]
            arg_values[name] = value

            if param.annotation is not param.empty:
                arg_types[name] = _get_type_str(param.annotation)
            else:
                # Infer type from value if no annotation
                arg_types[name] = type(value).__name__

    return arg_types, arg_values


__all__ = [
    "inspect_arguments",
    "ArgTypes",
    "ArgValues",
]
