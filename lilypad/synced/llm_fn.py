"""The lilypad `llm_fn` decorator."""

import inspect
import json
import os
import time
import webbrowser
from collections.abc import AsyncIterable, Callable, Coroutine, Iterable
from functools import partial, wraps
from typing import (
    Any,
    ParamSpec,
    Protocol,
    TypeVar,
    cast,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from mirascope import core as mcore
from pydantic import BaseModel

from lilypad.models import VersionPublic
from lilypad.server import client
from lilypad.trace import trace

from ..lexical_closure import compute_function_hash
from ..messages import Message
from ..utils import fn_is_async

_P = ParamSpec("_P")
_R = TypeVar("_R")

lilypad_client = client.LilypadClient(base_url="http://localhost:8000/api", timeout=10)


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
                and (fn_params_hash and fn_params_hash == active_version.fn_params.hash)
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


class LLMFn(Protocol):
    """Protocol for the `llm_fn` decorator return type."""

    @overload
    def __call__(
        self, fn: Callable[_P, Coroutine[Any, Any, _R]]
    ) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def __call__(self, fn: Callable[_P, _R]) -> Callable[_P, _R]: ...

    def __call__(
        self, fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        """Protocol `call` definition for `llm_fn` decorator return type."""
        ...


def llm_fn() -> LLMFn:
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

        def get_call_params(
            *args: _P.args, **kwargs: _P.kwargs
        ) -> tuple[Callable, VersionPublic, dict[str, Any]]:
            """Retrieve the call parameters for the function."""
            input = inspect_arguments(*args, **kwargs)
            hash, code = compute_function_hash(fn)
            input_types: dict[str, type[Any]] = {}
            input_values: dict[str, Any] = {}
            for arg_name, arg_info in input.items():
                input_types[arg_name] = arg_info["type"]
                input_values[arg_name] = arg_info["value"]
            try:
                llm_version = lilypad_client.get_llm_function_by_hash(hash)
            except client.NotFoundError:
                print("New version detected")
                llm_version = lilypad_client.post_llm_function(
                    function_name=fn.__name__,
                    code=code,
                    version_hash=hash,
                    input_arguments=json.dumps(input_types),
                )
            try:
                active_version = lilypad_client.get_active_version_by_function_name(
                    fn.__name__
                )
            except client.NotFoundError:
                active_version = None
            if (
                os.getenv("LILYPAD_EDITOR_OPEN") == "True"
                or not llm_version.fn_params
                or (active_version and active_version.llm_function_hash != hash)
            ):
                webbrowser.open(lilypad_client.get_editor_url(llm_version.id))

            version = poll_active_version(
                hash,
                fn.__name__,
                active_version.fn_params.hash if active_version else None,
            )
            call_args = version.fn_params
            # running into weird type errors, so forcing openai right now
            if (provider := call_args.provider) == "openai":
                call_decorator = mcore.openai.call

            # if (provider := data["provider"]) == "anthropic":
            #     call_decorator = mcore.anthropic.call
            # elif provider == "azure":
            #     call_decorator = mcore.azure.call
            # elif provider == "cohere":
            #     call_decorator = mcore.cohere.call
            # elif provider == "gemini":
            #     call_decorator = mcore.gemini.call
            # elif provider == "groq":
            #     call_decorator = mcore.groq.call
            # elif provider == "litellm":
            #     call_decorator = mcore.litellm.call
            # elif provider == "mistral":
            #     call_decorator = mcore.mistral.call
            # elif provider == "openai":
            #     call_decorator = mcore.openai.call
            # elif provider == "vertex":
            #     call_decorator = mcore.vertex.call
            else:
                # realistically we should never reach this point since we're in control
                # of what providers we allow the user to set in the editor.
                raise ValueError(f"Unknown provider: {provider}")
            call = partial(call_decorator, model=call_args.model, json_mode=False)
            return call, version, input_values

        return_type = get_type_hints(fn).get("return", type(None))

        if fn_is_async(fn):

            @wraps(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                call, version, input_values = get_call_params(*args, **kwargs)
                llm_function = version.llm_fn
                call_args = version.fn_params
                traced_call = trace(
                    llm_function_id=llm_function.id,
                    input_values=input_values,
                    input_types=json.loads(llm_function.input_arguments)
                    if llm_function.input_arguments
                    else {},
                    lexical_closure=llm_function.code,
                    prompt_template=call_args.prompt_template,
                    version=version.version,
                )(call)

                @mcore.base.prompt_template(call_args.prompt_template)
                @wraps(fn)
                async def prompt_template(
                    *args: _P.args, **kwargs: _P.kwargs
                ) -> mcore.base.BaseDynamicConfig:
                    return {
                        "call_params": json.loads(call_args.call_params)
                        if call_args.call_params
                        else {}
                    }

                if return_type is str:
                    mirascope_fn = traced_call()(prompt_template)
                    return cast(_R, (await mirascope_fn(*args, **kwargs)).content)
                elif get_origin(return_type) is AsyncIterable and get_args(
                    return_type
                ) == (str,):
                    mirascope_fn = traced_call(stream=True)(prompt_template)

                    async def iterable() -> AsyncIterable[str]:
                        async for chunk, _ in await mirascope_fn(*args, **kwargs):
                            yield chunk.content

                    return cast(_R, iterable())
                elif get_origin(return_type) is Message:
                    mirascope_fn = traced_call(tools=list(get_args(return_type)))(
                        prompt_template
                    )
                    return cast(
                        _R, Message(response=await mirascope_fn(*args, **kwargs))
                    )
                elif issubclass(return_type, Message):
                    mirascope_fn = traced_call()(prompt_template)
                    return cast(
                        _R, Message(response=await mirascope_fn(*args, **kwargs))
                    )
                elif mcore.base._utils.is_base_type(return_type) or issubclass(
                    return_type, BaseModel
                ):
                    mirascope_fn = traced_call(response_model=return_type)(
                        prompt_template
                    )
                    return cast(_R, await mirascope_fn(*args, **kwargs))  # pyright: ignore [reportGeneralTypeIssues]
                else:
                    raise ValueError(f"Unsupported return type `{return_type}`.")

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                call, version, input_values = get_call_params(*args, **kwargs)
                llm_function = version.llm_fn
                call_args = version.fn_params
                traced_call = trace(
                    llm_function_id=llm_function.id,
                    input_values=input_values,
                    input_types=json.loads(llm_function.input_arguments)
                    if llm_function.input_arguments
                    else {},
                    lexical_closure=llm_function.code,
                    prompt_template=call_args.prompt_template,
                    version=version.version,
                )

                @mcore.base.prompt_template(call_args.prompt_template)
                @wraps(fn)
                def prompt_template(
                    *args: _P.args, **kwargs: _P.kwargs
                ) -> mcore.base.BaseDynamicConfig:
                    return {
                        "call_params": json.loads(call_args.call_params)
                        if call_args.call_params
                        else {}
                    }

                if return_type is str:
                    mirascope_fn = call()(prompt_template)
                    traced_llm_fn = traced_call(mirascope_fn)
                    return cast(_R, traced_llm_fn(*args, **kwargs).content)
                elif get_origin(return_type) is Iterable and get_args(return_type) == (
                    str,
                ):
                    mirascope_fn = call(stream=True)(prompt_template)
                    traced_llm_fn = traced_call(mirascope_fn)

                    def iterable() -> Iterable[str]:
                        for chunk, _ in traced_llm_fn(*args, **kwargs):
                            yield chunk.content

                    return cast(_R, iterable())
                elif get_origin(return_type) is Message:
                    mirascope_fn = call(tools=list(get_args(return_type)))(
                        prompt_template
                    )
                    traced_llm_fn = traced_call(mirascope_fn)
                    return cast(_R, Message(response=traced_llm_fn(*args, **kwargs)))
                elif issubclass(return_type, Message):
                    mirascope_fn = call()(prompt_template)
                    traced_llm_fn = traced_call(mirascope_fn)
                    return cast(_R, Message(response=traced_llm_fn(*args, **kwargs)))
                elif mcore.base._utils.is_base_type(return_type) or issubclass(
                    return_type, BaseModel
                ):
                    mirascope_fn = call(response_model=return_type)(prompt_template)
                    traced_llm_fn = traced_call(mirascope_fn)
                    return cast(_R, traced_llm_fn(*args, **kwargs))
                else:
                    raise ValueError(f"Unsupported return type `{return_type}`.")

            return inner

    return decorator
