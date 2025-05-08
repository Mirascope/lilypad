"""Organizations models."""

from typing import TYPE_CHECKING
from enum import Enum

from sqlmodel import Field, Relationship, SQLModel

from .base_sql_model import BaseSQLModel
from .table_names import ORGANIZATION_TABLE_NAME

if TYPE_CHECKING:
    from ...ee.server.models.user_organizations import UserOrganizationTable
    from .api_keys import APIKeyTable
    from .projects import ProjectTable
    from .tags import TagTable


class SubscriptionPlan(str, Enum):
    """Subscription plan enum."""
    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class OrganizationBase(SQLModel):
    """Base Organization Model."""

    name: str = Field(nullable=False, min_length=1)


class OrganizationTable(OrganizationBase, BaseSQLModel, table=True):
    """Organization table."""

    __tablename__ = ORGANIZATION_TABLE_NAME  # type: ignore

    user_organizations: list["UserOrganizationTable"] = Relationship(
        back_populates="organization", cascade_delete=True
    )
    projects: list["ProjectTable"] = Relationship(
        back_populates="organization", cascade_delete=True
    )
    api_keys: list["APIKeyTable"] = Relationship(
        back_populates="organization", cascade_delete=True
    )
    tags: list["TagTable"] = Relationship(
        back_populates="organization", cascade_delete=True
    )
    license: str | None = Field(default=None, nullable=True)
    support_services: bool = Field(default=True, nullable=False)

    # Stripe billing fields
    stripe_customer_id: str | None = Field(default=None, nullable=True)
    stripe_subscription_id: str | None = Field(default=None, nullable=True)
    subscription_plan: SubscriptionPlan = Field(default=SubscriptionPlan.FREE, nullable=False)
    subscription_status: str | None = Field(default=None, nullable=True)
    subscription_current_period_end: int | None = Field(default=None, nullable=True)
