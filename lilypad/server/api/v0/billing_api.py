"""The `/billing` API router for handling Stripe webhooks."""

import logging
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from sqlmodel import Session
from stripe import SignatureVerificationError

from ..._utils.auth import get_current_user
from ...db import get_session
from ...schemas.billing import StripeWebhookResponse
from ...schemas.users import UserPublic
from ...services.billing import BillingService
from ...services.organizations import OrganizationService
from ...settings import get_settings

billing_router = APIRouter()
settings = get_settings()

logger = logging.getLogger(__name__)

HANDLED_EVENT_TYPES = {
    "customer.subscription.created",
    "customer.subscription.updated",
    "customer.subscription.deleted",
}


@billing_router.post("/stripe/create-customer-portal-session", response_model=str)
def create_portal_session(
    user: Annotated[UserPublic, Depends(get_current_user)],
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
) -> str:
    try:
        if not user.active_organization_uuid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User does not have an active organization",
            )
        organization = organization_service.find_record_by_uuid(
            user.active_organization_uuid
        )
        customer_id = organization.billing.stripe_customer_id
        if not customer_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer ID not found",
            )
        # Create a billing portal session
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{settings.client_url}/settings/overview",
        )

        return session.url
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating portal session: {str(e)}",
        )


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
    except (ValueError, SignatureVerificationError) as e:
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
