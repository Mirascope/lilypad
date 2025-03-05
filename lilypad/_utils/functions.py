"""Utilities for Python functions"""

import inspect
import os
import types
from collections.abc import AsyncIterable, Callable, Coroutine, Iterable
from functools import partial, wraps
from importlib import import_module
from typing import (
    Any,
    ParamSpec,
    TypeAlias,
    TypeVar,
    Union,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from mirascope.core import base as mb
from pydantic import BaseModel

from ..messages import Message
from ..server.schemas.generations import GenerationCreate, GenerationPublic, Provider
from .fn_is_async import fn_is_async

_P = ParamSpec("_P")
_R = TypeVar("_R")

MAP_STANDARD_TYPES = {
    "List": "list",
    "Dict": "dict",
    "Set": "set",
    "Tuple": "tuple",
    "NoneType": "None",
}


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
    if (
        (origin is Union or origin is types.UnionType)
        and len(args) == 2
        and type(None) in args
    ):
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


def inspect_arguments(
    fn: Callable, *args: Any, **kwargs: Any
) -> tuple[ArgTypes, ArgValues]:
    """Inspect a function's arguments and their values.
    Returns type information and values for all arguments.
    """
    sig = inspect.signature(fn)
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


def _construct_call_decorator(
    fn: Callable, provider: Provider, model: str
) -> partial[Any]:
    client = None
    if provider == Provider.OPENROUTER:
        provider = Provider.OPENAI
        if fn_is_async(fn):
            from openai import AsyncOpenAI

            client = AsyncOpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )
        else:
            from openai import OpenAI

            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=os.getenv("OPENROUTER_API_KEY"),
            )

    return partial(
        import_module(f"mirascope.core.{provider.value}").call,
        model=model,
        json_mode=False,
        client=client,
    )


@overload
def create_mirascope_call(
    fn: Callable[_P, Coroutine[Any, Any, _R]],
    generation: GenerationPublic | GenerationCreate,
    provider: Provider,
    model: str,
    trace_decorator: Callable | None,
) -> Callable[_P, Coroutine[Any, Any, _R]]: ...


@overload
def create_mirascope_call(
    fn: Callable[_P, _R],
    generation: GenerationPublic | GenerationCreate,
    provider: Provider,
    model: str,
    trace_decorator: Callable | None,
) -> Callable[_P, _R]: ...


def create_mirascope_call(
    fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
    generation: GenerationPublic | GenerationCreate,
    provider: Provider,
    model: str,
    trace_decorator: Callable | None,
) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
    """Returns the constructed Mirascope call function."""
    if not trace_decorator:
        trace_decorator = lambda x: x  # noqa: E731

    call_decorator = _construct_call_decorator(fn, provider, model)
    return_type = get_type_hints(fn).get("return", type(None))
    if fn_is_async(fn):

        @mb.prompt_template(generation.prompt_template)
        @wraps(fn)
        async def prompt_template_async(
            *args: _P.args, **kwargs: _P.kwargs
        ) -> mb.BaseDynamicConfig:
            return {"call_params": generation.call_params}

        @wraps(fn)
        async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            if return_type is str:
                traced_call = trace_decorator(call_decorator()(prompt_template_async))
                return (await traced_call(*args, **kwargs)).content
            origin_return_type = get_origin(return_type)
            if origin_return_type is AsyncIterable and get_args(return_type) == (str,):
                traced_call = trace_decorator(
                    call_decorator(stream=True)(prompt_template_async)
                )

                async def iterable() -> AsyncIterable[str]:
                    async for chunk, _ in await traced_call(*args, **kwargs):
                        yield chunk.content

                return cast(_R, iterable())
            elif origin_return_type is Message:
                traced_call = trace_decorator(
                    call_decorator(tools=list(get_args(return_type)))(
                        prompt_template_async
                    )
                )
                return cast(_R, Message(await traced_call(*args, **kwargs)))  # pyright: ignore [reportAbstractUsage] # pyright: ignore [reportAbstractUsage]
            elif (
                origin_return_type is AsyncIterable
                and len(iter_args := get_args(return_type)) == 1
                and issubclass((response_model := iter_args[0]), BaseModel)
            ):
                traced_call = trace_decorator(
                    call_decorator(response_model=response_model, stream=True)(
                        prompt_template_async
                    )
                )
                return cast(_R, await traced_call(*args, **kwargs))
            elif (
                inspect.isclass(origin_return_type)
                and issubclass(origin_return_type, Message)
                or (
                    inspect.isclass(return_type)
                    and type(return_type) is not types.GenericAlias
                    and issubclass(return_type, Message)
                )
            ):
                traced_call = trace_decorator(call_decorator()(prompt_template_async))
                return cast(_R, Message(await traced_call(*args, **kwargs)))  # pyright: ignore [reportAbstractUsage]
            elif mb._utils.is_base_type(return_type) or (
                inspect.isclass(return_type)
                and type(return_type) is not types.GenericAlias
                and issubclass(return_type, BaseModel)
            ):
                traced_call = trace_decorator(
                    call_decorator(response_model=return_type)(prompt_template_async)
                )
                return cast(_R, await traced_call(*args, **kwargs))
            else:
                raise ValueError(f"Unsupported return type `{return_type}`.")

        return inner_async
    else:

        @mb.prompt_template(generation.prompt_template)
        @wraps(fn)
        def prompt_template(
            *args: _P.args, **kwargs: _P.kwargs
        ) -> mb.BaseDynamicConfig:
            return {"call_params": generation.call_params}

        @wraps(fn)
        def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
            if return_type is str:
                traced_call = trace_decorator(call_decorator()(prompt_template))
                return traced_call(*args, **kwargs).content
            origin_return_type = get_origin(return_type)
            if origin_return_type is Iterable and get_args(return_type) == (str,):
                traced_call = trace_decorator(
                    call_decorator(stream=True)(prompt_template)
                )

                def iterable() -> Iterable[str]:
                    for chunk, _ in traced_call(*args, **kwargs):
                        yield chunk.content

                return cast(_R, iterable())
            elif origin_return_type is Message:
                traced_call = trace_decorator(
                    call_decorator(tools=list(get_args(return_type)))(prompt_template)
                )
                return cast(_R, Message(traced_call(*args, **kwargs)))  # pyright: ignore [reportAbstractUsage]
            elif (
                origin_return_type is Iterable
                and len(iter_args := get_args(return_type)) == 1
                and issubclass((response_model := iter_args[0]), BaseModel)
            ):
                traced_call = trace_decorator(
                    call_decorator(response_model=response_model, stream=True)(
                        prompt_template
                    )
                )
                return cast(_R, traced_call(*args, **kwargs))
            elif (
                inspect.isclass(origin_return_type)
                and issubclass(origin_return_type, Message)
                or inspect.isclass(return_type)
                and issubclass(return_type, Message)
            ):
                traced_call = trace_decorator(call_decorator()(prompt_template))
                return cast(_R, Message(traced_call(*args, **kwargs)))  # pyright: ignore [reportAbstractUsage]
            elif mb._utils.is_base_type(return_type) or issubclass(
                return_type, BaseModel
            ):
                traced_call = trace_decorator(
                    call_decorator(response_model=return_type)(prompt_template)
                )
                return cast(_R, traced_call(*args, **kwargs))
            else:
                raise ValueError(f"Unsupported return type `{return_type}`.")

        return inner


__all__ = ["inspect_arguments", "create_mirascope_call", "ArgTypes", "ArgValues"]
