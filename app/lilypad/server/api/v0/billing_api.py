"""The `/billing` API router for handling Stripe webhooks."""

import calendar
import logging
from datetime import datetime, timezone
from typing import Annotated

import stripe
from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel
from sqlmodel import Session
from stripe import SignatureVerificationError

from ee.validate import LicenseInfo, Tier

from ....ee.server.features import cloud_features
from ....ee.server.require_license import get_organization_license, is_lilypad_cloud
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


class StripeCheckoutSession(BaseModel):
    """Response model for Stripe checkout session creation."""

    tier: Tier


@billing_router.post("/stripe/customer-portal")
async def create_customer_portal(
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
        stripe.api_key = settings.stripe_secret_api_key
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{settings.client_url}/settings/overview",
        )

        return session.url

    except Exception:
        raise HTTPException(status_code=500, detail="Invalid API key")


@billing_router.post("/stripe/create-checkout-session", response_model=str)
def create_checkout_session(
    user: Annotated[UserPublic, Depends(get_current_user)],
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
    stripe_checkout_session: StripeCheckoutSession,
) -> str:
    try:
        settings = get_settings()
        PRICE_MAP = {
            Tier.PRO: [
                {"price": settings.stripe_cloud_pro_flat_price_id, "quantity": 1},
                {"price": settings.stripe_cloud_pro_meter_price_id},
            ],
            Tier.TEAM: [
                {"price": settings.stripe_cloud_team_flat_price_id, "quantity": 1},
                {"price": settings.stripe_cloud_team_meter_price_id},
            ],
        }

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
        stripe.api_key = settings.stripe_secret_api_key
        subscriptions = stripe.Subscription.list(customer=customer_id, status="active")
        if len(subscriptions.data) > 0:
            current_subscription = subscriptions.data[0]
            # Build the items list - delete old items and add new ones
            items = []

            # Delete existing items
            for item in current_subscription["items"]["data"]:
                items.append({"id": item["id"], "deleted": True})

            # Add new items
            items.extend(PRICE_MAP[stripe_checkout_session.tier])
            if not organization.billing.stripe_subscription_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Stripe subscription ID not found",
                )
            stripe.Subscription.modify(
                organization.billing.stripe_subscription_id,
                items=items,
            )
            return "success"
        else:
            session = stripe.checkout.Session.create(
                mode="subscription",
                customer=customer_id,
                success_url=f"{settings.client_url}/settings/overview",
                line_items=PRICE_MAP[stripe_checkout_session.tier],
            )
            if not session.url:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to create checkout session",
                )
            return session.url

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating portal session",
        )


class EventSummaryResponse(BaseModel):
    """Response model for event summaries."""

    current_meter: int | float
    monthly_total: int | float


@billing_router.get("/stripe/event-summaries", response_model=EventSummaryResponse)
def get_event_summaries(
    user: Annotated[UserPublic, Depends(get_current_user)],
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
    license: Annotated[LicenseInfo, Depends(get_organization_license)],
    is_lilypad_cloud: Annotated[bool, Depends(is_lilypad_cloud)],
) -> EventSummaryResponse:
    if not is_lilypad_cloud:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This endpoint is only available for Lilypad Cloud users",
        )
    if not user.active_organization_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an active organization",
        )
    organization = organization_service.find_record_by_uuid(
        user.active_organization_uuid
    )
    customer_id = organization.billing.stripe_customer_id
    settings = get_settings()
    now = datetime.now(timezone.utc)
    start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
    last_day = calendar.monthrange(now.year, now.month)[1]
    end_of_month = datetime(
        now.year, now.month, last_day, 23, 59, 59, tzinfo=timezone.utc
    )
    if not customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer ID not found",
        )
    if not settings.stripe_spans_metering_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Stripe spans metering ID not configured",
        )
    summaries = stripe.billing.Meter.list_event_summaries(
        settings.stripe_spans_metering_id,
        customer=customer_id,
        start_time=int(start_of_month.timestamp()),
        end_time=int(end_of_month.timestamp()),
    )

    # Get the total
    return EventSummaryResponse(
        current_meter=summaries.data[0].aggregated_value if summaries.data else 0,
        monthly_total=cloud_features[license.tier].traces_per_month,
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
    try:
        event = stripe.Webhook.construct_event(
            payload_bytes, stripe_signature, settings.stripe_webhook_secret
        )
    except (ValueError, SignatureVerificationError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Webhook error"
        )
    if event.type in HANDLED_EVENT_TYPES:
        subscription = event.data.object
        if event.type == "customer.subscription.deleted":  # Downgrade to free plan
            data = {
                "stripe_subscription_id": None,
                "subscription_current_period_start": None,
                "subscription_current_period_end": None,
            }
            billing = BillingService.update_billing(session, subscription, data)
        else:
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
