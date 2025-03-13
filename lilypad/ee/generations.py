"""EE Generations module for Lilypad."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any, ParamSpec, TypeAlias, TypeVar

from .._utils.license import require_license
from ..sandbox import SandboxRunner
from ..server.client import GenerationPublic, LilypadClient, Tier

if TYPE_CHECKING:
    from ..generations import Generation

_MANGED_PROMPT_TEMPLATE: TypeAlias = bool
_P = ParamSpec("_P")
_R = TypeVar("_R")


def specific_generation_version_sync_factory(
    fn: Callable[_P, _R],
    _create_inner_sync: Callable[
        [
            Callable[_P, tuple[GenerationPublic, _MANGED_PROMPT_TEMPLATE]],
            SandboxRunner | None,
        ],
        Callable[_P, _R] | Callable[_P, Generation[_R]],
    ],
    lilypad_client: LilypadClient,
) -> Callable[
    [int, SandboxRunner | None],
    Callable[_P, _R] | Callable[_P, Generation[_R]],
]:
    """Create a _specific_generation_version_sync function for a function."""

    @require_license(tier=Tier.PRO)
    def _specific_generation_version_sync(
        forced_version: int,
        sandbox_runner: SandboxRunner | None = None,
    ) -> Callable[_P, _R] | Callable[_P, Generation[_R]]:
        specific_version_generation = lilypad_client.get_generation_by_version(
            fn,
            version=forced_version,
        )
        if not specific_version_generation:
            raise ValueError(
                f"Generation version {forced_version} not found for function: {fn.__name__}"
            )

        def _get_specific_version(
            *args: _P.args, **kwargs: _P.kwargs
        ) -> tuple[GenerationPublic, _MANGED_PROMPT_TEMPLATE]:
            return specific_version_generation, True

        return _create_inner_sync(_get_specific_version, sandbox_runner)

    return _specific_generation_version_sync  # pyright: ignore [reportReturnType]


def specific_generation_version_async_factory(
    fn: Callable[_P, Coroutine[Any, Any, _R]],
    _create_inner_async: Callable[
        [
            Callable[_P, tuple[GenerationPublic, _MANGED_PROMPT_TEMPLATE]],
            SandboxRunner | None,
        ],
        Callable[_P, Coroutine[Any, Any, _R]]
        | Callable[_P, Coroutine[Any, Any, Generation[_R]]],
    ],
    lilypad_client: LilypadClient,
) -> Callable[
    [int, SandboxRunner | None],
    Callable[_P, Coroutine[Any, Any, _R]]
    | Callable[_P, Coroutine[Any, Any, Generation[_R]]],
]:
    """Create a _specific_generation_version_async function for a function."""

    @require_license(tier=Tier.PRO)
    def _specific_generation_version_async(
        forced_version: int,
        sandbox_runner: SandboxRunner | None = None,
    ) -> (
        Callable[_P, Coroutine[Any, Any, _R]]
        | Callable[_P, Coroutine[Any, Any, Generation[_R]]]
    ):
        specific_version_generation = lilypad_client.get_generation_by_version(
            fn,
            version=forced_version,
        )
        if not specific_version_generation:
            raise ValueError(
                f"Generation version {forced_version} not found for function: {fn.__name__}"
            )

        def _get_specific_version(
            *args: _P.args, **kwargs: _P.kwargs
        ) -> tuple[GenerationPublic, _MANGED_PROMPT_TEMPLATE]:
            return specific_version_generation, True

        return _create_inner_async(_get_specific_version, sandbox_runner)

    return _specific_generation_version_async  # pyright: ignore [reportReturnType]
