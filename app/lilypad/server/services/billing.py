"""Billing service for handling Stripe operations."""

import logging
import time
import uuid
from datetime import datetime, timezone
from typing import Any

import stripe
from fastapi import HTTPException, status
from sqlmodel import Session, desc, select, update
from stripe import InvalidRequestError, StripeError

from ee import Tier

from ..models.billing import BillingTable, SubscriptionStatus
from ..models.organizations import OrganizationTable
from ..schemas.billing import BillingCreate
from ..settings import get_settings
from .base_organization import BaseOrganizationService

settings = get_settings()
stripe.api_key = settings.stripe_api_key
logger = logging.getLogger(__name__)


class _CustomerNotFound(Exception):
    """Exception raised when a Stripe customer is not found."""

    pass


class BillingService(BaseOrganizationService[BillingTable, BillingCreate]):
    """Service for handling billing operations."""

    table: type[BillingTable] = BillingTable
    create_model: type[BillingCreate] = BillingCreate

    def get_tier_from_billing(self, organization_uuid: uuid.UUID) -> Tier:
        """Get the tier from the billing table for an organization.

        Args:
            organization_uuid: The UUID of the organization

        Returns:
            The tier of the organization
        """
        billing = self.session.exec(
            select(self.table)
            .where(self.table.organization_uuid == organization_uuid)
            .order_by(desc(self.table.created_at))
        ).first()
        if not billing or not billing.stripe_price_id:
            return Tier.FREE

        # Determine tier based on stripe_price_id
        if billing.stripe_price_id == settings.stripe_cloud_team_flat_price_id:
            return Tier.TEAM
        elif billing.stripe_price_id == settings.stripe_cloud_pro_flat_price_id:
            return Tier.PRO
        else:
            return Tier.FREE

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

            billing_data = BillingCreate(
                stripe_customer_id=customer.id,
            )

            if existing_billing:
                existing_billing.stripe_customer_id = customer.id
                existing_billing.subscription_status = SubscriptionStatus.ACTIVE
                self.session.add(existing_billing)
            else:
                self.create_record(billing_data, organization_uuid=organization.uuid)

            # Update the organization with the customer ID for backward compatibility
            if organization.billing:
                organization.billing.stripe_customer_id = customer.id
                self.session.add(organization)

            self.session.commit()

            return customer.id
        except StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error creating Stripe customer: {str(e)}",
            )

    def delete_customer_and_billing(self, organization_uuid: uuid.UUID) -> None:
        """Delete a Stripe customer for an organization and then delete billing row.

        Args:
            organization_uuid: The UUID of the organization
        """
        if not stripe.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stripe API key not configured",
            )
        billing = self.session.exec(
            select(self.table)
            .where(self.table.organization_uuid == organization_uuid)
            .order_by(desc(self.table.created_at))
        ).first()
        if not billing or not billing.stripe_customer_id:
            raise _CustomerNotFound()

        try:
            stripe.Customer.delete(billing.stripe_customer_id)
            self.session.delete(billing)
            self.session.commit()
        except InvalidRequestError as e:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Stripe customer not found: {str(e)}",
            )
        except StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error deleting Stripe customer: {str(e)}",
            )

    def update_customer(
        self, customer_id: str, new_name: str
    ) -> stripe.Customer | None:
        """Update a Stripe customer by ID.

        Args:
            customer_id: The Stripe customer ID
            new_name: The new name for the customer

        Returns:
            The updated Stripe customer or None if not found
        """
        if not stripe.api_key:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Stripe API key not configured",
            )

        try:
            customer = stripe.Customer.modify(
                customer_id,
                name=new_name,
            )
            if not customer:
                raise _CustomerNotFound()
            return customer
        except InvalidRequestError:
            return None
        except StripeError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error updating Stripe customer: {str(e)}",
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

    def report_span_usage(
        self, organization_uuid: uuid.UUID, quantity: int = 1
    ) -> None:
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

        stripe.billing.MeterEvent.create(  # type: ignore[attr-defined]
            event_name="spans",
            payload={
                "value": str(quantity),
                "stripe_customer_id": str(organization.billing.stripe_customer_id),
            },
            identifier=str(uuid.uuid4()),
            timestamp=int(time.time()),
        )

        # First, get the billing record ID
        billing = self.session.exec(
            select(BillingTable)
            .where(BillingTable.organization_uuid == organization_uuid)
            .order_by(desc(BillingTable.created_at))
        ).first()

        if billing:
            stmt = (
                update(BillingTable)
                .where(BillingTable.uuid == billing.uuid)  # pyright: ignore[reportArgumentType]
                .values(
                    usage_quantity=BillingTable.usage_quantity + quantity,  # type: ignore[operator]
                    last_usage_report=datetime.now(timezone.utc),
                )
            )
            self.session.execute(stmt)
            self.session.commit()

        return None

    @classmethod
    def find_by_subscription_id(
        cls, session: Session, subscription_id: str
    ) -> BillingTable | None:
        """Find by subscription_id"""
        return session.exec(
            select(BillingTable).where(
                BillingTable.stripe_subscription_id == subscription_id
            )
        ).first()

    @classmethod
    def find_by_customer_id(
        cls, session: Session, customer_id: str | None
    ) -> BillingTable | None:
        """Find by customer_id"""
        if not customer_id:
            return None
        return session.exec(
            select(BillingTable).where(BillingTable.stripe_customer_id == customer_id)
        ).first()

    @classmethod
    def update_billing(
        cls,
        session: Session,
        subscription: Any,
        data: dict,
    ) -> BillingTable | None:
        """Update billing information from a Stripe subscription.

        Args:
            session: The SQLAlchemy session
            subscription: The Stripe subscription object
            data: The data to update in the billing record
        Returns:
            The updated billing record or None if not found
        """
        billing = cls.find_by_subscription_id(
            session, subscription.id
        ) or cls.find_by_customer_id(session, getattr(subscription, "customer", None))
        if billing is None:
            return None

        billing.sqlmodel_update(data)
        session.add(billing)
        session.flush()
        return billing

    @classmethod
    def update_from_subscription(
        cls,
        session: Session,
        subscription: Any,
    ) -> BillingTable | None:
        """Update billing information from a Stripe subscription."""

        def _get(obj: Any, attr: str, default: Any = None) -> Any:
            if isinstance(obj, dict):
                return obj.get(attr, default)
            return getattr(obj, attr, default)

        billing = cls.find_by_subscription_id(
            session, subscription.id
        ) or cls.find_by_customer_id(session, getattr(subscription, "customer", None))
        if billing is None:
            return None

        billing.stripe_subscription_id = subscription.id

        customer_id = getattr(subscription, "customer", None)
        if customer_id and not billing.stripe_customer_id:
            billing.stripe_customer_id = customer_id

        # status
        try:
            billing.subscription_status = SubscriptionStatus(subscription.status)
        except ValueError:
            logger.warning("Unknown subscription status: %s", subscription.status)
            billing.subscription_status = None

        # current period
        if getattr(subscription, "current_period_start", None):
            billing.subscription_current_period_start = datetime.fromtimestamp(
                subscription.current_period_start, tz=timezone.utc
            )
        if getattr(subscription, "current_period_end", None):
            billing.subscription_current_period_end = datetime.fromtimestamp(
                subscription.current_period_end, tz=timezone.utc
            )
        if getattr(subscription, "cancel_at_period_end", None):
            billing.cancel_at_period_end = True

        items_obj = _get(subscription, "items")
        data_list = _get(items_obj, "data", [])
        if data_list:
            first_item = data_list[0]
            price = _get(first_item, "price")
            price_id = _get(price, "id")
            if price_id:
                billing.stripe_price_id = price_id

        session.add(billing)
        session.commit()
        return billing
