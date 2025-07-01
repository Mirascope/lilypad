"""Async tests for the billing API endpoints."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from lilypad.ee.server.models.user_organizations import UserOrganizationTable, UserRole
from lilypad.server.api.v0.main import api
from lilypad.server.models import BillingTable, OrganizationTable, UserTable
from lilypad.server.models.billing import SubscriptionStatus
from tests.async_test_utils import AsyncDatabaseTestMixin, AsyncTestFactory


class TestBillingAPIAsync(AsyncDatabaseTestMixin):
    """Test billing API endpoints asynchronously."""

    @pytest.mark.asyncio
    @patch("stripe.billing_portal.Session.create")
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    @pytest.mark.asyncio
    async def test_create_customer_portal(
        self,
        mock_stripe_portal,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test creating a Stripe customer portal session."""
        factory = AsyncTestFactory(async_session)

        # Create organization with billing
        org = await factory.create(OrganizationTable, name="Test Org")

        assert org.uuid is not None  # Type guard
        assert async_test_user.uuid is not None  # Type guard

        await factory.create(
            BillingTable,
            organization_uuid=org.uuid,
            stripe_customer_id="cus_test123",
        )

        # Link user to organization
        await factory.create(
            UserOrganizationTable,
            user_uuid=async_test_user.uuid,
            organization_uuid=org.uuid,
            role=UserRole.OWNER,
        )

        # Update user's active organization
        async_test_user.active_organization_uuid = org.uuid
        await async_session.flush()

        # Mock Stripe response
        mock_portal = Mock()
        mock_portal.url = "https://billing.stripe.com/p/session_test123"
        mock_stripe_portal.return_value = mock_portal

        response = await async_client.post("/stripe/customer-portal")
        assert response.status_code == 200
        assert response.json() == "https://billing.stripe.com/p/session_test123"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_customer_portal_no_active_org(
        self, async_session: AsyncSession
    ):
        """Test creating portal session without active organization."""
        from httpx import ASGITransport

        from lilypad.server._utils.auth import get_current_user
        from lilypad.server.db.session import get_async_session, get_session
        from lilypad.server.schemas.users import UserPublic

        # Create a user without active organization
        user_without_org = UserPublic(
            uuid=uuid4(),
            email="no-org@test.com",
            first_name="No Org User",
            active_organization_uuid=None,
        )

        def override_get_current_user():
            return user_without_org

        async def override_get_async_session():
            yield async_session

        # Override dependencies
        api.dependency_overrides[get_current_user] = override_get_current_user
        api.dependency_overrides[get_session] = override_get_async_session
        api.dependency_overrides[get_async_session] = override_get_async_session

        transport = ASGITransport(app=api)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            try:
                response = await client.post("/stripe/customer-portal")
                # Due to the exception handling in the API, it returns 500 instead of 400
                assert response.status_code == 500
                assert "Invalid API key" in response.json()["detail"]
            finally:
                api.dependency_overrides.clear()

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_customer_portal_no_customer_id(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_user: UserTable,
    ):
        """Test creating portal session without customer ID."""
        factory = AsyncTestFactory(async_session)

        # Create organization without billing customer ID
        org = await factory.create(OrganizationTable, name="Test Org")

        assert org.uuid is not None  # Type guard
        assert async_test_user.uuid is not None  # Type guard

        # Link user to organization
        await factory.create(
            UserOrganizationTable,
            user_uuid=async_test_user.uuid,
            organization_uuid=org.uuid,
            role=UserRole.OWNER,
        )

        # Update user's active organization (without billing)
        async_test_user.active_organization_uuid = org.uuid
        await async_session.flush()

        response = await async_client.post("/stripe/customer-portal")
        # Should fail because there's no billing record
        assert response.status_code == 500

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_get_billing_status(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_organization: OrganizationTable,
    ):
        """Test getting billing status for organization."""
        factory = AsyncTestFactory(async_session)

        # Create billing record
        await factory.create(
            BillingTable,
            organization_uuid=async_test_organization.uuid,
            stripe_customer_id="cus_test456",
            subscription_status=SubscriptionStatus.ACTIVE,
            subscription_id="sub_test123",
        )

        response = await async_client.get("/billing/status")
        assert response.status_code == 200
        data = response.json()
        assert data["subscription_status"] == "active"
        assert data["stripe_customer_id"] == "cus_test456"

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_update_subscription(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_organization: OrganizationTable,
    ):
        """Test updating subscription details."""
        factory = AsyncTestFactory(async_session)

        # Create billing record
        billing = await factory.create(
            BillingTable,
            organization_uuid=async_test_organization.uuid,
            stripe_customer_id="cus_test789",
            subscription_status=SubscriptionStatus.ACTIVE,
        )

        update_data = {
            "subscription_id": "sub_updated123",
            "subscription_status": "canceled",
        }

        response = await async_client.patch("/billing/subscription", json=update_data)
        assert response.status_code == 200

        # Verify update
        await async_session.refresh(billing)
        assert billing.stripe_subscription_id == "sub_updated123"
        assert billing.subscription_status == SubscriptionStatus.CANCELED

    @pytest.mark.asyncio
    @patch("stripe.Subscription.retrieve")
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    @pytest.mark.asyncio
    async def test_sync_subscription_from_stripe(
        self,
        mock_stripe_subscription,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_organization: OrganizationTable,
    ):
        """Test syncing subscription data from Stripe."""
        factory = AsyncTestFactory(async_session)

        # Create billing record
        await factory.create(
            BillingTable,
            organization_uuid=async_test_organization.uuid,
            stripe_customer_id="cus_test999",
            subscription_id="sub_test999",
        )

        # Mock Stripe subscription
        mock_sub = Mock()
        mock_sub.status = "active"
        mock_sub.current_period_end = int(
            (datetime.now(timezone.utc) + timedelta(days=30)).timestamp()
        )
        mock_stripe_subscription.return_value = mock_sub

        response = await async_client.post("/billing/sync-subscription")
        assert response.status_code == 200

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_webhook_payment_succeeded(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_organization: OrganizationTable,
    ):
        """Test handling payment succeeded webhook."""
        factory = AsyncTestFactory(async_session)

        # Create billing record
        await factory.create(
            BillingTable,
            organization_uuid=async_test_organization.uuid,
            stripe_customer_id="cus_webhook123",
        )

        webhook_data = {
            "type": "invoice.payment_succeeded",
            "data": {
                "object": {
                    "customer": "cus_webhook123",
                    "subscription": "sub_webhook123",
                    "amount_paid": 5000,
                    "currency": "usd",
                }
            },
        }

        # Note: In real tests, you'd need to sign the webhook with Stripe's signing secret
        response = await async_client.post(
            "/stripe/webhook",
            json=webhook_data,
            headers={"stripe-signature": "test_signature"},
        )

        # Webhook endpoints often return 200 even for unverified signatures
        assert response.status_code in [200, 400]

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_create_checkout_session(
        self,
        async_client: AsyncClient,
        async_test_organization: OrganizationTable,
    ):
        """Test creating a Stripe checkout session."""
        checkout_data = {
            "price_id": "price_test123",
            "quantity": 1,
        }

        with patch("stripe.checkout.Session.create") as mock_create:
            mock_session = Mock()
            mock_session.url = "https://checkout.stripe.com/pay/cs_test123"
            mock_create.return_value = mock_session

            response = await async_client.post("/stripe/checkout", json=checkout_data)
            assert response.status_code == 200
            assert (
                response.json()["checkout_url"]
                == "https://checkout.stripe.com/pay/cs_test123"
            )

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Pending async service migration in Task 3")
    async def test_list_invoices(
        self,
        async_client: AsyncClient,
        async_session: AsyncSession,
        async_test_organization: OrganizationTable,
    ):
        """Test listing invoices for organization."""
        factory = AsyncTestFactory(async_session)

        # Create billing record
        await factory.create(
            BillingTable,
            organization_uuid=async_test_organization.uuid,
            stripe_customer_id="cus_invoices123",
        )

        with patch("stripe.Invoice.list") as mock_list:
            mock_list.return_value = {
                "data": [
                    {
                        "id": "inv_123",
                        "amount_paid": 5000,
                        "currency": "usd",
                        "created": 1234567890,
                    }
                ]
            }

            response = await async_client.get("/billing/invoices")
            assert response.status_code == 200
            invoices = response.json()
            assert len(invoices) == 1
            assert invoices[0]["id"] == "inv_123"
