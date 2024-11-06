"""Utilities for the `lilypad` library."""

import base64
import inspect
import json
import os
import time
import webbrowser
from collections.abc import (
    AsyncIterable,
    Callable,
    Coroutine,
    Generator,
    Iterable,
)
from contextlib import _GeneratorContextManager, contextmanager
from functools import partial, wraps
from importlib import import_module
from io import BytesIO
from pathlib import Path
from typing import (
    Any,
    ParamSpec,
    TypeVar,
    cast,
    get_args,
    get_origin,
    get_type_hints,
)

import PIL
import PIL.WebPImagePlugin
from mirascope.core import base as mb
from opentelemetry.trace import get_tracer
from opentelemetry.trace.span import Span
from opentelemetry.util.types import AttributeValue
from pydantic import BaseModel

from lilypad.models import FnParamsPublic, VersionPublic
from lilypad.server import client
from lilypad.server.models.fn_params import Provider

from ._lexical_closure import compute_function_hash
from .messages import Message

_P = ParamSpec("_P")
_R = TypeVar("_R")


def load_config() -> dict[str, Any]:
    try:
        project_dir = os.getenv("LILYPAD_PROJECT_DIR", Path.cwd())
        with open(f"{project_dir}/.lilypad/config.json") as f:
            config = json.loads(f.read())
        return config
    except FileNotFoundError:
        return {}


config = load_config()
port = config.get("port", 8000)

lilypad_client = client.LilypadClient(
    base_url=f"http://localhost:{port}/api", timeout=10
)


def stringify_type(t: Any) -> str:  # noqa: ANN401
    """Convert a type or annotation to a string."""
    if hasattr(t, "__name__"):
        return t.__name__
    else:
        return str(t)


def poll_active_version(hash: str, fn_params_hash: str | None = None) -> VersionPublic:
    """Polls the LLM API for the active version."""
    while True:
        try:
            active_version = lilypad_client.get_active_version_by_function_hash(hash)
            if (
                os.getenv("LILYPAD_EDITOR_OPEN") == "True"
                and fn_params_hash
                and active_version.fn_params
                and fn_params_hash == active_version.fn_params.hash
            ) or active_version.llm_function_hash != hash:
                time.sleep(1)
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

    if not synced:
        try:
            return lilypad_client.get_non_synced_version(hash)
        except client.NotFoundError:
            llm_fn_version = lilypad_client.post_llm_function(
                function_name=fn.__name__,
                code=code,
                version_hash=hash,
                arg_types=arg_types,
            )
            return lilypad_client.create_non_synced_version(llm_fn_version.id, hash)
    else:
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
            active_version = lilypad_client.get_active_version_by_function_hash(hash)
        except client.NotFoundError:
            active_version = None

        if synced and not active_version:
            webbrowser.open(lilypad_client.get_editor_url(llm_fn_version.id))

        return poll_active_version(
            hash,
            active_version.fn_params.hash
            if active_version and active_version.fn_params
            else None,
        )


def _construct_call_decorator(fn: Callable, fn_params: FnParamsPublic) -> partial[Any]:
    provider, client = fn_params.provider.value, None
    if fn_params.provider.value == "openrouter":
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
        model=fn_params.model,
        json_mode=False,
        client=client,
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

    def decorator(
        fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        call_decorator = _construct_call_decorator(fn, fn_params)
        return_type = get_type_hints(fn).get("return", type(None))
        if inspect.iscoroutinefunction(fn):

            @mb.prompt_template(fn_params.prompt_template)
            @wraps(fn)
            async def prompt_template_async(
                *args: _P.args, **kwargs: _P.kwargs
            ) -> mb.BaseDynamicConfig:
                if fn_params.provider == Provider.GEMINI:
                    return {
                        "call_params": {
                            "generation_config": fn_params.call_params.model_dump(
                                exclude_defaults=True
                            )
                        }
                        if fn_params.call_params
                        else {}
                    }
                return {
                    "call_params": fn_params.call_params.model_dump(
                        exclude_defaults=True
                    )
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
                if fn_params.provider == Provider.GEMINI:
                    return {
                        "call_params": {
                            "generation_config": fn_params.call_params.model_dump(
                                exclude_defaults=True
                            )
                        }
                        if fn_params.call_params
                        else {}
                    }
                return {
                    "call_params": fn_params.call_params.model_dump(
                        exclude_defaults=True
                    )
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


def get_custom_context_manager(
    version: VersionPublic,
    arg_types: dict[str, str],
    arg_values: dict[str, Any],
    is_async: bool,
    prompt_template: str | None = None,
) -> Callable[..., _GeneratorContextManager[Span]]:
    @contextmanager
    def custom_context_manager(
        fn: Callable,
    ) -> Generator[Span, Any, None]:
        tracer = get_tracer("lilypad")
        lilypad_prompt_template = (
            version.fn_params.prompt_template if version.fn_params else prompt_template
        )
        with tracer.start_as_current_span(f"{fn.__name__}") as span:
            attributes: dict[str, AttributeValue] = {
                "lilypad.project_id": lilypad_client.project_id
                if lilypad_client.project_id
                else 0,
                "lilypad.function_name": fn.__name__,
                "lilypad.version": version.version if version.version else "",
                "lilypad.version_id": version.id,
                "lilypad.arg_types": json.dumps(arg_types),
                "lilypad.arg_values": json.dumps(arg_values),
                "lilypad.lexical_closure": version.llm_fn.code,
                "lilypad.prompt_template": lilypad_prompt_template,
                "lilypad.is_async": is_async,
            }
            span.set_attributes(attributes)
            yield span

    return custom_context_manager


def encode_gemini_part(
    part: str | dict | PIL.WebPImagePlugin.WebPImageFile,
) -> str | dict:
    if isinstance(part, dict):
        if "mime_type" in part and "data" in part:
            # Handle binary data by base64 encoding it
            return {
                "mime_type": part["mime_type"],
                "data": base64.b64encode(part["data"]).decode("utf-8"),
            }
        return part
    elif isinstance(part, PIL.WebPImagePlugin.WebPImageFile):
        buffered = BytesIO()
        part.save(buffered, format="WEBP")  # Use "WEBP" to maintain the original format
        img_bytes = buffered.getvalue()
        return {
            "mime_type": "image/webp",
            "data": base64.b64encode(img_bytes).decode("utf-8"),
        }
    return part


def serialize_proto_data(data: list[dict]) -> str:
    """Serializes a list of dictionaries containing protocol buffer-like data.
    Handles binary data by base64 encoding it.

    Args:
        data: List of dictionaries containing mixed data types

    Returns:
        str: JSON-serialized string of the data
    """
    serializable_data = []
    for item in data:
        serialized_item = item.copy()
        if "parts" in item:
            serialized_item["parts"] = [
                encode_gemini_part(part) for part in item["parts"]
            ]
        serializable_data.append(serialized_item)

    return json.dumps(serializable_data)


def _set_call_response_attributes(response: mb.BaseCallResponse, span: Span) -> None:
    try:
        output = json.dumps(response.message_param)
    except TypeError:
        output = str(response.message_param)
    try:
        messages = json.dumps(response.messages)
    except TypeError:
        messages = serialize_proto_data(response.messages)  # Gemini
    attributes: dict[str, AttributeValue] = {
        "lilypad.output": output,
        "lilypad.messages": messages,
    }
    span.set_attributes(attributes)


def _set_response_model_attributes(result: BaseModel | mb.BaseType, span: Span) -> None:
    if isinstance(result, BaseModel):
        completion = result.model_dump_json()
        messages = json.dumps(result._response.messages)  # pyright: ignore [reportAttributeAccessIssue]
    else:
        if not isinstance(result, str | int | float | bool):
            result = str(result)
        completion = result
        messages = None

    attributes: dict[str, AttributeValue] = {
        "lilypad.output": completion,
    }
    if messages:
        attributes["lilypad.messages"] = messages
    span.set_attributes(attributes)


def handle_call_response(
    result: mb.BaseCallResponse, fn: Callable, span: Span | None
) -> None:
    if span is None:
        return
    _set_call_response_attributes(result, span)


def handle_stream(stream: mb.BaseStream, fn: Callable, span: Span | None) -> None:
    if span is None:
        return
    call_response = cast(mb.BaseCallResponse, stream.construct_call_response())
    _set_call_response_attributes(call_response, span)


def handle_response_model(
    result: BaseModel | mb.BaseType, fn: Callable, span: Span | None
) -> None:
    if span is None:
        return

    _set_response_model_attributes(result, span)


def handle_structured_stream(
    result: mb.BaseStructuredStream, fn: Callable, span: Span | None
) -> None:
    if span is None:
        return

    _set_response_model_attributes(result.constructed_response_model, span)


async def handle_call_response_async(
    result: mb.BaseCallResponse, fn: Callable, span: Span | None
) -> None:
    if span is None:
        return

    _set_call_response_attributes(result, span)


async def handle_stream_async(
    stream: mb.BaseStream, fn: Callable, span: Span | None
) -> None:
    if span is None:
        return
    call_response = cast(mb.BaseCallResponse, stream.construct_call_response())
    _set_call_response_attributes(call_response, span)


async def handle_response_model_async(
    result: BaseModel | mb.BaseType, fn: Callable, span: Span | None
) -> None:
    if span is None:
        return
    _set_response_model_attributes(result, span)


async def handle_structured_stream_async(
    result: mb.BaseStructuredStream, fn: Callable, span: Span | None
) -> None:
    if span is None:
        return
    _set_response_model_attributes(result.constructed_response_model, span)
