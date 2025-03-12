from collections.abc import Callable, Coroutine
from datetime import datetime, timezone
from functools import wraps
from typing import Any, ParamSpec, TypeVar, overload

from ..exceptions import LicenseError
from ..server.client import LicenseInfo, Tier
from . import fn_is_async, load_config

_P = ParamSpec("_P")
_R = TypeVar("_R")


def _validate_license_with_client(
    cached_license: LicenseInfo | None, tier: Tier
) -> LicenseInfo | None:
    if cached_license:
        if cached_license.info < tier:
            cached_license = None
        if cached_license.info.expires_at < datetime.now(timezone.utc):
            cached_license = None
    if not cached_license:
        config = load_config()
        from lilypad.server.client import LilypadClient

        lilypad_client = LilypadClient(
            token=config.get("token", None),
        )
        cached_license = lilypad_client.get_license_info()
    if cached_license.tier < tier:
        raise LicenseError("Invalid License. Contact support@mirascope.com to get one.")
    return cached_license


@overload
def require_license(
    tier: Tier,
) -> Callable[[Callable[_P, _R]], Callable[_P, _R]]: ...


@overload
def require_license(
    tier: Tier,
) -> Callable[
    [Callable[_P, Coroutine[Any, Any, _R]]], Callable[_P, Coroutine[Any, Any, _R]]
]: ...


def require_license(
    tier: Tier,
) -> Callable[
    [Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]],
    Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
]:
    """Decorator to require a valid license for a function"""

    @overload
    def decorator(func: Callable[_P, _R]) -> Callable[_P, _R]: ...

    @overload
    def decorator(
        func: Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, Coroutine[Any, Any, _R]]: ...

    def decorator(
        func: Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]],
    ) -> Callable[_P, _R] | Callable[_P, Coroutine[Any, Any, _R]]:
        _cached_license_info: LicenseInfo | None = None

        if fn_is_async(func):

            @wraps(func)
            async def async_wrapper(
                *args: _P.args, **kwargs: _P.kwargs
            ) -> Coroutine[Any, Any, _R]:
                nonlocal _cached_license_info
                _cached_license_info = _validate_license_with_client(
                    _cached_license_info, tier
                )
                return await func(*args, **kwargs)

            return async_wrapper
        else:

            @wraps(func)
            def sync_wrapper(*args: _P.args, **kwargs: _P.kwargs) -> _R:
                nonlocal _cached_license_info
                _cached_license_info = _validate_license_with_client(
                    _cached_license_info, tier
                )
                return func(*args, **kwargs)

            return sync_wrapper

    return decorator
