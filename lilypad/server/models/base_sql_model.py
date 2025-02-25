"""Base SQLModel class from which all `lilypad` SQLModel classes inherit."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from pydantic import ConfigDict, field_serializer
from pydantic.types import AwareDatetime
from sqlalchemy import JSON, Column, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeEngine
from sqlmodel import DateTime, Field, SQLModel


class JSONTypeDecorator(TypeDecorator):
    """JSON type decorator."""

    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect: Dialect) -> TypeEngine:
        """Load dialect implementation."""
        if isinstance(dialect, PGDialect):
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


def get_json_column() -> Column:
    """Uses JSONB for PostgreSQL and JSON for other databases."""
    return Column(JSONTypeDecorator)


class BaseSQLModel(SQLModel):
    """Base SQLModel class"""

    uuid: UUID | None = Field(
        nullable=False,
        default_factory=uuid4,
        primary_key=True,
        schema_extra={"format": "uuid"},
    )
    created_at: Annotated[datetime, AwareDatetime] = Field(
        sa_type=DateTime(timezone=True),  # pyright: ignore [reportArgumentType]
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
        schema_extra={"format": "date-time"},
    )

    @field_serializer("uuid")
    def serialize_uuid(self, uuid: UUID) -> str:
        """Serialize the UUID."""
        return str(uuid)

    @field_serializer("created_at")
    def serialize_created_at(self, created_at: datetime) -> str:
        """Serialize the created_at datetime."""
        return created_at.isoformat()

    model_config = ConfigDict(  # pyright: ignore [reportAssignmentType]
        populate_by_name=True,
        from_attributes=True,
        validate_assignment=True,
    )


BaseSQLModel.metadata.naming_convention = {
    "ix": "%(column_0_label)s_idx",
    "uq": "%(table_name)s_%(column_0_name)s_key",
    "ck": "%(table_name)s_%(constraint_name)s_check",
    "fk": "%(table_name)s_%(column_0_name)s_%(referred_table_name)s_fkey",
    "pk": "%(table_name)s_pkey",
}
