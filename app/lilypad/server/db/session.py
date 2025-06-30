"""Database session management"""

import threading
from collections.abc import AsyncGenerator, Generator
from typing import Any

from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool
from sqlmodel import Session, create_engine

from ..settings import get_settings


def get_database_url(environment: str | None = None) -> str:
    """Get a SQLite or PostgreSQL database URL

    Args:
        environment (str): Override the environment to use. Defaults to None.

    Returns:
        str: The database URL
    """
    settings = get_settings()
    if not environment:
        environment = settings.environment
    if environment == "local" or environment == "test":
        database_url = "sqlite:///pad.db"
    else:  # pragma: no cover
        database_url = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    return database_url


def get_async_database_url(environment: str | None = None) -> str:
    """Get an async SQLite or PostgreSQL database URL

    Args:
        environment (str): Override the environment to use. Defaults to None.

    Returns:
        str: The async database URL
    """
    settings = get_settings()
    if not environment:
        environment = settings.environment
    if environment == "local" or environment == "test":
        # SQLite async URL uses aiosqlite
        database_url = "sqlite+aiosqlite:///pad.db"
    else:  # pragma: no cover
        # PostgreSQL async URL uses asyncpg
        database_url = f"postgresql+asyncpg://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    return database_url


class DatabaseEngine:
    """Thread-safe database engine singleton"""

    _engine: Engine | None = None
    _async_engine: AsyncEngine | None = None
    _engine_lock = threading.RLock()  # Use RLock for reentrant locking
    _async_engine_lock = threading.RLock()  # Use RLock for reentrant locking

    def get_engine(self, environment: str | None = None) -> Engine:
        """Get the database engine (thread-safe with double-checked locking)"""
        # First check without lock for performance
        if self._engine is not None:
            return self._engine

        # Acquire lock for creation
        with self._engine_lock:
            # Double-check after acquiring lock
            if self._engine is None:
                database_url = get_database_url(environment)
                if database_url.startswith("sqlite"):
                    # SQLite configuration for development/testing
                    # check_same_thread=False allows sharing connections between threads
                    self._engine = create_engine(
                        database_url,
                        connect_args={"check_same_thread": False},
                        pool_pre_ping=True,
                    )
                else:  # pragma: no cover
                    settings = get_settings()
                    self._engine = create_engine(
                        database_url,
                        pool_size=settings.db_pool_size,
                        max_overflow=settings.db_max_overflow,
                        pool_pre_ping=settings.db_pool_pre_ping,
                        pool_recycle=settings.db_pool_recycle,
                        pool_timeout=settings.db_pool_timeout,
                    )
        return self._engine

    def get_async_engine(self, environment: str | None = None) -> AsyncEngine:
        """Get the async database engine (thread-safe with double-checked locking)"""
        # First check without lock for performance
        if self._async_engine is not None:
            return self._async_engine

        # Acquire lock for creation
        with self._async_engine_lock:
            # Double-check after acquiring lock
            if self._async_engine is None:
                database_url = get_async_database_url(environment)
                if "sqlite" in database_url:
                    # WARNING: check_same_thread=False is required for async SQLite but
                    # can cause issues with concurrent writes. This is acceptable for
                    # development/testing but proper test isolation should be implemented.
                    # Production uses PostgreSQL which doesn't have this limitation.
                    self._async_engine = create_async_engine(
                        database_url,
                        connect_args={
                            "check_same_thread": False,  # Required for async, see warning above
                            "timeout": 10.0,
                        },
                        poolclass=NullPool,  # NullPool for async SQLite to avoid connection issues
                    )
                else:  # pragma: no cover
                    settings = get_settings()
                    self._async_engine = create_async_engine(
                        database_url,
                        pool_size=settings.db_pool_size,
                        max_overflow=settings.db_max_overflow,
                        pool_pre_ping=settings.db_pool_pre_ping,
                        pool_recycle=settings.db_pool_recycle,
                        pool_timeout=settings.db_pool_timeout,
                    )
        return self._async_engine

    def dispose(self) -> None:
        """Dispose of sync engine and connections"""
        if self._engine:
            self._engine.dispose()
            self._engine = None

    async def dispose_async(self) -> None:
        """Dispose of async engine and connections"""
        if self._async_engine:
            await self._async_engine.dispose()
            self._async_engine = None

    async def dispose_all(self) -> None:
        """Dispose of all engines"""
        self.dispose()
        await self.dispose_async()

    def get_pool_status(self) -> dict[str, Any]:
        """Get connection pool status for monitoring"""
        status = {}

        if self._engine:
            try:
                pool = self._engine.pool
                status["sync"] = {
                    "size": getattr(pool, "size", lambda: None)(),
                    "checked_in": getattr(pool, "checkedin", lambda: None)(),
                    "overflow": getattr(pool, "overflow", lambda: None)(),
                    "total": getattr(pool, "total", lambda: None)(),
                }
            except Exception:
                status["sync"] = {"error": "Pool info not available"}

        if self._async_engine:
            try:
                pool = self._async_engine.pool
                status["async"] = {
                    "size": getattr(pool, "size", lambda: None)(),
                    "checked_in": getattr(pool, "checkedin", lambda: None)(),
                    "overflow": getattr(pool, "overflow", lambda: None)(),
                    "total": getattr(pool, "total", lambda: None)(),
                }
            except Exception:
                status["async"] = {"error": "Pool info not available"}

        return status


db = DatabaseEngine()


def get_session() -> Generator[Session, None, None]:
    """Get a SQLModel session"""
    engine = db.get_engine()
    with Session(engine) as session:
        yield session
        try:  # pragma: no cover
            session.flush()
        except Exception:  # pragma: no cover
            session.rollback()
            raise
        else:  # pragma: no cover
            session.commit()


def create_session() -> Session:
    """Create a new SQLModel session that must be manually managed.

    Note: The caller is responsible for committing and closing the session.
    """
    engine = db.get_engine()
    return Session(engine)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get an async SQLModel session with proper transaction handling"""
    engine = db.get_async_engine()
    async with AsyncSession(engine, expire_on_commit=True) as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


def create_async_session() -> AsyncSession:
    """Create a new async SQLModel session that must be manually managed.

    Note: The caller is responsible for committing and closing the session.
    """
    engine = db.get_async_engine()
    return AsyncSession(engine)
