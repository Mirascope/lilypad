"""Billing service for handling Stripe operations."""

import time
import uuid
from datetime import datetime
from uuid import UUID

import stripe
from fastapi import HTTPException, status
from sqlmodel import desc, select
from stripe import InvalidRequestError, StripeError

from ..models.billing import BillingTable
from ..models.organizations import OrganizationTable
from ..schemas.billing import BillingCreate
from ..settings import get_settings
from .base_organization import BaseOrganizationService

settings = get_settings()
stripe.api_key = settings.stripe_api_key


class _CustomerNotFound(Exception):
    """Exception raised when a Stripe customer is not found."""

    pass


class BillingService(BaseOrganizationService[BillingTable, BillingCreate]):
    """Service for handling billing operations."""

    table: type[BillingTable] = BillingTable
    create_model: type[BillingCreate] = BillingCreate

    def create_customer(self, organization: OrganizationTable, email: str) -> str:
        """Create a Stripe customer for an organization.

        Args:
            organization: The organization to create a customer for
            email: The email of the organization owner

        Returns:
            The Stripe customer ID
        """
        if not stripe.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stripe API key not configured",
            )
        stripe_cloud_free_price_id = settings.stripe_cloud_free_price_id
        if not stripe_cloud_free_price_id:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Free price ID not configured",
            )
        existing_billing = self.session.exec(
            select(BillingTable).where(
                BillingTable.organization_uuid == organization.uuid
            )
        ).first()

        if existing_billing and existing_billing.stripe_customer_id:
            return existing_billing.stripe_customer_id

        try:
            customer = stripe.Customer.create(
                email=email,
                name=organization.name,
                metadata={"organization_uuid": str(organization.uuid)},
            )
            # Create a subscription to enable metering
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{"price": stripe_cloud_free_price_id}],
            )

            # Create a billing record for this customer
            billing_data = BillingCreate(
                stripe_customer_id=customer.id,
                stripe_subscription_id=subscription.id,
                stripe_price_id=stripe_cloud_free_price_id,
            )

            if existing_billing:
                existing_billing.stripe_customer_id = customer.id
                self.session.add(existing_billing)
            else:
                self.create_record(billing_data, organization_uuid=organization.uuid)

            # Update the organization with the customer ID for backward compatibility
            if organization.billing:
                organization.billing.stripe_customer_id = customer.id
                self.session.add(organization)

            self.session.flush()

            return customer.id
        except StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating Stripe customer: {str(e)}",
            )

    def get_customer(self, customer_id: str) -> stripe.Customer | None:
        """Get a Stripe customer by ID.

        Args:
            customer_id: The Stripe customer ID

        Returns:
            The Stripe customer or None if not found
        """
        if not stripe.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stripe API key not configured",
            )

        try:
            return stripe.Customer.retrieve(customer_id)
        except InvalidRequestError:
            return None
        except StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error retrieving Stripe customer: {str(e)}",
            )

    def report_span_usage(self, organization_uuid: UUID, quantity: int = 1) -> None:
        """Report span usage to Stripe.

        Args:
            organization_uuid: The UUID of the organization
            quantity: The number of spans to report (default: 1)
        """
        if not stripe.api_key:
            # Skip reporting if Stripe is not configured
            return None

        organization = self.session.exec(
            select(OrganizationTable).where(OrganizationTable.uuid == organization_uuid)
        ).first()

        if not organization:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Organization or Stripe customer not found",
            )
        if not organization.billing or not organization.billing.stripe_customer_id:
            raise _CustomerNotFound()

        stripe.billing.MeterEvent.create(
            event_name="spans",
            payload={
                "value": str(quantity),
                "stripe_customer_id": str(organization.billing.stripe_customer_id),
            },
            identifier=str(uuid.uuid4()),
            timestamp=int(time.time()),
        )

        # Update the billing record with the usage information
        billing = self.session.exec(
            select(BillingTable)
            .where(BillingTable.organization_uuid == organization_uuid)
            .order_by(desc(BillingTable.created_at))
        ).first()

        if billing:
            billing.usage_quantity += quantity
            billing.last_usage_report = datetime.now()
            self.session.add(billing)
            self.session.flush()
            return None
        return None
