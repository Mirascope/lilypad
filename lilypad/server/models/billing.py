"""Billing models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlmodel import Field, Relationship, SQLModel

from . import get_json_column
from .base_organization_sql_model import BaseOrganizationSQLModel
from .table_names import BILLING_TABLE_NAME

if TYPE_CHECKING:
    from .organizations import OrganizationTable


class SubscriptionPlan(str, Enum):
    """Subscription plan enum."""

    FREE = "free"
    PRO = "pro"
    TEAM = "team"
    ENTERPRISE = "enterprise"


class BillingBase(SQLModel):
    """Base Billing Model."""

    stripe_customer_id: str | None = Field(nullable=True, index=True)
    stripe_subscription_id: str | None = Field(nullable=True)
    stripe_price_id: str | None = Field(nullable=True)
    subscription_status: str | None = Field(nullable=True)
    subscription_current_period_start: datetime | None = Field(nullable=True)
    subscription_current_period_end: datetime | None = Field(nullable=True)
    # Usage tracking
    usage_quantity: int = Field(default=0)
    last_usage_report: datetime = Field(nullable=True)

    # Additional metadata
    metadata_: dict = Field(
        default_factory=dict, sa_column=get_json_column(), alias="metadata"
    )


class BillingTable(BillingBase, BaseOrganizationSQLModel, table=True):
    """Billing table for Stripe integration."""

    __tablename__ = BILLING_TABLE_NAME  # type: ignore

    organization: "OrganizationTable" = Relationship(back_populates="billing")
