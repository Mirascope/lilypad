"""Database session management"""

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
        database_url = "sqlite:///pad.db"
    else:  # pragma: no cover
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
            else:  # pragma: no cover
                settings = get_settings()
                self._engine = create_engine(
                    database_url,
                    pool_size=settings.db_pool_size,
                    max_overflow=settings.db_max_overflow,
                    pool_pre_ping=settings.db_pool_pre_ping,
                    pool_recycle=settings.db_pool_recycle,
                )
        return self._engine


db = DatabaseEngine()


def get_session() -> Generator[Session, None, None]:
    """Get a SQLModel session"""
    engine = db.get_engine()
    with Session(engine) as session:
        yield session
        try:  # pragma: no cover
            session.flush()  # pragma: no cover
        except Exception:  # pragma: no cover
            session.rollback()  # pragma: no cover
            raise  # pragma: no cover
        else:  # pragma: no cover
            session.commit()  # pragma: no cover


def create_session() -> Session:
    """Create a new SQLModel session that must be manually managed.

    Note: The caller is responsible for committing and closing the session.
    """
    engine = db.get_engine()
    return Session(engine)
