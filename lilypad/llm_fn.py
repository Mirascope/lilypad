"""The lilypad `llm_fn` decorator."""

import inspect
import json
from collections.abc import Callable, Coroutine, Generator
from contextlib import contextmanager
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
from opentelemetry.trace import get_tracer
from opentelemetry.trace.span import Span
from opentelemetry.util.types import AttributeValue

from lilypad._trace import trace
from lilypad.server import client

from ._utils import (
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

                if not synced:
                    trace_decorator = trace(
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
                    return cast(_R, await trace_decorator(fn)(*args, **kwargs))

                if not version.fn_params:
                    raise ValueError(f"Synced function {fn.__name__} has no params.")

                fn_params = version.fn_params

                @contextmanager
                def custom_context_manager(
                    fn: Callable,
                ) -> Generator[Span, Any, None]:
                    tracer = get_tracer("lilypad")
                    with tracer.start_as_current_span(f"{fn.__name__}") as span:
                        attributes: dict[str, AttributeValue] = {
                            "lilypad.project_id": lilypad_client.project_id
                            if lilypad_client.project_id
                            else 0,
                            "lilypad.function_name": fn.__name__,
                            "lilypad.version": version.version
                            if version.version
                            else "",
                            "lilypad.version_id": version.id,
                            "lilypad.arg_types": json.dumps(arg_types),
                            "lilypad.arg_values": json.dumps(arg_values),
                            "lilypad.lexical_closure": version.llm_fn.code,
                            "lilypad.prompt_template": fn_params.prompt_template,
                            "lilypad.is_async": True,
                        }
                        span.set_attributes(attributes)
                        yield span

                synced_decorator_async = middleware_factory(
                    custom_context_manager=custom_context_manager,
                    handle_call_response=handle_call_response,
                    handle_call_response_async=handle_call_response_async,
                    handle_stream=handle_stream,
                    handle_stream_async=handle_stream_async,
                    handle_response_model=handle_response_model,
                    handle_response_model_async=handle_response_model_async,
                    handle_structured_stream=handle_structured_stream,
                    handle_structured_stream_async=handle_structured_stream_async,
                )
                if not version.fn_params:
                    raise ValueError(f"Synced function {fn.__name__} has no params.")
                return await traced_synced_llm_function_constructor(
                    version.fn_params, synced_decorator_async
                )(fn)(*args, **kwargs)

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
                version = get_llm_function_version(fn, arg_types, synced)

                @contextmanager
                def custom_context_manager(
                    fn: Callable,
                ) -> Generator[Span, Any, None]:
                    tracer = get_tracer("lilypad")
                    with tracer.start_as_current_span(f"{fn.__name__}") as span:
                        attributes: dict[str, AttributeValue] = {
                            "lilypad.project_id": lilypad_client.project_id
                            if lilypad_client.project_id
                            else 0,
                            "lilypad.function_name": fn.__name__,
                            "lilypad.version": version.version
                            if version.version
                            else "",
                            "lilypad.version_id": version.id,
                            "lilypad.arg_types": json.dumps(arg_types),
                            "lilypad.arg_values": json.dumps(arg_values),
                            "lilypad.lexical_closure": version.llm_fn.code,
                            "lilypad.prompt_template": version.fn_params.prompt_template
                            if version.fn_params
                            else "",
                            "lilypad.is_async": False,
                        }
                        span.set_attributes(attributes)
                        yield span

                if not synced:
                    if hasattr(fn, "__mirascope_call__"):
                        decorator = middleware_factory(
                            custom_context_manager=custom_context_manager,
                            handle_call_response=handle_call_response,
                            handle_call_response_async=handle_call_response_async,
                            handle_stream=handle_stream,
                            handle_stream_async=handle_stream_async,
                            handle_response_model=handle_response_model,
                            handle_response_model_async=handle_response_model_async,
                            handle_structured_stream=handle_structured_stream,
                            handle_structured_stream_async=handle_structured_stream_async,
                        )
                    else:
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

                if not version.fn_params:
                    raise ValueError(f"Synced function {fn.__name__} has no params.")

                synced_decorator = middleware_factory(
                    custom_context_manager=custom_context_manager,
                    handle_call_response=handle_call_response,
                    handle_call_response_async=handle_call_response_async,
                    handle_stream=handle_stream,
                    handle_stream_async=handle_stream_async,
                    handle_response_model=handle_response_model,
                    handle_response_model_async=handle_response_model_async,
                    handle_structured_stream=handle_structured_stream,
                    handle_structured_stream_async=handle_structured_stream_async,
                )
                return traced_synced_llm_function_constructor(
                    version.fn_params, synced_decorator
                )(fn)(*args, **kwargs)  # pyright: ignore [reportReturnType]

            return inner

    return decorator
