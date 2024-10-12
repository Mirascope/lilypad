"""Utilities for the `lilypad` library."""

import inspect
import json
import os
import time
import webbrowser
from collections.abc import AsyncIterable, Callable, Coroutine, Iterable
from functools import partial, wraps
from importlib import import_module
from typing import Any, ParamSpec, TypeVar, cast, get_args, get_origin, get_type_hints

from mirascope.core import base as mb
from pydantic import BaseModel

from lilypad.models import FnParamsPublic, VersionPublic
from lilypad.server import client

from ._lexical_closure import compute_function_hash
from .messages import Message

_P = ParamSpec("_P")
_R = TypeVar("_R")

lilypad_client = client.LilypadClient(base_url="http://localhost:8000/api", timeout=10)


def stringify_type(t: Any) -> str:  # noqa: ANN401
    """Convert a type or annotation to a string."""
    if hasattr(t, "__name__"):
        return t.__name__
    else:
        return str(t)


def poll_active_version(
    hash: str, function_name: str, fn_params_hash: str | None = None
) -> VersionPublic:
    """Polls the LLM API for the active version."""
    while True:
        try:
            active_version = lilypad_client.get_active_version_by_function_name(
                function_name
            )
            if (
                os.getenv("LILYPAD_EDITOR_OPEN") == "True"
                and fn_params_hash
                and active_version.fn_params
                and fn_params_hash == active_version.fn_params.hash
            ) or active_version.llm_function_hash != hash:
                continue
        except client.NotFoundError:
            time.sleep(1)
            continue
        except client.APIConnectionError:
            time.sleep(1)
            continue
        else:
            return active_version


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
        arg_types[name] = stringify_type(
            param.annotation
            if param.annotation != inspect.Parameter.empty
            else type(arg_values[name])
        )

    return arg_types, arg_values


def get_llm_function_version(
    fn: Callable, arg_types: dict[str, str], synced: bool
) -> VersionPublic:
    """Returns the active version for the given function."""
    hash, code = compute_function_hash(fn)

    try:
        llm_fn_version = lilypad_client.get_llm_function_by_hash(hash)
    except client.NotFoundError:
        llm_fn_version = lilypad_client.post_llm_function(
            function_name=fn.__name__,
            code=code,
            version_hash=hash,
            arg_types=arg_types,
        )

    try:
        active_version = lilypad_client.get_active_version_by_function_name(fn.__name__)
    except client.NotFoundError:
        active_version = None

    if not synced and (not active_version or active_version.llm_function_hash != hash):
        lilypad_client.create_non_synced_version(llm_fn_version.id, fn.__name__)
    elif synced and (
        os.getenv("LILYPAD_EDITOR_OPEN") == "True"
        or not llm_fn_version.fn_params
        or (active_version and active_version.llm_function_hash != hash)
    ):
        webbrowser.open(lilypad_client.get_editor_url(llm_fn_version.id))

    return poll_active_version(
        hash,
        fn.__name__,
        active_version.fn_params.hash
        if active_version and active_version.fn_params
        else None,
    )


def traced_synced_llm_function_constructor(
    fn_params: FnParamsPublic, trace_decorator: Callable | None
) -> Callable[
    [Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]],
    Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
]:
    """Returns a method for converting a function signature into a traced/synced fn."""
    if not trace_decorator:
        trace_decorator = lambda x: x  # noqa: E731

    call_decorator = partial(
        import_module(f"mirascope.core.{fn_params.provider.value}").call,
        model=fn_params.model,
        json_mode=False,
    )

    def decorator(
        fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        return_type = get_type_hints(fn).get("return", type(None))
        if inspect.iscoroutinefunction(fn):

            @mb.prompt_template(fn_params.prompt_template)
            @wraps(fn)
            async def prompt_template_async(
                *args: _P.args, **kwargs: _P.kwargs
            ) -> mb.BaseDynamicConfig:
                return {
                    "call_params": json.loads(fn_params.call_params)
                    if fn_params.call_params
                    else {}
                }

            @wraps(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                if return_type is str:
                    traced_call = trace_decorator(
                        call_decorator()(prompt_template_async)
                    )
                    return (await traced_call(*args, **kwargs)).content
                elif get_origin(return_type) is AsyncIterable and get_args(
                    return_type
                ) == (str,):
                    traced_call = trace_decorator(
                        call_decorator(stream=True)(prompt_template)
                    )

                    async def iterable() -> AsyncIterable[str]:
                        async for chunk, _ in await traced_call(*args, **kwargs):
                            yield chunk.content

                    return cast(_R, iterable())
                elif get_origin(return_type) is Message:
                    traced_call = trace_decorator(
                        call_decorator(tools=list(get_args(return_type)))(
                            prompt_template
                        )
                    )
                    return cast(
                        _R, Message(response=await traced_call(*args, **kwargs))
                    )
                elif issubclass(return_type, Message):
                    traced_call = trace_decorator(call_decorator()(prompt_template))
                    return cast(
                        _R, Message(response=await traced_call(*args, **kwargs))
                    )
                elif (
                    get_origin(return_type) is Iterable
                    and len(iter_args := get_args(return_type)) == 1
                    and issubclass((response_model := iter_args[0]), BaseModel)
                ):
                    traced_call = trace_decorator(
                        call_decorator(response_model=response_model, stream=True)(
                            prompt_template
                        )
                    )
                    return cast(_R, await traced_call(*args, **kwargs))
                elif mb._utils.is_base_type(return_type) or issubclass(
                    return_type, BaseModel
                ):
                    traced_call = trace_decorator(
                        call_decorator(response_model=return_type)(prompt_template)
                    )
                    return cast(_R, await traced_call(*args, **kwargs))
                else:
                    raise ValueError(f"Unsupported return type `{return_type}`.")

            return inner_async
        else:

            @mb.prompt_template(fn_params.prompt_template)
            @wraps(fn)
            def prompt_template(
                *args: _P.args, **kwargs: _P.kwargs
            ) -> mb.BaseDynamicConfig:
                return {
                    "call_params": json.loads(fn_params.call_params)
                    if fn_params.call_params
                    else {}
                }

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                if return_type is str:
                    traced_call = trace_decorator(call_decorator()(prompt_template))
                    return traced_call(*args, **kwargs).content
                elif get_origin(return_type) is Iterable and get_args(return_type) == (
                    str,
                ):
                    traced_call = trace_decorator(
                        call_decorator(stream=True)(prompt_template)
                    )

                    def iterable() -> Iterable[str]:
                        for chunk, _ in traced_call(*args, **kwargs):
                            yield chunk.content

                    return cast(_R, iterable())
                elif get_origin(return_type) is Message:
                    traced_call = trace_decorator(
                        call_decorator(tools=list(get_args(return_type)))(
                            prompt_template
                        )
                    )
                    return cast(_R, Message(response=traced_call(*args, **kwargs)))
                elif issubclass(return_type, Message):
                    traced_call = trace_decorator(call_decorator()(prompt_template))
                    return cast(_R, Message(response=traced_call(*args, **kwargs)))
                elif (
                    get_origin(return_type) is Iterable
                    and len(iter_args := get_args(return_type)) == 1
                    and issubclass((response_model := iter_args[0]), BaseModel)
                ):
                    traced_call = trace_decorator(
                        call_decorator(response_model=response_model, stream=True)(
                            prompt_template
                        )
                    )
                    return cast(_R, traced_call(*args, **kwargs))
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

    return decorator
