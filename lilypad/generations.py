"""The `generations` module for automatically versioning and tracing LLM generations."""

import inspect
import json
from collections.abc import Callable, Coroutine, Generator
from contextlib import contextmanager
from contextvars import ContextVar, Token
from functools import wraps
from typing import Any, ParamSpec, Protocol, TypeVar, overload

from fastapi.encoders import jsonable_encoder
from mirascope import llm
from mirascope.core import prompt_template
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.trace import get_tracer, get_tracer_provider
from opentelemetry.util.types import AttributeValue
from pydantic import BaseModel

from ._utils import (
    Closure,
    call_safely,
    create_mirascope_middleware,
    get_qualified_name,
    inspect_arguments,
    load_config,
)
from .server.client import LilypadClient, NotFoundError
from .server.schemas import GenerationPublic
from .server.settings import get_settings

_P = ParamSpec("_P")
_R = TypeVar("_R")


current_generation: ContextVar[GenerationPublic | None] = ContextVar(
    "current_generation", default=None
)


class GenerationDecorator(Protocol):
    """Protocol for the `generation` decorator return type."""

    @overload
    def __call__(
        self, fn: Callable[_P, Coroutine[Any, Any, _R]]
    ) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def __call__(self, fn: Callable[_P, _R]) -> Callable[_P, _R]: ...

    def __call__(
        self, fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        """Protocol `call` definition for `generation` decorator return type."""
        ...


def _get_batch_span_processor() -> BatchSpanProcessor | None:
    """Get the BatchSpanProcessor from the current TracerProvider.

    Retrieve the BatchSpanProcessor from the current TracerProvider dynamically.
    This avoids using a global variable by inspecting the provider's _active_span_processors.
    """
    tracer_provider = get_tracer_provider()
    processor = getattr(tracer_provider, "_active_span_processor", None)
    if not processor:
        return None
    _span_processors = getattr(processor, "_span_processors", None)
    if _span_processors:
        for processor in _span_processors:
            if isinstance(processor, BatchSpanProcessor):
                return processor
    return None


@contextmanager
def outermost_lock_context(enable_lock: bool) -> Generator[None, None, None]:
    """Acquire the BatchSpanProcessor's condition lock if enable_lock is True.

    This context manager is intended for use in the outermost generation.
    When enable_lock is True, it retrieves the current BatchSpanProcessor and acquires its
    condition lock. This ensures that flush operations are synchronized and only executed
    at the outermost generation level.
    For inner generations (enable_lock is False), no lock is acquired.
    """
    if not enable_lock:
        yield
        return
    processor = _get_batch_span_processor()
    if not processor:
        yield
        return
    with processor.condition:
        yield


def _construct_trace_attributes(
    generation: GenerationPublic,
    arg_types: dict[str, str],
    arg_values: dict[str, Any],
    prompt_template: str,
    output: Any,
    is_async: bool,
) -> dict[str, AttributeValue]:
    if isinstance(output, BaseModel):
        output = str(output.model_dump())
    jsonable_arg_values = {}
    settings = get_settings()
    for arg_name, arg_value in arg_values.items():
        try:
            serialized_arg_value = jsonable_encoder(arg_value)
        except ValueError:
            serialized_arg_value = "could not serialize"
        jsonable_arg_values[arg_name] = serialized_arg_value
    return {
        "lilypad.project_uuid": settings.project_id if settings.project_id else "",
        "lilypad.type": "generation",
        "lilypad.generation.uuid": str(generation.uuid),
        "lilypad.generation.name": generation.name,
        "lilypad.generation.signature": generation.signature,
        "lilypad.generation.code": generation.code,
        "lilypad.generation.arg_types": json.dumps(arg_types),
        "lilypad.generation.arg_values": json.dumps(jsonable_arg_values),
        "lilypad.generation.prompt_template": prompt_template,
        "lilypad.generation.output": str(output),
        "lilypad.generation.version": generation.version_num
        if generation.version_num
        else -1,
        "lilypad.is_async": is_async,
    }


def _trace(
    generation: GenerationPublic,
    arg_types: dict[str, str],
    arg_values: dict[str, Any],
    prompt_template: str = "",
) -> GenerationDecorator:
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
                with get_tracer("lilypad").start_as_current_span(
                    get_qualified_name(fn)
                ) as span:
                    output = await fn(*args, **kwargs)
                    attributes: dict[str, AttributeValue] = _construct_trace_attributes(
                        generation, arg_types, arg_values, prompt_template, output, True
                    )
                    span.set_attributes(attributes)
                return output  # pyright: ignore [reportReturnType]

            return inner_async

        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                with get_tracer("lilypad").start_as_current_span(
                    get_qualified_name(fn)
                ) as span:
                    output = fn(*args, **kwargs)
                    attributes: dict[str, AttributeValue] = _construct_trace_attributes(
                        generation,
                        arg_types,
                        arg_values,
                        prompt_template,
                        output,
                        False,
                    )
                    span.set_attributes(attributes)
                return output  # pyright: ignore [reportReturnType]

            return inner

    return decorator


def _build_mirascope_call(
    generation_public: GenerationPublic, fn: Callable
) -> Callable:
    """Build a Mirascope call object."""
    mirascope_prompt = prompt_template(generation_public.prompt_template)(fn)

    call_params = generation_public.call_params

    if generation_public.tools:
        call_params["tools"] = [
            Closure.from_code(tool.code, tool.name).build_object()
            for tool in generation_public.tools
        ]
    elif response_model := generation_public.response_model:
        call_params["response_model"] = Closure.from_code(
            response_model.code, response_model.name
        ).build_object()
    mirascope_call = llm.call(**call_params)(mirascope_prompt)
    return mirascope_call


def generation(
    custom_id: str | None = None, managed: bool = False
) -> GenerationDecorator:
    """The `generation` decorator for versioning and tracing LLM generations.\

    The decorated function will be versioned according to it's runnable lexical closure,
    and any call to the function will be traced and logged automatically.

    Returns:
        GenerationDecorator: The `generation` decorator return protocol.
    """

    @overload
    def decorator(
        fn: Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def decorator(fn: Callable[_P, _R]) -> Callable[_P, _R]: ...

    def decorator(
        fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        is_mirascope_call = hasattr(fn, "__mirascope_call__") or managed
        prompt_template = (
            fn._prompt_template if hasattr(fn, "_prompt_template") else ""  # pyright: ignore[reportFunctionMemberAccess]
        )
        config = load_config()
        lilypad_client = LilypadClient(
            token=config.get("token", None),
        )
        if inspect.iscoroutinefunction(fn):

            @call_safely(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
                try:
                    generation = lilypad_client.get_generation_version(
                        fn,
                        arg_types,
                        custom_id=custom_id,
                        create_new_generation=not managed,
                    )
                except NotFoundError:
                    ui_link = f"{get_settings().remote_client_url}/projects/{lilypad_client.project_uuid}"
                    raise ValueError(
                        f"No generation found for function '{Closure.from_fn(fn).name}'. "
                        f"Please create a new generation at: {ui_link}"
                    )
                token = current_generation.set(generation)
                try:
                    # Check if this is the outermost generation (no previous generation)
                    is_outermost = token.old_value is None
                    with outermost_lock_context(is_outermost):
                        if not is_mirascope_call:
                            decorator_inner = _trace(
                                generation=generation,
                                arg_types=arg_types,
                                arg_values=arg_values,
                                prompt_template="",
                            )
                            return await decorator_inner(fn)(*args, **kwargs)
                        # managed_prompt_template = generation.prompt_template
                        managed_prompt_template = (
                            "Answer this question: {question}"  # fake prompt template
                        )
                        decorator_inner = create_mirascope_middleware(
                            generation,
                            arg_types,
                            arg_values,
                            True,
                            managed_prompt_template if managed else prompt_template,
                        )
                        return await decorator_inner(
                            _build_mirascope_call(generation, fn) if managed else fn
                        )(*args, **kwargs)
                finally:
                    current_generation.reset(token)

            return inner_async

        else:

            @call_safely(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
                try:
                    generation = lilypad_client.get_generation_version(
                        fn, arg_types, custom_id=custom_id, create_new_generation=True
                    )
                except NotFoundError:
                    ui_link = f"{get_settings().remote_client_url}/projects/{lilypad_client.project_uuid}"
                    raise ValueError(
                        f"No generation found for function '{Closure.from_fn(fn).name}'. "
                        f"Please create a new generation at: {ui_link}"
                    )
                token = current_generation.set(generation)
                try:
                    is_outermost = token.old_value == Token.MISSING
                    with outermost_lock_context(is_outermost):
                        if not is_mirascope_call:
                            decorator_inner = _trace(
                                generation=generation,
                                arg_types=arg_types,
                                arg_values=arg_values,
                                prompt_template="",
                            )
                            return decorator_inner(fn)(*args, **kwargs)  # pyright: ignore [reportReturnType]
                        # managed_prompt_template = generation.prompt_template
                        managed_prompt_template = (
                            "Answer this question: {question}"  # fake prompt template
                        )
                        decorator_inner = create_mirascope_middleware(
                            generation,
                            arg_types,
                            arg_values,
                            False,
                            managed_prompt_template if managed else prompt_template,
                        )
                        return decorator_inner(
                            _build_mirascope_call(generation, fn) if managed else fn
                        )(*args, **kwargs)  # pyright: ignore [reportReturnType]
                finally:
                    current_generation.reset(token)

            return inner  # pyright: ignore [reportReturnType]

    return decorator
