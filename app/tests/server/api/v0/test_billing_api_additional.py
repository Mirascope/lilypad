"""Additional tests for billing API to improve coverage."""

from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session

from ee.validate import LicenseInfo, Tier
from lilypad.ee.server.models.user_organizations import UserOrganizationTable, UserRole
from lilypad.server.models import BillingTable, OrganizationTable


class TestCreateCheckoutSessionAdditional:
    """Test additional cases for create_checkout_session."""

    def test_create_checkout_session_no_active_org(self, session: Session):
        """Test checkout session creation without active organization."""
        from lilypad.server._utils.auth import get_current_user
        from lilypad.server.api.v0.main import api
        from lilypad.server.db.session import get_session
        from lilypad.server.schemas.users import UserPublic

        # Create user without active organization
        user_without_org = UserPublic(
            uuid=uuid4(),
            email="no-org@test.com",
            first_name="No Org User",
            active_organization_uuid=None,  # No active org
        )

        def override_get_current_user():
            return user_without_org

        async def override_get_session():
            yield session

        api.dependency_overrides[get_current_user] = override_get_current_user
        api.dependency_overrides[get_session] = override_get_session

        client = TestClient(api)

        try:
            checkout_data = {"tier": Tier.PRO}
            response = client.post(
                "/stripe/create-checkout-session", json=checkout_data
            )
            # Due to exception handling, returns 500
            assert response.status_code == 500
            assert "Error creating portal session" in response.json()["detail"]
        finally:
            api.dependency_overrides.clear()

    def test_create_checkout_session_no_customer_id(
        self, client: TestClient, session: Session, test_user
    ):
        """Test checkout session creation without customer ID."""
        # Create organization without billing customer ID
        org = OrganizationTable(name="Test Org")
        session.add(org)
        session.flush()

        assert org.uuid is not None
        assert test_user.uuid is not None

        billing = BillingTable(
            organization_uuid=org.uuid,
            stripe_customer_id=None,  # No customer ID
        )
        session.add(billing)

        # Link user to organization
        user_org = UserOrganizationTable(
            user_uuid=test_user.uuid,
            organization_uuid=org.uuid,
            role=UserRole.OWNER,
        )
        session.add(user_org)

        test_user.active_organization_uuid = org.uuid
        session.add(test_user)
        session.commit()

        checkout_data = {"tier": Tier.PRO}
        response = client.post("/stripe/create-checkout-session", json=checkout_data)
        # Due to exception handling, returns 500
        assert response.status_code == 500
        assert "Error creating portal session" in response.json()["detail"]

    @patch("stripe.Subscription.modify")
    @patch("stripe.Subscription.list")
    def test_create_checkout_session_no_subscription_id(
        self,
        mock_sub_list,
        mock_sub_modify,
        client: TestClient,
        session: Session,
        test_user,
    ):
        """Test upgrade path when subscription ID is missing."""
        # Create organization with billing but no subscription ID
        org = OrganizationTable(name="Test Org")
        session.add(org)
        session.flush()

        assert org.uuid is not None
        assert test_user.uuid is not None

        billing = BillingTable(
            organization_uuid=org.uuid,
            stripe_customer_id="cus_test123",
            stripe_subscription_id=None,  # No subscription ID
        )
        session.add(billing)

        # Link user to organization
        user_org = UserOrganizationTable(
            user_uuid=test_user.uuid,
            organization_uuid=org.uuid,
            role=UserRole.OWNER,
        )
        session.add(user_org)

        test_user.active_organization_uuid = org.uuid
        session.add(test_user)
        session.commit()

        # Mock existing subscription (triggers upgrade path)
        mock_sub = {
            "items": {
                "data": [
                    {"id": "si_123", "price": {"id": "price_old"}},
                ]
            }
        }
        mock_sub_list.return_value.data = [mock_sub]

        checkout_data = {"tier": Tier.TEAM}
        response = client.post("/stripe/create-checkout-session", json=checkout_data)
        # Due to exception handling, returns 500
        assert response.status_code == 500
        assert "Error creating portal session" in response.json()["detail"]

    @patch("stripe.checkout.Session.create")
    @patch("stripe.Subscription.list")
    def test_create_checkout_session_no_url(
        self,
        mock_sub_list,
        mock_session_create,
        client: TestClient,
        session: Session,
        test_user,
    ):
        """Test checkout session creation when Stripe returns no URL."""
        # Create organization with billing
        org = OrganizationTable(name="Test Org")
        session.add(org)
        session.flush()

        assert org.uuid is not None
        assert test_user.uuid is not None

        billing = BillingTable(
            organization_uuid=org.uuid,
            stripe_customer_id="cus_test123",
        )
        session.add(billing)

        # Link user to organization
        user_org = UserOrganizationTable(
            user_uuid=test_user.uuid,
            organization_uuid=org.uuid,
            role=UserRole.OWNER,
        )
        session.add(user_org)

        test_user.active_organization_uuid = org.uuid
        session.add(test_user)
        session.commit()

        # Mock no existing subscriptions
        mock_sub_list.return_value.data = []

        # Mock Stripe checkout session with no URL
        mock_checkout = Mock()
        mock_checkout.url = None  # No URL returned
        mock_session_create.return_value = mock_checkout

        checkout_data = {"tier": Tier.PRO}
        response = client.post("/stripe/create-checkout-session", json=checkout_data)
        # Due to exception handling, returns 500
        assert response.status_code == 500
        assert "Error creating portal session" in response.json()["detail"]


class TestGetEventSummaries:
    """Test get_event_summaries endpoint."""

    @patch("lilypad.server.api.v0.billing_api.is_lilypad_cloud")
    @patch("lilypad.server.api.v0.billing_api.get_organization_license")
    def test_get_event_summaries_not_cloud(
        self, mock_get_license, mock_is_cloud, client: TestClient
    ):
        """Test event summaries when not on Lilypad Cloud."""
        # Mock not being on Lilypad Cloud
        mock_is_cloud.return_value = False
        mock_license = LicenseInfo(
            customer="Test Customer",
            license_id="test-123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            tier=Tier.ENTERPRISE,
            organization_uuid=uuid4(),
        )
        mock_get_license.return_value = mock_license

        response = client.get("/stripe/event-summaries")
        assert response.status_code == 403
        assert "only available for Lilypad Cloud users" in response.json()["detail"]

    @patch("lilypad.server.api.v0.billing_api.is_lilypad_cloud")
    @patch("lilypad.server.api.v0.billing_api.get_organization_license")
    def test_get_event_summaries_no_active_org(
        self, mock_get_license, mock_is_cloud, session: Session
    ):
        """Test event summaries without active organization."""
        from datetime import datetime, timedelta, timezone

        from lilypad.server._utils.auth import get_current_user
        from lilypad.server.api.v0.main import api
        from lilypad.server.db.session import get_session
        from lilypad.server.schemas.users import UserPublic

        # Mock being on Lilypad Cloud
        mock_is_cloud.return_value = True
        mock_license = LicenseInfo(
            customer="Test Customer",
            license_id="test-123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            tier=Tier.ENTERPRISE,
            organization_uuid=uuid4(),
        )
        mock_get_license.return_value = mock_license

        # Create user without active organization
        user_without_org = UserPublic(
            uuid=uuid4(),
            email="no-org@test.com",
            first_name="No Org User",
            active_organization_uuid=None,  # No active org
        )

        def override_get_current_user():
            return user_without_org

        async def override_get_session():
            yield session

        def override_get_license():
            return mock_license

        def override_is_cloud():
            return True

        api.dependency_overrides[get_current_user] = override_get_current_user
        api.dependency_overrides[get_session] = override_get_session
        api.dependency_overrides[mock_get_license] = override_get_license
        api.dependency_overrides[mock_is_cloud] = override_is_cloud

        client = TestClient(api)

        try:
            response = client.get("/stripe/event-summaries")
            assert response.status_code == 400
            assert "does not have an active organization" in response.json()["detail"]
        finally:
            api.dependency_overrides.clear()

    @patch("stripe.billing.Meter.list_event_summaries")
    @patch("lilypad.server.api.v0.billing_api.is_lilypad_cloud")
    @patch("lilypad.server.api.v0.billing_api.get_organization_license")
    def test_get_event_summaries_no_customer_id(
        self,
        mock_get_license,
        mock_is_cloud,
        mock_stripe_summaries,
        client: TestClient,
        session: Session,
        test_user,
    ):
        """Test event summaries without customer ID."""
        from datetime import datetime, timedelta, timezone

        # Mock being on Lilypad Cloud
        mock_is_cloud.return_value = True
        mock_license = LicenseInfo(
            customer="Test Customer",
            license_id="test-123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            tier=Tier.PRO,
            organization_uuid=uuid4(),
        )
        mock_get_license.return_value = mock_license

        # Create organization without customer ID
        org = OrganizationTable(name="Test Org")
        session.add(org)
        session.flush()

        assert org.uuid is not None
        assert test_user.uuid is not None

        billing = BillingTable(
            organization_uuid=org.uuid,
            stripe_customer_id=None,  # No customer ID
        )
        session.add(billing)

        # Link user to organization
        user_org = UserOrganizationTable(
            user_uuid=test_user.uuid,
            organization_uuid=org.uuid,
            role=UserRole.OWNER,
        )
        session.add(user_org)

        test_user.active_organization_uuid = org.uuid
        session.add(test_user)
        session.commit()

        response = client.get("/stripe/event-summaries")
        assert response.status_code == 400
        assert "Customer ID not found" in response.json()["detail"]

    @patch("lilypad.server.api.v0.billing_api.get_settings")
    @patch("stripe.billing.Meter.list_event_summaries")
    @patch("lilypad.server.api.v0.billing_api.is_lilypad_cloud")
    @patch("lilypad.server.api.v0.billing_api.get_organization_license")
    def test_get_event_summaries_no_metering_id(
        self,
        mock_get_license,
        mock_is_cloud,
        mock_stripe_summaries,
        mock_get_settings,
        client: TestClient,
        session: Session,
        test_user,
    ):
        """Test event summaries without metering ID configured."""
        from datetime import datetime, timedelta, timezone

        # Mock being on Lilypad Cloud
        mock_is_cloud.return_value = True
        mock_license = LicenseInfo(
            customer="Test Customer",
            license_id="test-123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            tier=Tier.PRO,
            organization_uuid=uuid4(),
        )
        mock_get_license.return_value = mock_license

        # Mock settings without metering ID
        mock_settings = Mock()
        mock_settings.stripe_spans_metering_id = None  # No metering ID
        mock_get_settings.return_value = mock_settings

        # Create organization with customer ID
        org = OrganizationTable(name="Test Org")
        session.add(org)
        session.flush()

        assert org.uuid is not None
        assert test_user.uuid is not None

        billing = BillingTable(
            organization_uuid=org.uuid,
            stripe_customer_id="cus_test123",
        )
        session.add(billing)

        # Link user to organization
        user_org = UserOrganizationTable(
            user_uuid=test_user.uuid,
            organization_uuid=org.uuid,
            role=UserRole.OWNER,
        )
        session.add(user_org)

        test_user.active_organization_uuid = org.uuid
        session.add(test_user)
        session.commit()

        response = client.get("/stripe/event-summaries")
        assert response.status_code == 500
        assert "Stripe spans metering ID not configured" in response.json()["detail"]

    @patch("lilypad.server.api.v0.billing_api.cloud_features")
    @patch("stripe.billing.Meter.list_event_summaries")
    @patch("lilypad.server.api.v0.billing_api.is_lilypad_cloud")
    @patch("lilypad.server.api.v0.billing_api.get_organization_license")
    def test_get_event_summaries_success(
        self,
        mock_get_license,
        mock_is_cloud,
        mock_stripe_summaries,
        mock_cloud_features,
        client: TestClient,
        session: Session,
        test_user,
    ):
        """Test successful event summaries retrieval."""
        from datetime import datetime, timedelta, timezone

        # Mock being on Lilypad Cloud
        mock_is_cloud.return_value = True
        mock_license = LicenseInfo(
            customer="Test Customer",
            license_id="test-123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            tier=Tier.PRO,
            organization_uuid=uuid4(),
        )
        mock_get_license.return_value = mock_license

        # Mock cloud features
        mock_cloud_features.__getitem__.return_value.traces_per_month = 10000

        # Mock Stripe response
        mock_summary = Mock()
        mock_summary.aggregated_value = 1500
        mock_stripe_summaries.return_value.data = [mock_summary]

        # Create organization with customer ID
        org = OrganizationTable(name="Test Org")
        session.add(org)
        session.flush()

        assert org.uuid is not None
        assert test_user.uuid is not None

        billing = BillingTable(
            organization_uuid=org.uuid,
            stripe_customer_id="cus_test123",
        )
        session.add(billing)

        # Link user to organization
        user_org = UserOrganizationTable(
            user_uuid=test_user.uuid,
            organization_uuid=org.uuid,
            role=UserRole.OWNER,
        )
        session.add(user_org)

        test_user.active_organization_uuid = org.uuid
        session.add(test_user)
        session.commit()

        response = client.get("/stripe/event-summaries")
        assert response.status_code == 200
        data = response.json()
        assert data["current_meter"] == 1500
        assert data["monthly_total"] == 10000

    @patch("lilypad.server.api.v0.billing_api.cloud_features")
    @patch("stripe.billing.Meter.list_event_summaries")
    @patch("lilypad.server.api.v0.billing_api.is_lilypad_cloud")
    @patch("lilypad.server.api.v0.billing_api.get_organization_license")
    def test_get_event_summaries_empty_data(
        self,
        mock_get_license,
        mock_is_cloud,
        mock_stripe_summaries,
        mock_cloud_features,
        client: TestClient,
        session: Session,
        test_user,
    ):
        """Test event summaries with empty Stripe data."""
        from datetime import datetime, timedelta, timezone

        # Mock being on Lilypad Cloud
        mock_is_cloud.return_value = True
        mock_license = LicenseInfo(
            customer="Test Customer",
            license_id="test-123",
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            tier=Tier.PRO,
            organization_uuid=uuid4(),
        )
        mock_get_license.return_value = mock_license

        # Mock cloud features
        mock_cloud_features.__getitem__.return_value.traces_per_month = 10000

        # Mock empty Stripe response
        mock_stripe_summaries.return_value.data = []  # Empty data

        # Create organization with customer ID
        org = OrganizationTable(name="Test Org")
        session.add(org)
        session.flush()

        assert org.uuid is not None
        assert test_user.uuid is not None

        billing = BillingTable(
            organization_uuid=org.uuid,
            stripe_customer_id="cus_test123",
        )
        session.add(billing)

        # Link user to organization
        user_org = UserOrganizationTable(
            user_uuid=test_user.uuid,
            organization_uuid=org.uuid,
            role=UserRole.OWNER,
        )
        session.add(user_org)

        test_user.active_organization_uuid = org.uuid
        session.add(test_user)
        session.commit()

        response = client.get("/stripe/event-summaries")
        assert response.status_code == 200
        data = response.json()
        assert data["current_meter"] == 0  # Defaults to 0 for empty data
        assert data["monthly_total"] == 10000


class TestWebhookAdditional:
    """Test additional webhook scenarios."""

    @patch("lilypad.server.api.v0.billing_api.settings")
    def test_stripe_webhook_missing_secret(self, mock_settings, client: TestClient):
        """Test webhook with missing webhook secret configuration."""
        # Mock missing webhook secret
        mock_settings.stripe_webhook_secret = None

        response = client.post(
            "/webhooks/stripe",
            content=b"test_payload",
            headers={"Stripe-Signature": "test_signature"},
        )

        assert response.status_code == 500
        assert "Stripe webhook secret not configured" in response.json()["detail"]

    @patch("lilypad.server.api.v0.billing_api.BillingService")
    @patch("lilypad.server.api.v0.billing_api.settings")
    @patch("stripe.Webhook.construct_event")
    def test_stripe_webhook_billing_not_found(
        self,
        mock_construct_event,
        mock_settings,
        mock_billing_service,
        client: TestClient,
    ):
        """Test webhook when billing record is not found."""
        # Mock settings
        mock_settings.stripe_webhook_secret = "whsec_test123"

        # Mock webhook event
        mock_event = Mock()
        mock_event.type = "customer.subscription.created"
        mock_event.data.object = Mock()
        mock_construct_event.return_value = mock_event

        # Mock billing service returning None (billing not found)
        mock_billing_service.update_from_subscription.return_value = None

        response = client.post(
            "/webhooks/stripe",
            content=b"test_payload",
            headers={"Stripe-Signature": "test_signature"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "error"
        assert data["message"] == "Billing record not found"
        assert data["event"] == "customer.subscription.created"
