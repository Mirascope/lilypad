"""Database session management"""

import os
from collections.abc import Generator

from sqlalchemy.engine import Engine
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
        db_directory = os.getenv("LILYPAD_PROJECT_DIR", os.getcwd())
        database_url = f"sqlite:///{db_directory}/pad.db"
    else:
        database_url = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    return database_url


class DatabaseEngine:
    """Database engine singleton"""

    _engine: Engine | None = None

    def get_engine(self, environment: str | None = None) -> Engine:
        """Get the database engine"""
        if self._engine is None:
            database_url = get_database_url(environment)
            if database_url.startswith("sqlite"):
                self._engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    pool_pre_ping=True,
                )
            else:
                self._engine = create_engine(
                    database_url, pool_size=5, max_overflow=10, pool_pre_ping=True
                )
        return self._engine


db = DatabaseEngine()


def get_session() -> Generator[Session, None, None]:
    """Get a SQLModel session"""
    engine = db.get_engine()
    with Session(engine) as session:
        yield session
        try:
            session.flush()
        except Exception:
            session.rollback()
            raise
        else:
            session.commit()
