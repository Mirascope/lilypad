"""The `/billing` API router for handling Stripe webhooks."""
import logging
from datetime import datetime, timezone
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlmodel import select

from ...models.billing import BillingTable, SubscriptionStatus
from ...schemas.billing import StripeWebhookResponse
from ...services.billing import BillingService
from ...settings import get_settings

billing_router = APIRouter()
settings = get_settings()

logger = logging.getLogger(__name__)

HANDLED_EVENT_TYPES = {
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
}


@billing_router.post("/webhooks/stripe",  response_model=StripeWebhookResponse,)
async def stripe_webhook(
    request: Request,
    billing_service: Annotated[BillingService, Depends(BillingService)],
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
) -> StripeWebhookResponse:
    """Handle Stripe webhook events.

    This endpoint receives webhook events from Stripe and updates the billing records accordingly.
    It handles the following events:
    - customer.subscription.created
    - customer.subscription.updated
    - customer.subscription.deleted
    """
    if not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe webhook secret not configured",
        )

    if stripe_signature is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing Stripe-Signature header",
        )

    payload_bytes: bytes = await request.body()
    payload: str = payload_bytes.decode()  # Convert bytes to str

    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if event.type in HANDLED_EVENT_TYPES:
        subscription = event.data.object

        subscription_id = subscription.id
        if not subscription_id:
            return StripeWebhookResponse(status= "error", message="Missing subscription ID")

        billing = billing_service.session.exec(
            select(BillingTable).where(
                BillingTable.stripe_subscription_id == subscription_id
            )
        ).first()

        if not billing:
            customer_id = subscription.customer
            if not customer_id:
                return StripeWebhookResponse(status="error", message="Missing customer ID")

            billing = billing_service.session.exec(
                select(BillingTable).where(
                    BillingTable.stripe_customer_id == customer_id
                )
            ).first()

        if not billing:
            # No matching billing record found
            return StripeWebhookResponse(status="error", message="Billing record not found")

        billing.stripe_subscription_id = subscription_id

        customer_id = getattr(subscription, "customer", None)
        if customer_id and not billing.stripe_customer_id:
            billing.stripe_customer_id = customer_id

        if hasattr(subscription, "items") and subscription.items.data:
            first_item = subscription.items.data[0]
            price = getattr(first_item, "price", None)
            if price and hasattr(price, "id"):
                billing.stripe_price_id = price.id

        try:
            billing.subscription_status = SubscriptionStatus(subscription.status)
        except ValueError:
            logger.warning("Unknown subscription status: %s", subscription.status)

            billing.subscription_status = None

        if hasattr(subscription, "current_period_start") and subscription.current_period_start:
            billing.subscription_current_period_start = datetime.fromtimestamp(
                subscription.current_period_start, tz=timezone.utc
            )

        if hasattr(subscription, "current_period_end") and subscription.current_period_end:
            billing.subscription_current_period_end = datetime.fromtimestamp(
                subscription.current_period_end, tz=timezone.utc
            )

        try:
            billing_service.session.add(billing)
            billing_service.session.commit()
        except Exception:
            billing_service.session.rollback()
            raise

        return StripeWebhookResponse(status="success", event=event.type)

    return StripeWebhookResponse(status="ignored", event=event.type)


__all__ = ["billing_router"]
