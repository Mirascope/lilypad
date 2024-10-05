"""The lilypad `prompt` decorator."""

import inspect
import json
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

import lilypad_sdk
import requests
from lilypad_sdk.types import LlmFunctionBasePublic
from lilypad_sdk.types.llm_functions import CallArgsPublic
from mirascope import core as mcore
from pydantic import BaseModel

from lilypad.trace import trace

from ..lexical_closure import compute_function_hash
from ..messages import Message
from ..utils import fn_is_async

_P = ParamSpec("_P")
_R = TypeVar("_R")

client = lilypad_sdk.LilypadSDK(base_url="http://localhost:8000/api", timeout=10)


def poll_call_args(hash: str) -> CallArgsPublic:
    """Polls the LLM API for the call args."""
    while True:
        try:
            provider_call_args = client.llm_functions.provider_call_params.retrieve(
                hash
            )
        except lilypad_sdk.NotFoundError:
            print("Waiting for provider call arguments...")
            time.sleep(1)
            continue
        except lilypad_sdk.APIConnectionError:
            print("Connection error, API may not be running...")
            time.sleep(1)
            continue
        else:
            return provider_call_args


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

        def get_call_params(
            *args: _P.args, **kwargs: _P.kwargs
        ) -> tuple[Callable, CallArgsPublic, LlmFunctionBasePublic, dict[str, Any]]:
            """Retrieve the call parameters for the function."""
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

            if not llm_version.provider_call_params:
                webbrowser.open(
                    f"http://localhost:8000/lilypad/llmFunctions/{llm_version.id}/providerCallParams"
                )

            call_args = poll_call_args(hash)
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
            return call, call_args, llm_version, input_values

        return_type = get_type_hints(fn).get("return", type(None))

        if fn_is_async(fn):

            @wraps(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                call, call_args, llm_function, input_values = get_call_params(
                    *args, **kwargs
                )
                traced_call = trace(
                    llm_function_id=llm_function.id,
                    version_hash=llm_function.version_hash
                    if llm_function.version_hash
                    else "",
                    input_values=input_values,
                    input_types=json.loads(llm_function.input_arguments)
                    if llm_function.input_arguments
                    else {},
                    lexical_closure=llm_function.code,
                    prompt_template=call_args.prompt_template,
                )(call)

                @mcore.base.prompt_template(call_args.prompt_template)
                @wraps(fn)
                async def prompt_template(
                    *args: _P.args, **kwargs: _P.kwargs
                ) -> mcore.base.BaseDynamicConfig:
                    return {"call_params": call_args.call_params}

                if return_type is str:
                    llm_fn = traced_call()(prompt_template)
                    return cast(_R, (await llm_fn(*args, **kwargs)).content)
                elif get_origin(return_type) is AsyncIterable and get_args(
                    return_type
                ) == (str,):
                    llm_fn = traced_call(stream=True)(prompt_template)

                    async def iterable() -> AsyncIterable[str]:
                        async for chunk, _ in await llm_fn(*args, **kwargs):
                            yield chunk.content

                    return cast(_R, iterable())
                elif get_origin(return_type) is Message:
                    llm_fn = traced_call(tools=list(get_args(return_type)))(
                        prompt_template
                    )
                    return cast(_R, Message(response=await llm_fn(*args, **kwargs)))
                elif issubclass(return_type, Message):
                    llm_fn = traced_call()(prompt_template)
                    return cast(_R, Message(response=await llm_fn(*args, **kwargs)))
                elif mcore.base._utils.is_base_type(return_type) or issubclass(
                    return_type, BaseModel
                ):
                    llm_fn = traced_call(response_model=return_type)(prompt_template)
                    return cast(_R, await llm_fn(*args, **kwargs))  # pyright: ignore [reportGeneralTypeIssues]
                else:
                    raise ValueError(f"Unsupported return type `{return_type}`.")

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                call, call_args, llm_function, input_values = get_call_params(
                    *args, **kwargs
                )
                traced_call = trace(
                    llm_function_id=llm_function.id,
                    version_hash=llm_function.version_hash
                    if llm_function.version_hash
                    else "",
                    input_values=input_values,
                    input_types=json.loads(llm_function.input_arguments)
                    if llm_function.input_arguments
                    else {},
                    lexical_closure=llm_function.code,
                    prompt_template=call_args.prompt_template,
                )

                @mcore.base.prompt_template(call_args.prompt_template)
                @wraps(fn)
                def prompt_template(
                    *args: _P.args, **kwargs: _P.kwargs
                ) -> mcore.base.BaseDynamicConfig:
                    return {"call_params": call_args.call_params}

                if return_type is str:
                    llm_fn = call()(prompt_template)
                    traced_llm_fn = traced_call(llm_fn)
                    return cast(_R, traced_llm_fn(*args, **kwargs).content)
                elif get_origin(return_type) is Iterable and get_args(return_type) == (
                    str,
                ):
                    llm_fn = call(stream=True)(prompt_template)
                    traced_llm_fn = traced_call(llm_fn)

                    def iterable() -> Iterable[str]:
                        for chunk, _ in traced_llm_fn(*args, **kwargs):
                            yield chunk.content

                    return cast(_R, iterable())
                elif get_origin(return_type) is Message:
                    llm_fn = call(tools=list(get_args(return_type)))(prompt_template)
                    traced_llm_fn = traced_call(llm_fn)
                    return cast(_R, Message(response=traced_llm_fn(*args, **kwargs)))
                elif issubclass(return_type, Message):
                    llm_fn = call()(prompt_template)
                    traced_llm_fn = traced_call(llm_fn)
                    return cast(_R, Message(response=traced_llm_fn(*args, **kwargs)))
                elif mcore.base._utils.is_base_type(return_type) or issubclass(
                    return_type, BaseModel
                ):
                    llm_fn = call(response_model=return_type)(prompt_template)
                    traced_llm_fn = traced_call(llm_fn)
                    return cast(_R, traced_llm_fn(*args, **kwargs))
                else:
                    raise ValueError(f"Unsupported return type `{return_type}`.")

            return inner

    return decorator
