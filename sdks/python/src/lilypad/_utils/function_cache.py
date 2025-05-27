"""Utilities for caching Function metadata fetched from the Lilypad API."""

from __future__ import annotations

import asyncio
import threading
from time import time
from typing import Any, Final, Generic, TypeVar
from functools import lru_cache  # noqa: TID251
from collections import OrderedDict
from collections.abc import Callable, Awaitable, Coroutine

from . import Closure
from .client import get_sync_client, get_async_client
from ..generated.types.function_public import FunctionPublic

_HASH_SYNC_MAX = 2_048
_hash_async_lock = asyncio.Lock()
_hash_async_cache: dict[tuple[str, str], FunctionPublic] = {}

_VERSION_SYNC_MAX = 2_048
_version_async_lock = asyncio.Lock()
_version_async_cache: dict[tuple[str, str, int], FunctionPublic] = {}


_Future = Coroutine[Any, Any, FunctionPublic] | Awaitable[FunctionPublic]

_Key = tuple[str, str]  # (project_uuid, function_name | function_hash)

_Hit = tuple[float, FunctionPublic]  # (timestamp, value)

_deployed_cache: dict[_Key, _Hit] = {}
_hash_cache: dict[_Key, FunctionPublic] = {}

_hash_lock = threading.Lock()
_deployed_sync_lock = threading.Lock()
_deployed_async_lock = asyncio.Lock()

_DEFAULT_DEPLOY_TTL = 30.0  # seconds


@lru_cache(maxsize=_HASH_SYNC_MAX)
def get_function_by_hash_sync(project_uuid: str, function_hash: str) -> FunctionPublic:
    """Synchronous, cached `retrieve_by_hash`."""
    client = get_sync_client()
    return client.projects.functions.get_by_hash(
        project_uuid=project_uuid,
        function_hash=function_hash,
    )


async def get_function_by_hash_async(project_uuid: str, function_hash: str) -> FunctionPublic:
    """Asynchronous, cached `retrieve_by_hash`."""
    key = (project_uuid, function_hash)
    if key in _hash_async_cache:
        return _hash_async_cache[key]

    async with _hash_async_lock:
        if key in _hash_async_cache:  # lost race
            return _hash_async_cache[key]

        client = get_async_client()
        fn = await client.projects.functions.get_by_hash(
            project_uuid=project_uuid,
            function_hash=function_hash,
        )
        _hash_async_cache[key] = fn
        return fn


@lru_cache(maxsize=_VERSION_SYNC_MAX)
def get_function_by_version_sync(
    project_uuid: str,
    function_name: str,
    version_num: int,
) -> FunctionPublic:
    """Synchronous, cached `retrieve_by_version`."""
    client = get_sync_client()
    return client.projects.functions.get_by_version(
        project_uuid=project_uuid,
        function_name=function_name,
        version_num=version_num,
    )


async def get_function_by_version_async(
    project_uuid: str,
    function_name: str,
    version_num: int,
) -> FunctionPublic:
    """Asynchronous, cached `retrieve_by_version`."""
    key = (project_uuid, function_name, version_num)
    if key in _version_async_cache:
        return _version_async_cache[key]

    async with _version_async_lock:
        if key in _version_async_cache:
            return _version_async_cache[key]

        client = get_async_client()
        fn = await client.projects.functions.get_by_version(
            project_uuid=project_uuid,
            function_name=function_name,
            version_num=version_num,
        )
        _version_async_cache[key] = fn
        return fn


def _expired(ts: float, ttl: float) -> bool:
    return 0 < ttl < time() - ts


def get_deployed_function_sync(
    project_uuid: str,
    function_name: str,
    *,
    ttl: float | None = None,
    force_refresh: bool = False,
) -> FunctionPublic:
    if ttl is None:
        ttl = _DEFAULT_DEPLOY_TTL
    key: _Key = (project_uuid, function_name)
    if not force_refresh:
        with _deployed_sync_lock:
            ts, fn = _deployed_cache.get(key, (0.0, None))  # type: ignore[misc]
            if fn is not None and not _expired(ts, ttl):
                return fn

    client = get_sync_client()
    fn = client.projects.functions.get_deployed_environments(
        project_uuid=project_uuid,
        function_name=function_name,
    )

    with _deployed_sync_lock:
        _deployed_cache[key] = (time(), fn)
    return fn


async def get_deployed_function_async(
    project_uuid: str,
    function_name: str,
    *,
    ttl: float | None = None,
    force_refresh: bool = False,
) -> FunctionPublic:
    if ttl is None:
        ttl = _DEFAULT_DEPLOY_TTL
    key: _Key = (project_uuid, function_name)
    if not force_refresh:
        entry = _deployed_cache.get(key)
        if entry and not _expired(entry[0], ttl):
            return entry[1]

    async with _deployed_async_lock:
        # another coroutine might have filled the cache
        if not force_refresh:
            entry = _deployed_cache.get(key)
            if entry and not _expired(entry[0], ttl):
                return entry[1]

        client = get_async_client()
        fn = await client.projects.functions.get_deployed_environments(
            project_uuid=project_uuid,
            function_name=function_name,
        )
        _deployed_cache[key] = (time(), fn)
        return fn


_T = TypeVar("_T")


class _LRU(OrderedDict[str, _T], Generic[_T]):  # noqa: D101
    __slots__: tuple[str, ...] = ("_lock", "_max")

    def __init__(self, maxsize: int) -> None:  # noqa: D401
        super().__init__()
        self._lock = threading.Lock()
        self._max = maxsize

    def get_or_create(self, key: str, factory: Callable[..., _T]) -> _T:
        with self._lock:
            try:
                self.move_to_end(key)
                return self[key]
            except KeyError:
                value = factory()
                self[key] = value
                if len(self) > self._max:
                    self.popitem(last=False)  # evict least‑recent
                return value


_MAX_ENTRIES: Final[int] = 256
_CLOSURE_CACHE: Final[_LRU[Closure]] = _LRU(_MAX_ENTRIES)


def get_cached_closure(function: FunctionPublic) -> Closure:
    """Return a `Closure` for *function*, caching by its UUID."""
    key = str(function.uuid_)

    def _build() -> Closure:
        return Closure(
            name=function.name,
            code=function.code,
            signature=function.signature,
            hash=function.hash,
            dependencies={k: v.model_dump(mode="python") for k, v in (function.dependencies or {}).items()},
        )

    return _CLOSURE_CACHE.get_or_create(key, _build)


__all__ = [
    "get_deployed_function_async",
    "get_deployed_function_sync",
    "get_function_by_hash_async",
    "get_function_by_hash_sync",
    "get_function_by_version_async",
    "get_function_by_version_sync",
]
