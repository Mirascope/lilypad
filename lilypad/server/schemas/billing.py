"""Billing schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field
from sqlmodel import SQLModel

from ..models.billing import SubscriptionStatus


class BillingBase(SQLModel):
    """Base schema for billing operations."""

    stripe_customer_id: str | None = None
    stripe_subscription_id: str | None = None
    stripe_price_id: str | None = None
    subscription_status: SubscriptionStatus | None = None
    subscription_current_period_start: datetime | None = None
    subscription_current_period_end: datetime | None = None
    usage_quantity: int = 0
    last_usage_report: datetime | None = None
    metadata_: dict = Field(default_factory=dict)


class BillingCreate(BillingBase):
    """Schema for creating a new billing record."""

    pass


class BillingUpdate(BillingBase):
    """Schema for updating a billing record."""

    pass


class BillingPublic(BillingBase):
    """Schema for public billing information."""

    uuid: UUID
    organization_uuid: UUID
    created_at: datetime


class StripeWebhookResponse(BaseModel):
    """Response schema for Stripe webhook events."""

    status: Literal["success", "error", "ignored"]
    event: str | None = None
    message: str | None = None
