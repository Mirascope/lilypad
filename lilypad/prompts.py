"""The lilypad `prompt` decorator."""

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

from .dummy_database import get_dummy_database
from .messages import Message
from .utils import fn_is_async

_P = ParamSpec("_P")
_R = TypeVar("_R")


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


def prompt(json_mode: bool = False) -> Prompt:
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
        # this should be pulled from the editor
        data = get_dummy_database()[fn.__name__]

        # running into weird type errors, so forcing openai right now
        if (provider := data["provider"]) == "openai":
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
        call = partial(call_decorator, model=data["model"], json_mode=json_mode)
        return_type = get_type_hints(fn).get("return", type(None))

        if fn_is_async(fn):

            @wraps(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                @mcore.base.prompt_template(data["prompt_template"])
                @wraps(fn)
                async def prompt_template(
                    *args: _P.args, **kwargs: _P.kwargs
                ) -> mcore.base.BaseDynamicConfig:
                    return {"call_params": data["call_params"]}

                if return_type is str:
                    llm_fn = call()(prompt_template)
                    return cast(_R, (await llm_fn(*args, **kwargs)).content)
                elif get_origin(return_type) is AsyncIterable and get_args(
                    return_type
                ) == (str,):
                    llm_fn = call(stream=True)(prompt_template)

                    async def iterable() -> AsyncIterable[str]:
                        async for chunk, _ in await llm_fn(*args, **kwargs):
                            yield chunk.content

                    return cast(_R, iterable())
                elif get_origin(return_type) is Message:
                    llm_fn = call(tools=list(get_args(return_type)))(prompt_template)
                    return cast(_R, Message(response=await llm_fn(*args, **kwargs)))
                elif issubclass(return_type, Message):
                    llm_fn = call()(prompt_template)
                    return cast(_R, Message(response=await llm_fn(*args, **kwargs)))
                elif mcore.base._utils.is_base_type(return_type) or issubclass(
                    return_type, BaseModel
                ):
                    llm_fn = call(response_model=return_type)(prompt_template)
                    return cast(_R, await llm_fn(*args, **kwargs))
                else:
                    raise ValueError(f"Unsupported return type `{return_type}`.")

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                @mcore.base.prompt_template(data["prompt_template"])
                @wraps(fn)
                def prompt_template(
                    *args: _P.args, **kwargs: _P.kwargs
                ) -> mcore.base.BaseDynamicConfig:
                    return {"call_params": data["call_params"]}

                if return_type is str:
                    llm_fn = call()(prompt_template)
                    return cast(_R, llm_fn(*args, **kwargs).content)
                elif get_origin(return_type) is Iterable and get_args(return_type) == (
                    str,
                ):
                    llm_fn = call(stream=True)(prompt_template)

                    def iterable() -> Iterable[str]:
                        for chunk, _ in llm_fn(*args, **kwargs):
                            yield chunk.content

                    return cast(_R, iterable())
                elif get_origin(return_type) is Message:
                    llm_fn = call(tools=list(get_args(return_type)))(prompt_template)
                    return cast(_R, Message(response=llm_fn(*args, **kwargs)))
                elif issubclass(return_type, Message):
                    llm_fn = call()(prompt_template)
                    return cast(_R, Message(response=llm_fn(*args, **kwargs)))
                elif mcore.base._utils.is_base_type(return_type) or issubclass(
                    return_type, BaseModel
                ):
                    llm_fn = call(response_model=return_type)(prompt_template)
                    return cast(_R, llm_fn(*args, **kwargs))
                else:
                    raise ValueError(f"Unsupported return type `{return_type}`.")

            return inner

    return decorator
