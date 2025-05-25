"""Create the database tables."""

from sqlmodel import SQLModel

from ...ee.server.models import *  # noqa: F403
from ...server.db.session import db
from ...server.models import *  # noqa: F403


def create_tables(environment: str | None = None) -> None:
    """Create the database tables."""
    SQLModel.metadata.create_all(db.get_engine(environment))


if __name__ == "__main__":
    create_tables()
