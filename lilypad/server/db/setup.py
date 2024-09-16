"""Create the database tables."""

from sqlmodel import SQLModel

from lilypad.app.db.session import engine
from lilypad.app.models import *  # noqa: F403

SQLModel.metadata.create_all(engine)
