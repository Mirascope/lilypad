"""Database session management"""

import os
from collections.abc import Generator

from sqlmodel import Session, create_engine

from ..settings import get_settings

settings = get_settings()
if settings.environment == "local" or settings.environment == "test":
    db_directory = os.getenv("LILYPAD_PROJECT_DIR", os.getcwd())
    engine = create_engine(
        f"sqlite:///{db_directory}/pad.db", connect_args={"check_same_thread": False}
    )
else:
    database_url = f"postgresql://{settings.db_user}:{settings.db_password}@{settings.db_host}:{settings.db_port}/{settings.db_name}"
    engine = create_engine(database_url)


def get_session() -> Generator[Session, None, None]:
    """Get a SQLModel session"""
    with Session(engine) as session:
        yield session
        try:
            session.flush()
        except Exception:
            session.rollback()
            raise
        else:
            session.commit()
