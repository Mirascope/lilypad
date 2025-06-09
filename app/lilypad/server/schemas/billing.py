"""Billing schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel

from ..models.billing import BillingBase


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
