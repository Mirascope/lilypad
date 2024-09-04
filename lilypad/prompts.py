"""Utility for retrieving the prompt for a function."""

import hashlib
import inspect
from collections.abc import Callable
from functools import wraps
from typing import Any, ParamSpec, TypeVar

from mirascope.core import base
from pydantic import create_model

from .dummy_database import get_dummy_database

_P = ParamSpec("_P")
_R = TypeVar("_R")


def prompt(fn: Callable[_P, _R]) -> Callable[_P, base.BasePrompt]:
    """Returns a method for constructing a `BasePrompt` using `fn`'s args."""
    unique_id = hashlib.sha256(
        f"{fn.__name__}:{inspect.signature(fn)}".encode()
    ).hexdigest()
    prompt_template = get_dummy_database()[unique_id]["prompt_template"]
    template_vars = base._utils.get_template_variables(
        prompt_template, include_format_spec=False
    )

    @wraps(fn)
    def inner(*args: _P.args, **kwargs: _P.kwargs) -> base.BasePrompt:
        fn_args = {
            name: value
            for name, value in base._utils.get_fn_args(fn, args, kwargs).items()
            if name in template_vars
        }
        fields: dict[str, Any] = {
            name: (type(value), ...) for name, value in fn_args.items()
        }
        prompt_type = base.prompt_template(prompt_template)(
            create_model(
                "Prompt",
                __base__=base.BasePrompt,
                **fields,
            )
        )
        return prompt_type(**fn_args)

    return inner
