"""Base SQLModel class from which all `lilypad` SQLModel classes inherit."""

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any
from uuid import UUID, uuid4

from pydantic import ConfigDict, model_serializer
from sqlalchemy import JSON, Column, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.engine.interfaces import Dialect
from sqlalchemy.types import TypeEngine
from sqlmodel import Field, SQLModel


def get_json_column() -> Column:
    """Uses JSONB for PostgreSQL and JSON for other databases."""

    class JSONTypeDecorator(TypeDecorator):
        impl = JSON

        def load_dialect_impl(self, dialect: Dialect) -> TypeEngine:
            """Load dialect implementation."""
            if isinstance(dialect, PGDialect):
                return dialect.type_descriptor(JSONB())
            return dialect.type_descriptor(JSON())

    return Column(JSONTypeDecorator)


class BaseSQLModel(SQLModel):
    """Base SQLModel class"""

    uuid: UUID | None = Field(
        nullable=False,
        default_factory=uuid4,
        primary_key=True,
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    @model_serializer(mode="wrap")
    def serialize(
        self, original_serializer: Callable[["BaseSQLModel"], dict[str, Any]]
    ) -> dict[str, Any]:
        """Serialize datetime and UUID fields to strings."""
        for field_name, field_info in self.model_fields.items():
            if field_info.annotation == datetime or field_info.annotation == UUID:
                setattr(
                    self,
                    field_name,
                    str(getattr(self, field_name)),
                )

        result = original_serializer(self)

        for field_name, field_info in self.model_fields.items():
            if field_info.annotation == timedelta:
                result[field_name] = getattr(self, field_name).total_seconds()

        return result

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
