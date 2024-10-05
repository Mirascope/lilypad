"""The lilypad `prompt` decorator."""

import inspect
import json
from collections.abc import Callable, Coroutine
from functools import wraps
from threading import Thread
from typing import (
    Any,
    ParamSpec,
    Protocol,
    TypeVar,
    overload,
)

import lilypad_sdk
import requests
from lilypad_sdk import LilypadSDK
from opentelemetry.trace import get_tracer
from opentelemetry.util.types import AttributeValue

from lilypad import lexical_closure
from lilypad.trace import trace

from .lexical_closure import compute_function_hash
from .utils import fn_is_async

_P = ParamSpec("_P")
_R = TypeVar("_R")

client = LilypadSDK(base_url="http://localhost:8000/api")


class Prompt(Protocol):
    """Protocol for the `prompt` decorator return type."""

    @overload
    def __call__(
        self, fn: Callable[_P, Coroutine[Any, Any, _R]]
    ) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def __call__(self, fn: Callable[_P, _R]) -> Callable[_P, _R]: ...

    def __call__(
        self, fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        """Protocol `call` definition for `prompt` decorator return type."""
        ...


def prompt() -> Prompt:
    """Returns a decorator for turining a typed function into an LLM API call."""

    @overload
    def decorator(
        fn: Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def decorator(fn: Callable[_P, _R]) -> Callable[_P, _R]: ...

    def decorator(
        fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        def stringify_type(t: Any) -> str:
            """Convert a type or annotation to a string."""
            if hasattr(t, "__name__"):
                return t.__name__
            else:
                return str(t)

        def inspect_arguments(
            *args: _P.args, **kwargs: _P.kwargs
        ) -> dict[str, dict[str, Any]]:
            # Get the function's signature
            signature = inspect.signature(fn)
            # Bind the passed arguments to the function's parameters
            bound_args = signature.bind(*args, **kwargs)
            bound_args.apply_defaults()

            # Create a dictionary to hold the argument information
            arguments: dict[str, dict[str, Any]] = {}
            for name, param in signature.parameters.items():
                arg_value = bound_args.arguments.get(name, param.default)
                if param.annotation != inspect.Parameter.empty:
                    arg_type = param.annotation
                else:
                    arg_type = type(arg_value)
                arg_type_str = stringify_type(arg_type)
                arguments[name] = {"type": arg_type_str, "value": arg_value}
            return arguments

        if fn_is_async(fn):

            @wraps(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                input = inspect_arguments(*args, **kwargs)
                hash, code = compute_function_hash(fn)
                input_types: dict[str, type[Any]] = {}
                input_values: dict[str, Any] = {}

                for arg_name, arg_info in input.items():
                    input_types[arg_name] = arg_info["type"]
                    input_values[arg_name] = arg_info["value"]
                try:
                    llm_version = client.llm_functions.retrieve(hash)
                except lilypad_sdk.NotFoundError:
                    print("New version detected")
                    llm_version = client.llm_functions.create(
                        function_name=fn.__name__,
                        code=code,
                        version_hash=hash,
                        input_arguments=json.dumps(input_types),
                    )
                decorated_trace = trace(
                    llm_version_id=llm_version.id,
                    input_values=input_values,
                    input_types=input_types,
                    lexical_closure=code,
                )(fn)
                return await decorated_trace(*args, **kwargs)

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                input = inspect_arguments(*args, **kwargs)
                hash, code = compute_function_hash(fn)
                input_types: dict[str, type[Any]] = {}
                input_values: dict[str, Any] = {}

                for arg_name, arg_info in input.items():
                    input_types[arg_name] = arg_info["type"]
                    input_values[arg_name] = arg_info["value"]
                try:
                    llm_version = client.llm_functions.retrieve(hash)
                except lilypad_sdk.NotFoundError:
                    print("New version detected")
                    llm_version = client.llm_functions.create(
                        function_name=fn.__name__,
                        code=code,
                        version_hash=hash,
                        input_arguments=json.dumps(input_types),
                    )
                decorated_trace = trace(
                    llm_version_id=llm_version.id,
                    input_values=input_values,
                    input_types=input_types,
                    lexical_closure=code,
                )(fn)
                return decorated_trace(*args, **kwargs)

            return inner

    return decorator
