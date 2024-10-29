"""The lilypad `llm_fn` decorator."""

import inspect
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import (
    Any,
    ParamSpec,
    Protocol,
    TypeVar,
    cast,
    overload,
)

from mirascope.integrations import middleware_factory

from lilypad._trace import trace
from lilypad.server import client

from ._utils import (
    get_custom_context_manager,
    get_llm_function_version,
    handle_call_response,
    handle_call_response_async,
    handle_response_model,
    handle_response_model_async,
    handle_stream,
    handle_stream_async,
    handle_structured_stream,
    handle_structured_stream_async,
    inspect_arguments,
    load_config,
    traced_synced_llm_function_constructor,
)

_P = ParamSpec("_P")
_R = TypeVar("_R")

config = load_config()
port = config.get("port", 8000)
lilypad_client = client.LilypadClient(
    base_url=f"http://localhost:{port}/api", timeout=10
)


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


def llm_fn(synced: bool = False) -> LLMFn:
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
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
                version = get_llm_function_version(fn, arg_types, synced)
                is_mirascope_call = hasattr(fn, "__mirascope_call__")

                if not synced and not is_mirascope_call:
                    decorator = trace(
                        project_id=lilypad_client.project_id,
                        version_id=version.id,
                        arg_types=arg_types,
                        arg_values=arg_values,
                        lexical_closure=version.llm_fn.code,
                        prompt_template=version.fn_params.prompt_template
                        if version.fn_params
                        else "",
                        version=version.version,
                    )
                    return cast(_R, await decorator(fn)(*args, **kwargs))

                decorator = middleware_factory(
                    custom_context_manager=get_custom_context_manager(
                        version,
                        arg_types,
                        arg_values,
                        True,
                        fn._prompt_template,  # pyright: ignore [reportFunctionMemberAccess]
                    ),
                    handle_call_response=handle_call_response,
                    handle_call_response_async=handle_call_response_async,
                    handle_stream=handle_stream,
                    handle_stream_async=handle_stream_async,
                    handle_response_model=handle_response_model,
                    handle_response_model_async=handle_response_model_async,
                    handle_structured_stream=handle_structured_stream,
                    handle_structured_stream_async=handle_structured_stream_async,
                )
                if not synced and is_mirascope_call:
                    return cast(_R, await decorator(fn)(*args, **kwargs))

                if not version.fn_params:
                    raise ValueError(f"Synced function {fn.__name__} has no params.")

                return await traced_synced_llm_function_constructor(
                    version.fn_params, decorator
                )(fn)(*args, **kwargs)  # pyright: ignore [reportReturnType]

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
                version = get_llm_function_version(fn, arg_types, synced)
                is_mirascope_call = hasattr(fn, "__mirascope_call__")
                if not synced and not is_mirascope_call:
                    decorator = trace(
                        project_id=lilypad_client.project_id,
                        version_id=version.id,
                        arg_types=arg_types,
                        arg_values=arg_values,
                        lexical_closure=version.llm_fn.code,
                        prompt_template=version.fn_params.prompt_template
                        if version.fn_params
                        else "",
                        version=version.version,
                    )
                    return cast(_R, decorator(fn)(*args, **kwargs))
                decorator = middleware_factory(
                    custom_context_manager=get_custom_context_manager(
                        version,
                        arg_types,
                        arg_values,
                        False,
                        fn._prompt_template,  # pyright: ignore [reportFunctionMemberAccess]
                    ),
                    handle_call_response=handle_call_response,
                    handle_call_response_async=handle_call_response_async,
                    handle_stream=handle_stream,
                    handle_stream_async=handle_stream_async,
                    handle_response_model=handle_response_model,
                    handle_response_model_async=handle_response_model_async,
                    handle_structured_stream=handle_structured_stream,
                    handle_structured_stream_async=handle_structured_stream_async,
                )
                if not synced and is_mirascope_call:
                    return cast(_R, decorator(fn)(*args, **kwargs))

                if not version.fn_params:
                    raise ValueError(f"Synced function {fn.__name__} has no params.")

                return traced_synced_llm_function_constructor(
                    version.fn_params, decorator
                )(fn)(*args, **kwargs)  # pyright: ignore [reportReturnType]

            return inner

    return decorator
