"""A decorator for tracing functions."""

import inspect
import json
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar, overload

import requests
from openai import OpenAI

_P = ParamSpec("_P")
_R = TypeVar("_R")

client = OpenAI()


@overload
def trace(fn: Callable[_P, _R]) -> Callable[_P, _R]: ...


@overload
def trace(fn: None = None) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]: ...


def trace(
    fn: Callable[_P, _R] | None = None,
) -> Callable[_P, _R] | Callable[[Callable[_P, _R]], Callable[_P, _R]]:
    """A decorator for tracing functions."""
    if fn is None:

        def decorator(fn: Callable[_P, _R]) -> Callable[_P, _R]:
            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                return fn(*args, **kwargs)

            return inner

        return decorator

    else:

        @wraps(fn)
        def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            url = "http://localhost:8000/calls"

            params_dict: dict[str, Any] = {}
            bound_args = inspect.signature(fn).bind(*args, **kwargs)
            for param_name, param_value in bound_args.arguments.items():
                params_dict[param_name] = param_value
            output = fn(*args, **kwargs)
            input = json.dumps(params_dict)

            data = {
                "project_name": fn.__name__,
                "input": input,
                "output": output,
            }

            try:
                requests.post(url, json=data)
            except requests.exceptions.RequestException as e:
                print(f"An error occurred: {e}")
            return output

        return inner
