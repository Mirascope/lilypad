"""Create the database tables."""

from sqlmodel import SQLModel

from lilypad.server.db.session import engine
from lilypad.server.models import *  # noqa: F403


def create_tables() -> None:
    """Create the database tables."""
    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    create_tables()
