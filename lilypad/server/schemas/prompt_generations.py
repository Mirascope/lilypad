"""prompt and generation schemas.

This is to handle circular imports between prompt and generation schemas.
"""

from __future__ import annotations

from uuid import UUID

from .generations import _GenerationBase
from .prompts import _PromptBase
from .response_models import ResponseModelPublic


class PromptPublic(_PromptBase):
    """Prompt public model."""

    uuid: UUID
    generation: GenerationPublic


class GenerationPublic(_GenerationBase):
    """Generation public model."""

    uuid: UUID
    prompt: PromptPublic | None = None
    response_model: ResponseModelPublic | None = None
