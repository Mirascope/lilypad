"""The `prompts` module for prompting LLMs with data pulled from the database."""

import inspect
import json
from collections.abc import Callable, Coroutine, Sequence
from functools import wraps
from typing import TYPE_CHECKING, Any, Literal, ParamSpec, Protocol, overload

from mirascope.core import BaseMessageParam, prompt_template
from mirascope.core.base import CommonCallParams
from opentelemetry.trace import get_tracer
from opentelemetry.util.types import AttributeValue
from pydantic import BaseModel

from ._utils import Closure, inspect_arguments, load_config
from .generations import current_generation
from .server.client import LilypadClient
from .server.models import PromptPublic
from .server.settings import get_settings

_P = ParamSpec("_P")

config = load_config()
settings = get_settings()

lilypad_client = LilypadClient(
    timeout=10,
    token=config.get("token", None),
)

if TYPE_CHECKING:
    try:
        from mirascope.core.openai import OpenAICallParams
        from openai.types.chat import (
            ChatCompletionMessageParam,  # pyright: ignore [reportAssignmentType]
        )
    except ImportError:
        ChatCompletionMessageParam = Any
        OpenAICallParams = Any
    try:
        from anthropic.types import MessageParam
        from mirascope.core.anthropic import AnthropicCallParams
    except ImportError:
        MessageParam = Any
        AnthropicCallParams = Any
    try:
        from google.generativeai.types import ContentDict
        from mirascope.core.gemini import GeminiCallParams
    except ImportError:
        ContentDict = Any
        GeminiCallParams = Any


def _base_message_params(
    template: str, arg_values: dict[str, Any]
) -> list[BaseMessageParam]:
    @prompt_template(template)
    def fn(*args: Any, **kwargs: Any) -> None: ...

    return fn(**arg_values)


class Prompt(BaseModel):
    """The `Prompt` class for prompting LLMs with data pulled from the database."""

    template: str
    common_call_params: CommonCallParams
    arg_values: dict[str, Any]
    _base_message_params: list[BaseMessageParam]

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._base_message_params = _base_message_params(self.template, self.arg_values)

    @overload
    def messages(
        self, provider: Literal["openai"]
    ) -> Sequence["ChatCompletionMessageParam"]: ...

    @overload
    def messages(self, provider: Literal["anthropic"]) -> Sequence["MessageParam"]: ...  # pyright: ignore [reportInvalidTypeForm]

    @overload
    def messages(self, provider: Literal["gemini"]) -> Sequence["ContentDict"]: ...  # pyright: ignore [reportInvalidTypeForm]

    def messages(
        self, provider: Literal["openai", "anthropic", "gemini"]
    ) -> (
        Sequence["ChatCompletionMessageParam"]
        | Sequence["MessageParam"]  # pyright: ignore [reportInvalidTypeForm]
        | Sequence["ContentDict"]  # pyright: ignore [reportInvalidTypeForm]
    ):
        """Return the messages array for the given provider converted from base."""
        if provider == "openai":
            from mirascope.core.openai._utils import convert_message_params

            # type error needs resolution on mirascope side
            return convert_message_params(self._base_message_params)  # pyright: ignore [reportArgumentType]
        elif provider == "anthropic":
            from mirascope.core.anthropic._utils import convert_message_params

            # type error needs resolution on mirascope side
            return convert_message_params(self._base_message_params)  # pyright: ignore [reportArgumentType]
        elif provider == "gemini":
            from mirascope.core.gemini._utils import convert_message_params

            # type error needs resolution on mirascope side
            return convert_message_params(self._base_message_params)  # pyright: ignore [reportArgumentType]
        else:
            raise NotImplementedError(f"Unknown provider: {provider}")

    @overload
    def call_params(self, provider: Literal["openai"]) -> "OpenAICallParams": ...  # pyright: ignore [reportInvalidTypeForm]

    @overload
    def call_params(self, provider: Literal["anthropic"]) -> "AnthropicCallParams": ...  # pyright: ignore [reportInvalidTypeForm]

    @overload
    def call_params(self, provider: Literal["gemini"]) -> "GeminiCallParams": ...  # pyright: ignore [reportInvalidTypeForm]

    def call_params(
        self, provider: Literal["openai", "anthropic", "gemini"]
    ) -> "OpenAICallParams | AnthropicCallParams | GeminiCallParams":  # pyright: ignore [reportInvalidTypeForm]
        """Return the call parameters for the given provider converted from common."""
        if provider == "openai":
            from mirascope.core.openai._utils._convert_common_call_params import (
                convert_common_call_params,
            )

            return convert_common_call_params(self.common_call_params)
        elif provider == "anthropic":
            from mirascope.core.anthropic._utils._convert_common_call_params import (
                convert_common_call_params,
            )

            return convert_common_call_params(self.common_call_params)
        elif provider == "gemini":
            from mirascope.core.gemini._utils._convert_common_call_params import (
                convert_common_call_params,
            )

            return convert_common_call_params(self.common_call_params)
        else:
            raise NotImplementedError(f"Unknown provider: {provider}")


def _construct_trace_attributes(
    prompt: PromptPublic,
    arg_types: dict[str, str],
    arg_values: dict[str, Any],
    results: str,
    is_async: bool,
) -> dict[str, AttributeValue]:
    return {
        "lilypad.project_uuid": str(lilypad_client.project_uuid)
        if lilypad_client.project_uuid
        else 0,
        "lilypad.type": "prompt",
        "lilypad.prompt.uuid": str(prompt.uuid),
        "lilypad.prompt.name": prompt.name,
        "lilypad.prompt.signature": prompt.signature,
        "lilypad.prompt.code": prompt.code,
        "lilypad.prompt.template": prompt.template,
        "lilypad.prompt.arg_types": json.dumps(arg_types),
        "lilypad.prompt.arg_values": json.dumps(arg_values),
        "lilypad.prompt.output": results,
        "lilypad.is_async": is_async,
    }


class PromptDecorator(Protocol):
    """Protocol for the `prompt` decorator return type."""

    @overload
    def __call__(
        self, fn: Callable[_P, Coroutine[Any, Any, None]]
    ) -> Callable[_P, Coroutine[Any, Any, Prompt]]: ...

    @overload
    def __call__(self, fn: Callable[_P, None]) -> Callable[_P, Prompt]: ...

    def __call__(
        self, fn: Callable[_P, None] | Callable[_P, Coroutine[Any, Any, None]]
    ) -> Callable[_P, Prompt] | Callable[_P, Coroutine[Any, Any, Prompt]]:
        """Protocol `call` definition for `prompt` decorator return type."""
        ...


def _trace(
    prompt: PromptPublic, arg_types: dict[str, str], arg_values: dict[str, Any]
) -> PromptDecorator:
    @overload
    def decorator(
        fn: Callable[_P, Coroutine[Any, Any, None]],
    ) -> Callable[_P, Coroutine[Any, Any, Prompt]]: ...

    @overload
    def decorator(fn: Callable[_P, None]) -> Callable[_P, Prompt]: ...

    def decorator(
        fn: Callable[_P, None] | Callable[_P, Coroutine[Any, Any, None]],
    ) -> Callable[_P, Prompt] | Callable[_P, Coroutine[Any, Any, Prompt]]:
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> Prompt:
                with get_tracer("lilypad").start_as_current_span(
                    f"{fn.__name__}"
                ) as span:
                    _prompt = Prompt(
                        template=prompt.template,
                        common_call_params=prompt.call_params or {},
                        arg_values=arg_values,
                    )
                    attributes: dict[str, AttributeValue] = _construct_trace_attributes(
                        prompt, arg_types, arg_values, str(prompt.model_dump()), False
                    )
                    span.set_attributes(attributes)
                return _prompt

            return inner_async
        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> Prompt:
                with get_tracer("lilypad").start_as_current_span(
                    f"{fn.__name__}"
                ) as span:
                    _prompt = Prompt(
                        template=prompt.template,
                        common_call_params=prompt.call_params or {},
                        arg_values=arg_values,
                    )
                    attributes: dict[str, AttributeValue] = _construct_trace_attributes(
                        prompt, arg_types, arg_values, str(prompt.model_dump()), False
                    )
                    span.set_attributes(attributes)
                return _prompt

            return inner

    return decorator


def prompt() -> PromptDecorator:
    """The `prompt` decorator for turning a Python function into an managed prompt.

    The decorated function will not be run and will be used only for it's signature. The
    function will be called with the data pulled from the database, and the return value
    will be the corresponding `Prompt` instance.

    Functions decorated with `prompt` will be versioned and traced automatically.

    Returns:
        PromptDecorator: The `prompt` decorator.
    """

    @overload
    def decorator(
        fn: Callable[_P, Coroutine[Any, Any, None]],
    ) -> Callable[_P, Coroutine[Any, Any, Prompt]]: ...

    @overload
    def decorator(fn: Callable[_P, None]) -> Callable[_P, Prompt]: ...

    def decorator(
        fn: Callable[_P, None] | Callable[_P, Coroutine[Any, Any, None]],
    ) -> Callable[_P, Prompt] | Callable[_P, Coroutine[Any, Any, Prompt]]:
        closure = Closure.from_fn(fn)
        if inspect.iscoroutinefunction(fn):

            @wraps(fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> Prompt:
                arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
                if not (generation := current_generation.get()):
                    raise RuntimeError(
                        "Prompt must be run inside a `generation` decorated function."
                    )
                if prompt := generation.prompt:
                    if prompt.hash == closure.hash:
                        decorator = _trace(prompt, arg_types, arg_values)
                        return await decorator(fn)(*args, **kwargs)
                    raise ValueError(
                        "Prompt does not match signature of parent generations's prompt."
                    )
                raise ValueError("Parent generation does not have a prompt selected.")

            return inner_async
        else:

            @wraps(fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> Prompt:
                arg_types, arg_values = inspect_arguments(fn, *args, **kwargs)
                if not (generation := current_generation.get()):
                    raise RuntimeError(
                        "Prompt must be run inside a `generation` decorated function."
                    )
                if prompt := generation.prompt:
                    if prompt.hash == closure.hash:
                        decorator = _trace(prompt, arg_types, arg_values)
                        return decorator(fn)(*args, **kwargs)  # pyright: ignore [reportReturnType]
                    raise ValueError(
                        "Prompt does not match signature of parent generations's prompt."
                    )
                raise ValueError("Parent generation does not have a prompt selected.")

            return inner

    return decorator


__all__ = ["prompt"]
