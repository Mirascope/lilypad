"""Database session management"""

import os
from collections.abc import Generator

from sqlalchemy.engine import Engine
from sqlmodel import Session, create_engine

from ..settings import get_settings


def get_engine(environment: str | None = None) -> Engine:
    """Get a sqlite or postgres engine

    Args:
        environment (str): Override the environment to use. Defaults to None.

    Returns:
        Engine: The SQLAlchemy engine
    """
    settings = get_settings()
    if not environment:
        environment = settings.environment
    if environment == "local" or environment == "test":
        db_directory = os.getenv("LILYPAD_PROJECT_DIR", os.getcwd())
        engine = create_engine(
            f"sqlite:///{db_directory}/pad.db",
            connect_args={"check_same_thread": False},
        )
    else:
        database_url = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
        engine = create_engine(database_url)
    return engine


def get_session() -> Generator[Session, None, None]:
    """Get a SQLModel session"""
    engine = get_engine()
    with Session(engine) as session:
        yield session
        try:
            session.flush()
        except Exception:
            session.rollback()
            raise
        else:
            session.commit()
