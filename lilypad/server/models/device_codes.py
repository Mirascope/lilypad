"""Device codes table and models."""

from sqlmodel import Field

from .base_sql_model import BaseSQLModel
from .table_names import DEVICE_CODE_TABLE_NAME


class DeviceCodeTable(BaseSQLModel, table=True):
    """Device codes table."""

    __tablename__ = DEVICE_CODE_TABLE_NAME  # type: ignore

    id: str = Field(
        primary_key=True, nullable=False, description="Generated device code"
    )
    token: str = Field(nullable=False)
