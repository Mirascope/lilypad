"""Create the database tables."""

from sqlmodel import SQLModel

from lilypad.server.db.session import get_engine
from lilypad.server.models import *  # noqa: F403


def create_tables(environment: str | None = None) -> None:
    """Create the database tables."""
    SQLModel.metadata.create_all(get_engine(environment))


if __name__ == "__main__":
    create_tables()
