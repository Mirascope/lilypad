"""The `/billing` API router for handling Stripe webhooks."""
import logging
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlmodel import Session

from ...db import get_session
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


@billing_router.post("/webhooks/stripe", response_model=StripeWebhookResponse)
async def stripe_webhook(
    request: Request,
    session: Annotated[Session, Depends(get_session)],
    stripe_signature: str | None = Header(None, alias="Stripe-Signature"),
) -> StripeWebhookResponse:
    """Handle Stripe webhook events.

    This endpoint receives webhook events from Stripe and updates the billing records.
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
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

    if event.type in HANDLED_EVENT_TYPES:
        subscription = event.data.object

        billing = BillingService.update_from_subscription(session, subscription)
        if billing is None:
            return StripeWebhookResponse(
                status="error",
                message="Billing record not found",
                event=event.type,
            )

        return StripeWebhookResponse(status="success", event=event.type)

    return StripeWebhookResponse(status="ignored", event=event.type)


__all__ = ["billing_router"]