"""Billing models."""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import Index, UniqueConstraint, text
from sqlmodel import DateTime, Field, Relationship, SQLModel

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


class SubscriptionStatus(str, Enum):
    """Subscription status enum based on Stripe's subscription statuses."""

    ACTIVE = "active"
    PAST_DUE = "past_due"
    UNPAID = "unpaid"
    CANCELED = "canceled"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    TRIALING = "trialing"
    PAUSED = "paused"


class BillingBase(SQLModel):
    """Base Billing Model."""

    stripe_customer_id: str | None = Field(nullable=True, index=True)
    stripe_subscription_id: str | None = Field(nullable=True, index=True, default=None)
    stripe_price_id: str | None = Field(nullable=True, default=None)
    subscription_status: SubscriptionStatus | None = Field(nullable=True, default=None)
    subscription_current_period_start: datetime | None = Field(
        nullable=True,
        default=None,
        sa_type=DateTime(timezone=True),  # pyright: ignore [reportArgumentType]
    )
    subscription_current_period_end: datetime | None = Field(
        nullable=True,
        default=None,
        sa_type=DateTime(timezone=True),  # pyright: ignore [reportArgumentType]
    )
    # Usage tracking
    usage_quantity: int = Field(default=0)
    last_usage_report: datetime | None = Field(
        default=None,
        nullable=True,
        sa_type=DateTime(timezone=True),  # pyright: ignore [reportArgumentType]
    )
    cancel_at_period_end: bool | None = Field(
        default=False,
        description="Whether the subscription should be canceled at the end of the period",
    )

    # Additional metadata
    metadata_: dict = Field(
        default_factory=dict, sa_column=get_json_column(), alias="metadata"
    )


class BillingTable(BillingBase, BaseOrganizationSQLModel, table=True):
    """Billing table for Stripe integration."""

    __tablename__ = BILLING_TABLE_NAME  # type: ignore
    __table_args__ = (
        UniqueConstraint("stripe_customer_id", name="uix_billing_stripe_customer_id"),
        UniqueConstraint(
            "stripe_subscription_id", name="uix_billing_stripe_subscription_id"
        ),
        Index(
            "ix_billings_organization_uuid_created_at_desc",
            "organization_uuid",
            text("created_at DESC"),
            postgresql_using="btree",
        ),
    )

    organization: "OrganizationTable" = Relationship(back_populates="billing")
