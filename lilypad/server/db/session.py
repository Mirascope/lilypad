"""Database session management"""

import os
from collections.abc import Generator

from sqlmodel import Session, create_engine

db_directory = os.getenv("LILYPAD_PROJECT_DIR", os.getcwd())
engine = create_engine(
    f"sqlite:///{db_directory}/pad.db", connect_args={"check_same_thread": False}
)


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
