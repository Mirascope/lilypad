"""Base SQLModel class for all SQLModel classes to inherit from"""

from pydantic import ConfigDict
from sqlmodel import SQLModel


class BaseSQLModel(SQLModel):
    """Base SQLModel class"""

    model_config = ConfigDict(  # pyright:ignore[reportAssignmentType]
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
