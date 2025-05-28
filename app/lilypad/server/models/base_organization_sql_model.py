"""Base Organization SQLModel class from which all `client` SQLModel classes inherit."""

from uuid import UUID

from sqlmodel import Field

from .base_sql_model import BaseSQLModel
from .table_names import ORGANIZATION_TABLE_NAME


class BaseOrganizationSQLModel(BaseSQLModel):
    """Base SQLModel class"""

    organization_uuid: UUID = Field(
        index=True, foreign_key=f"{ORGANIZATION_TABLE_NAME}.uuid", ondelete="CASCADE"
    )
