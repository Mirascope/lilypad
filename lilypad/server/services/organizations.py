"""The `OrganizationService` class for organizations."""

from typing import Any
from uuid import UUID

from sqlmodel import select

from ..models.organizations import OrganizationTable
from ..schemas.organizations import OrganizationCreate
from .base import BaseService
from .billing import BillingService


class OrganizationService(BaseService[OrganizationTable, OrganizationCreate]):
    """The service class for organizations."""

    table: type[OrganizationTable] = OrganizationTable
    create_model: type[OrganizationCreate] = OrganizationCreate

    def get_organization_license(self, organization_uuid: UUID) -> str | None:
        """Get license for an organization."""
        org = self.session.exec(
            select(self.table).where(self.table.uuid == organization_uuid)
        ).first()

        return org.license if org else None

    def create_record(
        self, data: OrganizationCreate, **kwargs: Any
    ) -> OrganizationTable:
        """Create a new organization record.

        This overrides the base method to add Stripe customer creation.

        Args:
            data: The organization data
            **kwargs: Additional keyword arguments. If 'email' is provided, a Stripe customer will be created.

        Returns:
            The created organization
        """
        # Create the organization record
        organization = super().create_record(data)

        billing_service: BillingService | None = kwargs.get("billing_service")
        if billing_service and "email" in kwargs and kwargs["email"]:
            billing_service.create_customer(organization, kwargs["email"])
        return organization

    def create_stripe_customer(
        self, billing_service: BillingService, organization_uuid: UUID, email: str
    ) -> OrganizationTable:
        """Create a Stripe customer for an organization.

        Args:
            billing_service: The billing service instance
            organization_uuid: The UUID of the organization
            email: The email of the organization owner

        Returns:
            The updated organization
        """
        organization = self.find_record_by_uuid(organization_uuid)
        if not organization:
            raise ValueError("Organization not found")

        if organization.billing.stripe_customer_id:
            return organization

        billing_service.create_customer(organization, email)
        # Note: create_customer already updates the organization record
        self.session.flush()

        return organization

    def get_stripe_customer(
        self, billing_service: BillingService, organization_uuid: UUID
    ) -> Any:
        """Get the Stripe customer for an organization.

        Args:
            billing_service: The billing service instance
            organization_uuid: The UUID of the organization

        Returns:
            The Stripe customer or None if not found
        """
        organization = self.find_record_by_uuid(organization_uuid)
        if not organization or not organization.billing.stripe_customer_id:
            return None

        return billing_service.get_customer(organization.billing.stripe_customer_id)
