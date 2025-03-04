"""Utility module for setting up loggers and log handlers."""

import logging
import traceback
from collections.abc import Callable, Coroutine
from functools import wraps
from typing import Any, ParamSpec, TypeVar, overload

from ..exceptions import LilypadException
from .fn_is_async import fn_is_async

_P = ParamSpec("_P")
_R = TypeVar("_R")


def _default_logger(name: str = "lilypad") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


@overload
def call_safely(
    child_fn: Callable[_P, Coroutine[Any, Any, _R]],
) -> Callable[
    [Callable[_P, Coroutine[Any, Any, _R]]], Callable[_P, Coroutine[Any, Any, _R]]
]: ...


@overload
def call_safely(
    child_fn: Callable[_P, _R],
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]: ...


def call_safely(
    child_fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
) -> (
    Callable[
        [Callable[_P, Coroutine[Any, Any, _R]]], Callable[_P, Coroutine[Any, Any, _R]]
    ]
    | Callable[[Callable[_P, _R]], Callable[_P, _R]]
):
    @overload
    def decorator(
        fn: Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    @overload
    def decorator(fn: Callable[_P, _R]) -> Callable[_P, _R]: ...

    def decorator(
        fn: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        if fn_is_async(fn):

            @wraps(child_fn)
            async def inner_async(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                try:
                    return await fn(*args, **kwargs)
                except LilypadException as e:
                    logger = _default_logger()
                    logger.error(
                        "Error in wrapped function '%s': %s", fn.__name__, str(e)
                    )
                    logger.error("Exception type: %s", type(e).__name__)
                    tb_str = "".join(traceback.format_tb(e.__traceback__))
                    logger.error("Traceback:\n%s", tb_str)
                    logger.error(
                        "Function arguments - args: %s, kwargs: %s",
                        args,
                        {
                            k: "***" if "password" in k.lower() else v
                            for k, v in kwargs.items()
                        },
                    )
                    return await child_fn(*args, **kwargs)  # pyright: ignore [reportReturnType,reportGeneralTypeIssues]

            return inner_async
        else:

            @wraps(child_fn)
            def inner(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                try:
                    return fn(*args, **kwargs)  # pyright: ignore [reportReturnType]
                except LilypadException as e:
                    logger = _default_logger()
                    logger.error(
                        "Error in wrapped function '%s': %s", fn.__name__, str(e)
                    )
                    logger.error("Exception type: %s", type(e).__name__)
                    tb_str = "".join(traceback.format_tb(e.__traceback__))
                    logger.error("Traceback:\n%s", tb_str)
                    logger.error(
                        "Function arguments - args: %s, kwargs: %s",
                        args,
                        {
                            k: "***" if "password" in k.lower() else v
                            for k, v in kwargs.items()
                        },
                    )
                    return child_fn(*args, **kwargs)  # pyright: ignore [reportReturnType]

            return inner

    return decorator
