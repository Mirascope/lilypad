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

from lilypad_sdk import LilypadSDK

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
                output = await fn(*args, **kwargs)
                Thread(target=api_request, args=((fn, input, output))).start()
                return output
                ...

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                output = fn(*args, **kwargs)
                input = inspect_arguments(*args, **kwargs)
                Thread(target=api_request, args=((fn, input, output))).start()
                return output

            return inner

    return decorator


def api_request(fn: Callable, input: dict[str, dict[str, Any]], output: str) -> None:
    hash, lexical_closure = compute_function_hash(fn)
    input_types: dict[str, type[Any]] = {}
    input_values: dict[str, Any] = {}

    for arg_name, arg_info in input.items():
        input_types[arg_name] = arg_info["type"]
        input_values[arg_name] = arg_info["value"]
    prompt_version_id = client.prompt_versions.retrieve(version_hash=hash)
    if prompt_version_id == -1:
        print("New version detected")
        prompt_version = client.prompt_versions.create(
            function_name=fn.__name__,
            version_hash=hash,
            lexical_closure=lexical_closure,
            prompt_template="",
            input_arguments=json.dumps(input_types),
        )
        prompt_version_id = prompt_version.id
    call = client.calls.create(
        prompt_version_id=prompt_version_id,
        input=json.dumps(input_values),
        output=output,
    )

    print(f"API request complete {call.model_dump()}")
