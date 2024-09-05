"""Database session management"""

from collections.abc import Generator

from sqlmodel import Session, create_engine

from lilypad.app.models.projects import ProjectTable

engine = create_engine("sqlite:///database.db")


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
