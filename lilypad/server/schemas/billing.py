"""Billing API for handling Stripe subscriptions and payments."""

from pydantic import BaseModel

from lilypad.server.models.organizations import SubscriptionPlan


class SetupIntentCreate(BaseModel):
    """SetupIntent Create Model."""

    client_secret: str


class SubscriptionCreate(BaseModel):
    """Subscription Create Model."""

    subscriptionId: str
    status: str
    clientSecret: str | None = None


class SubscriptionInfo(BaseModel):
    """Subscription Info Model."""

    plan: SubscriptionPlan
    status: str
    current_period_end: int | None = None


class WebhookResponse(BaseModel):
    """Webhook Response Model."""

    status: str
