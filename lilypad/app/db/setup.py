"""Create the database tables."""

from sqlmodel import SQLModel

from lilypad.app.db.session import engine

SQLModel.metadata.create_all(engine)
