"""Settings and configuration for Lilypad SDK."""

from __future__ import annotations

from typing import Any
from functools import cache
from contextvars import ContextVar

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global settings for Lilypad SDK."""

    base_url: str | None = Field(default=None)
    api_key: str | None = None
    project_id: str | None = None

    def update(self, **kwargs: Any) -> None:
        """Update non-None fields in place."""
        for k, v in kwargs.items():
            if v is not None and hasattr(self, k):
                setattr(self, k, v)

    model_config = SettingsConfigDict(env_prefix="LILYPAD_")


@cache
def _default_settings() -> Settings:
    return Settings()


_current_settings: ContextVar[Settings | None] = ContextVar(
    "_current_settings", default=None
)


def get_settings() -> Settings:
    """Return Settings for the current context."""
    settings = _current_settings.get()
    if settings is None:
        settings = _default_settings()
        _current_settings.set(settings)
    return settings


def _set_settings(settings: Settings) -> None:
    """Replace Settings in the current context."""
    _current_settings.set(settings)
