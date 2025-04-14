from uuid import UUID
from sqlmodel import Field, SQLModel
from .table_names import FUNCTION_TABLE_NAME, TAG_TABLE_NAME, FUNCTION_TAG_LINK_TABLE_NAME

class FunctionTagLink(SQLModel, table=True):
    __tablename__ = FUNCTION_TAG_LINK_TABLE_NAME
    function_uuid: UUID | None = Field(
        default=None, foreign_key=f"{FUNCTION_TABLE_NAME}.uuid", primary_key=True
    )
    tag_uuid: UUID | None = Field(
        default=None, foreign_key=f"{TAG_TABLE_NAME}.uuid", primary_key=True
    )