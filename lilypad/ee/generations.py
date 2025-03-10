"""EE Generations module for Lilypad."""

from __future__ import annotations

from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any, ParamSpec, TypeAlias, TypeVar

from ee.validate import Tier, require_license
from lilypad._utils.sandbox import SandBoxFactory, SandboxRunner
from lilypad.server.client import LilypadClient
from lilypad.server.schemas import GenerationPublic

if TYPE_CHECKING:
    from lilypad.generations import Generation

_MANGED_PROMPT_TEMPLATE: TypeAlias = bool
_P = ParamSpec("_P")
_R = TypeVar("_R")
_SandBoxRunnerT = TypeVar("_SandBoxRunnerT", bound=SandboxRunner)


def _specific_generation_version_sync_factory(
    fn: Callable[_P, _R],
    sandbox_factory: SandBoxFactory[_SandBoxRunnerT] | None,
    _create_inner_sync: Callable[
        [
            Callable[_P, tuple[GenerationPublic, _MANGED_PROMPT_TEMPLATE]],
            SandBoxFactory[_SandBoxRunnerT] | None,
        ],
        Callable[_P, _R] | Callable[_P, Generation[_R]],
    ],
    lilypad_client: LilypadClient,
) -> Callable[
    [int, SandBoxFactory[_SandBoxRunnerT] | None],
    Callable[_P, _R] | Callable[_P, Generation[_R]],
]:
    """Create a _specific_generation_version_sync function for a function."""

    @require_license(tiers={Tier.PRO, Tier.TEAM, Tier.ENTERPRISE})
    def _specific_generation_version_sync(
        forced_version: int,
        override_sandbox_factory: SandBoxFactory[_SandBoxRunnerT] | None = None,
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

        return _create_inner_sync(
            _get_specific_version, override_sandbox_factory or sandbox_factory
        )

    return _specific_generation_version_sync


def _specific_generation_version_async_factory(
    fn: Callable[_P, Coroutine[Any, Any, _R]],
    sandbox_factory: SandBoxFactory[_SandBoxRunnerT] | None,
    _create_inner_async: Callable[
        [
            Callable[_P, tuple[GenerationPublic, _MANGED_PROMPT_TEMPLATE]],
            SandBoxFactory[_SandBoxRunnerT] | None,
        ],
        Callable[_P, Coroutine[Any, Any, _R]]
        | Callable[_P, Coroutine[Any, Any, Generation[_R]]],
    ],
    lilypad_client: LilypadClient,
) -> Callable[
    [int, SandBoxFactory[_SandBoxRunnerT] | None],
    Callable[_P, Coroutine[Any, Any, _R]]
    | Callable[_P, Coroutine[Any, Any, Generation[_R]]],
]:
    """Create a _specific_generation_version_async function for a function."""

    @require_license(tiers={Tier.PRO, Tier.TEAM, Tier.ENTERPRISE})
    def _specific_generation_version_async(
        forced_version: int,
        override_sandbox_factory: SandBoxFactory[_SandBoxRunnerT] | None = None,
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

        return _create_inner_async(
            _get_specific_version, override_sandbox_factory or sandbox_factory
        )

    return _specific_generation_version_async
