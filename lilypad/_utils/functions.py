"""Utilities for Python functions"""

import inspect
import os
from collections.abc import AsyncIterable, Callable, Coroutine, Iterable
from functools import partial, wraps
from importlib import import_module
from types import NoneType
from typing import (
    Any,
    ParamSpec,
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
from ..server.models import PromptPublic, Provider

_P = ParamSpec("_P")
_R = TypeVar("_R")

MAP_STANDARD_TYPES = {
    "List": "list",
    "Dict": "dict",
    "Set": "set",
    "Tuple": "tuple",
    "NoneType": "None",
}


def _get_type_str(type_: type) -> str | None:
    """Returns the string representation of the type."""
    type_str = type_.__name__ if hasattr(type_, "__name__") else str(type_)
    if type_str in MAP_STANDARD_TYPES:
        type_str = MAP_STANDARD_TYPES[type_str]

    is_optional = get_origin(type_) is Union and type_.__name__ == "Optional"
    if arg_types := get_args(type_):
        arg_type_strs = (
            arg_type_str
            for arg in arg_types
            if not (is_optional and arg is NoneType)
            and (arg_type_str := _get_type_str(arg))
        )
        if " | " in type_str:
            # New style union type
            return " | ".join(arg_type_strs)
        return f"{type_str}[{', '.join(arg_type_strs)}]"
    return type_str


def inspect_arguments(
    fn: Callable[_P, _R], *args: _P.args, **kwargs: _P.kwargs
) -> tuple[dict[str, str], dict[str, Any]]:
    """Returns mappings from argument names to their types and values, respectively."""
    signature = inspect.signature(fn)
    bound_args = signature.bind(*args, **kwargs)
    bound_args.apply_defaults()

    arg_types, arg_values = {}, {}
    for name, param in signature.parameters.items():
        arg_values[name] = bound_args.arguments.get(name, param.default)
        arg_type = (
            param.annotation
            if param.annotation != inspect.Parameter.empty
            else type(arg_values[name])
        )
        arg_types[name] = _get_type_str(arg_type)

    return arg_types, arg_values


def _construct_call_decorator(fn: Callable, prompt: PromptPublic) -> partial[Any]:
    provider, client = prompt.provider.value, None
    if prompt.provider.value == "openrouter":
        provider = "openai"
        if inspect.iscoroutinefunction(fn):
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
        import_module(f"mirascope.core.{provider}").call,
        model=prompt.model,
        json_mode=False,
        client=client,
    )


@overload
def create_mirascope_call(
    fn: Callable[_P, Coroutine[Any, Any, _R]],
    prompt: PromptPublic,
    trace_decorator: Callable | None,
) -> Callable[_P, Coroutine[Any, Any, _R]]: ...


@overload
def create_mirascope_call(
    fn: Callable[_P, _R],
    prompt: PromptPublic,
    trace_decorator: Callable | None,
) -> Callable[_P, _R]: ...


def create_mirascope_call(
    fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
    prompt: PromptPublic,
    trace_decorator: Callable | None,
) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
    """Returns the constructed Mirascope call function."""
    if not trace_decorator:
        trace_decorator = lambda x: x  # noqa: E731

    call_decorator = _construct_call_decorator(fn, prompt)
    return_type = get_type_hints(fn).get("return", type(None))
    if inspect.iscoroutinefunction(fn):

        @mb.prompt_template(prompt.template)
        @wraps(fn)
        async def prompt_template_async(
            *args: _P.args, **kwargs: _P.kwargs
        ) -> mb.BaseDynamicConfig:
            if prompt.provider == Provider.GEMINI:
                return {
                    "call_params": {
                        "generation_config": prompt.call_params.model_dump(
                            exclude_defaults=True
                        )
                    }
                    if prompt.call_params
                    else {}
                }
            return {
                "call_params": prompt.call_params.model_dump(exclude_defaults=True)
                if prompt.call_params
                else {}
            }

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
                origin_return_type is Iterable
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
                    or inspect.isclass(return_type)
                    and issubclass(return_type, Message)
            ):
                traced_call = trace_decorator(call_decorator()(prompt_template_async))
                return cast(_R, Message(await traced_call(*args, **kwargs)))  # pyright: ignore [reportAbstractUsage]
            elif mb._utils.is_base_type(return_type) or issubclass(
                return_type, BaseModel
            ):
                traced_call = trace_decorator(
                    call_decorator(response_model=return_type)(prompt_template_async)
                )
                return cast(_R, await traced_call(*args, **kwargs))
            else:
                raise ValueError(f"Unsupported return type `{return_type}`.")

        return inner_async
    else:

        @mb.prompt_template(prompt.template)
        @wraps(fn)
        def prompt_template(
            *args: _P.args, **kwargs: _P.kwargs
        ) -> mb.BaseDynamicConfig:
            if prompt.provider == Provider.GEMINI:
                return {
                    "call_params": {
                        "generation_config": prompt.call_params.model_dump(
                            exclude_defaults=True
                        )
                    }
                    if prompt.call_params
                    else {}
                }
            return {
                "call_params": prompt.call_params.model_dump(exclude_defaults=True)
                if prompt.call_params
                else {}
            }

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


__all__ = ["inspect_arguments", "create_mirascope_call"]
