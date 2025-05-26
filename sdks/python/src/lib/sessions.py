"""Run context utilities: Run dataclass, RUN_CONTEXT variable and run() context-manager."""

from __future__ import annotations

import uuid
from typing import Iterator
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass

_UNSET = object()


@dataclass(slots=True)
class Session:
    """Lightweight container for a session identifier."""

    id: str | None = None

    @staticmethod
    def generate_id() -> str:
        """Return a new 32-char hexadecimal SessionID."""
        return uuid.uuid4().hex


SESSION_CONTEXT: ContextVar[Session | None] = ContextVar("SESSION_CONTEXT", default=None)


@contextmanager
def session(id: str | None = _UNSET) -> Iterator[Session]:
    """Create a Session context."""

    if id is _UNSET:
        session_id = Session.generate_id()
    else:
        session_id = id
    session_obj = Session(session_id)
    token = SESSION_CONTEXT.set(session_obj)
    try:
        yield session_obj
    finally:
        SESSION_CONTEXT.reset(token)
