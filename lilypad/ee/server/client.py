"""The `lilypad.ee` API client."""

import logging
from collections.abc import Callable
from typing import Any, TypeVar

from pydantic import BaseModel

from ee import LicenseInfo

from ..._utils import Closure
from ...exceptions import LilypadNotFoundError
from ...server.client import LilypadClient as _LilypadClient
from ...server.schemas import GenerationPublic

_R = TypeVar("_R", bound=BaseModel)

log = logging.getLogger(__name__)


class LilypadEEClient(_LilypadClient):
    """Client for interacting with the Lilypad ee API."""

    def get_generation_by_version(
        self,
        fn: Callable[..., Any],
        version: int,
    ) -> GenerationPublic:
        """Get the matching version for a generation.

        Args:
            fn (Callable): The generation for which to get the version.
            version (int): If provided, force the retrieval of the generation with this version.

        Returns:
            GenerationPublic: The matching (or created) version for the generation.
        """
        closure = Closure.from_fn(fn)
        try:
            forced_version_num = int(version)
        except ValueError:
            raise ValueError(
                f"Version must be an integer. Received: '{version}' (type: {type(version).__name__})"
            )
        try:
            return self._request(
                "GET",
                f"v0/ee/projects/{self.project_uuid}/generations/name/{closure.name}/version/{forced_version_num}",
                response_model=GenerationPublic,
            )
        except LilypadNotFoundError:
            raise LilypadNotFoundError(
                f"Generation version '{version}' not found for signature {closure.signature}"
            )

    def get_generation_by_signature(
        self,
        fn: Callable[..., Any],
    ) -> GenerationPublic:
        """Get the matching name for a generation.

        Args:
            fn (Callable): The generation for which to get the version.

        Returns:
            GenerationPublic: The matching (or created) version for the generation.
        """
        closure = Closure.from_fn(fn)
        generations = self._request(
            "GET",
            f"v0/ee/projects/{self.project_uuid}/generations/name/{closure.name}",
            response_model=list[GenerationPublic],
        )
        for generation in generations:
            if generation.signature == closure.signature:
                return generation
        raise LilypadNotFoundError(
            f"Generation with signature '{closure.signature}' not found. Available signatures: {[g.signature for g in generations]}"
        )

    def get_generations_by_name(
        self,
        fn: Callable[..., Any],
    ) -> list[GenerationPublic]:
        """Get the matching name for a generation.

        Args:
            fn (Callable): The generation for which to get the all version.

        Returns:
            GenerationPublic: The matching versions for the generation.
        """
        closure = Closure.from_fn(fn)
        generations = self._request(
            "GET",
            f"v0/ee/projects/{self.project_uuid}/generations/name/{closure.name}",
            response_model=list[GenerationPublic],
        )
        if generations:
            return generations
        raise LilypadNotFoundError(f"Generation with name '{closure.name}' not found.")

    def get_license_info(self) -> LicenseInfo:
        """Get the license info for the organization."""
        return self._request("GET", f"/v0/ee/projects/{self.project_uuid}", LicenseInfo)
