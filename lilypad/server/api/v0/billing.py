"""Billing API for handling Stripe subscriptions and payments."""

import logging
from typing import Annotated, Any

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status

from lilypad.server._utils import get_current_user
from lilypad.server.models.organizations import SubscriptionPlan
from lilypad.server.schemas.billing import (
    SetupIntentCreate,
    SubscriptionCreate,
    SubscriptionInfo,
    WebhookResponse,
)
from lilypad.server.schemas.users import UserPublic
from lilypad.server.services import OrganizationService
from lilypad.server.settings import get_settings

logger = logging.getLogger(__name__)
router = APIRouter()

settings = get_settings()
stripe.api_key = settings.stripe_api_key


@router.post("/setup-intent")
async def create_setup_intent(
    user: Annotated[UserPublic, Depends(get_current_user)],
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
) -> SetupIntentCreate:
    """Create a SetupIntent for the user's organization"""
    if not user.active_organization_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an active organization",
        )

    organization = organization_service.find_record_by_uuid(
        user.active_organization_uuid
    )
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    # Create or retrieve Stripe customer
    if organization.stripe_customer_id:
        customer_id = organization.stripe_customer_id
    else:
        customer = stripe.Customer.create(
            email=user.email,
            name=organization.name,
            metadata={"organization_uuid": str(organization.uuid)},
        )
        customer_id = customer.id
        # Update organization with Stripe customer ID
        organization_service.update_record(
            organization.uuid, {"stripe_customer_id": customer_id}
        )

    # Create SetupIntent
    intent = stripe.SetupIntent.create(
        customer=customer_id,
        payment_method_types=["card"],
    )
    return SetupIntentCreate(client_secret=intent.client_secret)


@router.post("/subscribe")
async def create_subscription(
    plan: SubscriptionPlan,
    pm_id: str,
    user: Annotated[UserPublic, Depends(get_current_user)],
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
) -> SubscriptionCreate:
    """Create a subscription for the user's organization"""
    if not user.active_organization_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an active organization",
        )

    organization = organization_service.find_record_by_uuid(
        user.active_organization_uuid
    )
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    if not organization.stripe_customer_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Organization does not have a Stripe customer ID",
        )

    # Map plan to price ID
    price_map = {
        SubscriptionPlan.FREE: settings.stripe_cloud_free_price_id,
        SubscriptionPlan.PRO: settings.stripe_cloud_pro_price_id,
        SubscriptionPlan.TEAM: settings.stripe_cloud_team_price_id,
        SubscriptionPlan.ENTERPRISE: None,  # Enterprise requires custom pricing
    }

    price_id = price_map.get(plan)
    if not price_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid plan or plan requires custom pricing: {plan}",
        )

    if organization.stripe_subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(
                organization.stripe_subscription_id
            )
            if subscription.status not in ["canceled", "incomplete_expired"]:
                stripe.Subscription.modify(
                    organization.stripe_subscription_id,
                    items=[
                        {
                            "id": subscription["items"]["data"][0].id,
                            "price": price_id,
                        }
                    ],
                    default_payment_method=pm_id,
                )
                return SubscriptionCreate(
                    subscriptionId=organization.stripe_subscription_id,
                    status=subscription.status,
                )
        except stripe.error.StripeError as e:
            logger.error(f"Error retrieving subscription: {str(e)}")

    try:
        subscription = stripe.Subscription.create(
            customer=organization.stripe_customer_id,
            items=[{"price": price_id}],
            default_payment_method=pm_id,
            expand=["latest_invoice.payment_intent"],
            metadata={"organization_uuid": str(organization.uuid)},
        )

        # Update organization with subscription info
        organization_service.update_record(
            organization.uuid,
            {
                "stripe_subscription_id": subscription.id,
                "subscription_plan": plan,
                "subscription_status": subscription.status,
                "subscription_current_period_end": subscription.current_period_end,
            },
        )

        return SubscriptionCreate(
            subscriptionId=subscription.id,
            status=subscription.status,
            clientSecret=subscription.latest_invoice.payment_intent.client_secret
            if subscription.latest_invoice.payment_intent
            else None,
        )
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating subscription: {str(e)}",
        )


@router.get("/subscription")
async def get_subscription(
    user: Annotated[UserPublic, Depends(get_current_user)],
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
) -> SubscriptionInfo:
    """Get the current subscription for the user's organization"""
    if not user.active_organization_uuid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User does not have an active organization",
        )

    organization = organization_service.find_record_by_uuid(
        user.active_organization_uuid
    )
    if not organization:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Organization not found",
        )

    if not organization.stripe_subscription_id:
        return SubscriptionInfo(
            plan=organization.subscription_plan, status="none", current_period_end=None
        )

    try:
        subscription = stripe.Subscription.retrieve(organization.stripe_subscription_id)
        return SubscriptionInfo(
            plan=organization.subscription_plan,
            status=subscription.status,
            current_period_end=subscription.current_period_end,
        )
    except stripe.error.StripeError as e:
        logger.error(f"Error retrieving subscription: {str(e)}")
        return SubscriptionInfo(
            plan=organization.subscription_plan,
            status=organization.subscription_status,
            current_period_end=organization.subscription_current_period_end,
        )


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    organization_service: Annotated[OrganizationService, Depends(OrganizationService)],
) -> WebhookResponse:
    """Handle Stripe webhook events"""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header or not settings.stripe_webhook_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing stripe-signature header or webhook secret",
        )

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid payload: {str(e)}",
        )
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid signature: {str(e)}",
        )

    # Handle the event
    if event["type"] == "customer.subscription.created":
        await handle_subscription_created(event.data.object, organization_service)
    elif event["type"] == "customer.subscription.updated":
        await handle_subscription_updated(event.data.object, organization_service)
    elif event["type"] == "customer.subscription.deleted":
        await handle_subscription_deleted(event.data.object, organization_service)
    elif event["type"] == "invoice.payment_succeeded":
        await handle_payment_succeeded(event.data.object, organization_service)
    elif event["type"] == "invoice.payment_failed":
        await handle_payment_failed(event.data.object, organization_service)

    return WebhookResponse(status="success")


async def handle_subscription_created(
    subscription: Any, organization_service: OrganizationService
) -> None:
    """Handle subscription created event"""
    customer_id = subscription.customer
    organizations = organization_service.find_records_by_filter(
        {"stripe_customer_id": customer_id}
    )

    if not organizations:
        logger.error(f"No organization found for customer {customer_id}")
        return

    organization = organizations[0]

    # Get the plan from the price ID
    price_id = subscription.items.data[0].price.id
    plan = get_plan_from_price_id(price_id)

    organization_service.update_record(
        organization.uuid,
        {
            "stripe_subscription_id": subscription.id,
            "subscription_plan": plan,
            "subscription_status": subscription.status,
            "subscription_current_period_end": subscription.current_period_end,
        },
    )


async def handle_subscription_updated(
    subscription: Any, organization_service: OrganizationService
) -> None:
    """Handle subscription updated event"""
    customer_id = subscription.customer
    organizations = organization_service.find_records_by_filter(
        {"stripe_customer_id": customer_id}
    )

    if not organizations:
        logger.error(f"No organization found for customer {customer_id}")
        return

    organization = organizations[0]

    price_id = subscription.items.data[0].price.id
    plan = get_plan_from_price_id(price_id)

    organization_service.update_record(
        organization.uuid,
        {
            "subscription_plan": plan,
            "subscription_status": subscription.status,
            "subscription_current_period_end": subscription.current_period_end,
        },
    )


async def handle_subscription_deleted(
    subscription: Any, organization_service: OrganizationService
) -> None:
    """Handle subscription deleted event"""
    customer_id = subscription.customer
    organizations = organization_service.find_records_by_filter(
        {"stripe_customer_id": customer_id}
    )

    if not organizations:
        logger.error(f"No organization found for customer {customer_id}")
        return

    organization = organizations[0]

    organization_service.update_record(
        organization.uuid,
        {
            "subscription_plan": SubscriptionPlan.FREE,
            "subscription_status": "canceled",
            "subscription_current_period_end": subscription.current_period_end,
        },
    )


async def handle_payment_succeeded(
    invoice: Any, organization_service: OrganizationService
) -> None:
    """Handle payment succeeded event"""
    if not invoice.subscription:
        return

    subscription = stripe.Subscription.retrieve(invoice.subscription)
    customer_id = subscription.customer
    organizations = organization_service.find_records_by_filter(
        {"stripe_customer_id": customer_id}
    )

    if not organizations:
        logger.error(f"No organization found for customer {customer_id}")
        return

    organization = organizations[0]

    organization_service.update_record(
        organization.uuid,
        {
            "subscription_status": subscription.status,
            "subscription_current_period_end": subscription.current_period_end,
        },
    )


async def handle_payment_failed(
    invoice: Any, organization_service: OrganizationService
) -> None:
    """Handle payment failed event"""
    if not invoice.subscription:
        return

    subscription = stripe.Subscription.retrieve(invoice.subscription)
    customer_id = subscription.customer
    organizations = organization_service.find_records_by_filter(
        {"stripe_customer_id": customer_id}
    )

    if not organizations:
        logger.error(f"No organization found for customer {customer_id}")
        return

    organization = organizations[0]

    organization_service.update_record(
        organization.uuid, {"subscription_status": subscription.status}
    )


def get_plan_from_price_id(price_id: str) -> SubscriptionPlan:
    """Get the plan from the price ID"""
    settings = get_settings()

    if price_id == settings.stripe_cloud_free_price_id:
        return SubscriptionPlan.FREE
    elif price_id == settings.stripe_cloud_pro_price_id:
        return SubscriptionPlan.PRO
    elif price_id == settings.stripe_cloud_team_price_id:
        return SubscriptionPlan.TEAM
    else:
        return SubscriptionPlan.FREE  # Default to FREE if price ID is not recognized
