"""Create the database tables."""

from sqlmodel import SQLModel

from lilypad.ee.server.models import *  # noqa: F403
from lilypad.server.db.session import db
from lilypad.server.models import *  # noqa: F403


def create_tables(environment: str | None = None) -> None:
    """Create the database tables."""
    SQLModel.metadata.create_all(db.get_engine(environment))


if __name__ == "__main__":
    create_tables()
