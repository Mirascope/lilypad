"""Model for storing external API keys."""

from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlmodel import Field, Relationship, SQLModel

from .table_names import EXTERNAL_API_KEY_TABLE_NAME, USER_TABLE_NAME

if TYPE_CHECKING:
    from .users import UserTable


class ExternalAPIKeyBase(SQLModel):
    """Base External API Key Model."""

    service_name: str = Field(
        nullable=False, description="Name of the external service"
    )
    secret_id: str = Field(
        nullable=False, description="Identifier for the secret stored in SecretManager"
    )
    description: str | None = Field(default=None, description="Additional description")


class ExternalAPIKeyTable(ExternalAPIKeyBase, SQLModel, table=True):
    """External API Key table."""

    __tablename__ = EXTERNAL_API_KEY_TABLE_NAME  # type: ignore

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    user_id: UUID = Field(
        foreign_key=f"{USER_TABLE_NAME}.uuid",
        nullable=False,
        description="ID of the user",
    )

    user: "UserTable" = Relationship(back_populates="external_api_keys")
