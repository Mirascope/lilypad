"""Create the database tables."""

from sqlmodel import SQLModel

from lilypad.server.db.session import engine
from lilypad.server.models import *  # noqa: F403

SQLModel.metadata.create_all(engine)
