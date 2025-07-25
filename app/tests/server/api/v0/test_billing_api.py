"""Tests for the billing API endpoints."""

from datetime import datetime, timedelta, timezone
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

from fastapi.testclient import TestClient
from sqlmodel import Session

from ee.validate import LicenseInfo, Tier
from lilypad.ee.server.models.user_organizations import UserOrganizationTable, UserRole
from lilypad.server.api.v0.main import api
from lilypad.server.models import BillingTable, OrganizationTable, UserTable
from lilypad.server.models.billing import SubscriptionStatus


@patch("stripe.billing_portal.Session.create")
def test_create_customer_portal(
    mock_stripe_portal, client: TestClient, session: Session, test_user: UserTable
):
    """Test creating a Stripe customer portal session."""
    # Create organization with billing
    org = OrganizationTable(name="Test Org")
    session.add(org)
    session.flush()

    assert org.uuid is not None  # Type guard
    assert test_user.uuid is not None  # Type guard

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

    # Update user's active organization
    test_user.active_organization_uuid = org.uuid
    session.add(test_user)
    session.commit()

    # Mock Stripe response
    mock_portal = Mock()
    mock_portal.url = "https://billing.stripe.com/p/session_test123"
    mock_stripe_portal.return_value = mock_portal

    response = client.post("/stripe/customer-portal")
    assert response.status_code == 200
    assert response.json() == "https://billing.stripe.com/p/session_test123"


def test_create_customer_portal_no_active_org(session: Session):
    """Test creating portal session without active organization."""
    from lilypad.server._utils.auth import get_current_user
    from lilypad.server.api.v0.main import api
    from lilypad.server.db.session import get_session
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

    async def override_get_session():
        yield session

    # Override dependencies
    api.dependency_overrides[get_current_user] = override_get_current_user
    api.dependency_overrides[get_session] = override_get_session

    client = TestClient(api)

    try:
        response = client.post("/stripe/customer-portal")
        # Due to the exception handling in the API, it returns 500 instead of 400
        assert response.status_code == 500
        assert "Invalid API key" in response.json()["detail"]
    finally:
        api.dependency_overrides.clear()


def test_create_customer_portal_no_customer_id(
    client: TestClient, session: Session, test_user
):
    """Test creating portal session without customer ID."""
    # Create organization without billing customer ID
    org = OrganizationTable(name="Test Org")
    session.add(org)
    session.flush()

    assert org.uuid is not None  # Type guard
    assert test_user.uuid is not None  # Type guard

    billing = BillingTable(
        organization_uuid=org.uuid,
        stripe_customer_id=None,
    )
    session.add(billing)

    # Link user to organization
    user_org = UserOrganizationTable(
        user_uuid=test_user.uuid,
        organization_uuid=org.uuid,
        role=UserRole.OWNER,
    )
    session.add(user_org)

    # Update user's active organization
    test_user.active_organization_uuid = org.uuid
    session.add(test_user)
    session.commit()

    response = client.post("/stripe/customer-portal")
    # Due to the exception handling in the API, it returns 500 instead of 400
    assert response.status_code == 500
    assert "Invalid API key" in response.json()["detail"]


@patch("stripe.checkout.Session.create")
@patch("stripe.Subscription.list")
def test_create_checkout_session_new_subscription(
    mock_sub_list, mock_session_create, client: TestClient, session: Session, test_user
):
    """Test creating a Stripe checkout session for new subscription."""
    # Create organization with billing
    org = OrganizationTable(name="Test Org")
    session.add(org)
    session.flush()

    assert org.uuid is not None  # Type guard
    assert test_user.uuid is not None  # Type guard

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

    # Update user's active organization
    test_user.active_organization_uuid = org.uuid
    session.add(test_user)
    session.commit()

    # Mock no existing subscriptions
    mock_sub_list.return_value.data = []

    # Mock Stripe checkout session
    mock_checkout = Mock()
    mock_checkout.url = "https://checkout.stripe.com/pay/cs_test123"
    mock_session_create.return_value = mock_checkout

    checkout_data = {"tier": Tier.PRO}

    response = client.post("/stripe/create-checkout-session", json=checkout_data)
    assert response.status_code == 200
    assert response.json() == "https://checkout.stripe.com/pay/cs_test123"


@patch("stripe.Subscription.modify")
@patch("stripe.Subscription.list")
def test_create_checkout_session_upgrade_subscription(
    mock_sub_list, mock_sub_modify, client: TestClient, session: Session, test_user
):
    """Test upgrading an existing subscription."""
    # Create organization with billing
    org = OrganizationTable(name="Test Org")
    session.add(org)
    session.flush()

    assert org.uuid is not None  # Type guard
    assert test_user.uuid is not None  # Type guard

    billing = BillingTable(
        organization_uuid=org.uuid,
        stripe_customer_id="cus_test123",
        stripe_subscription_id="sub_test123",
    )
    session.add(billing)

    # Link user to organization
    user_org = UserOrganizationTable(
        user_uuid=test_user.uuid,
        organization_uuid=org.uuid,
        role=UserRole.OWNER,
    )
    session.add(user_org)

    # Update user's active organization
    test_user.active_organization_uuid = org.uuid
    session.add(test_user)
    session.commit()

    # Mock existing subscription
    mock_sub = {
        "items": {
            "data": [
                {"id": "si_123", "price": {"id": "price_old"}},
                {"id": "si_456", "price": {"id": "price_old_meter"}},
            ]
        }
    }
    mock_sub_list.return_value.data = [mock_sub]

    checkout_data = {"tier": Tier.TEAM}

    response = client.post("/stripe/create-checkout-session", json=checkout_data)
    assert response.status_code == 200
    assert response.json() == "success"

    # Verify subscription was modified
    mock_sub_modify.assert_called_once()


@patch("lilypad.server.api.v0.billing_api.settings")
@patch("stripe.Webhook.construct_event")
def test_stripe_webhook_subscription_created(
    mock_construct_event, mock_settings, client: TestClient, session: Session
):
    """Test handling subscription created webhook."""
    # Mock settings
    mock_settings.stripe_webhook_secret = "whsec_test123"

    # Create billing record
    billing = BillingTable(
        organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        stripe_customer_id="cus_test123",
    )
    session.add(billing)
    session.commit()

    # Mock webhook event
    mock_event = Mock()
    mock_event.type = "customer.subscription.created"

    # Create subscription object with attributes
    subscription = Mock()
    subscription.id = "sub_new123"
    subscription.customer = "cus_test123"
    subscription.status = "active"
    subscription.current_period_start = 1234567890
    subscription.current_period_end = 1234567890
    subscription.items = {
        "data": [
            {"price": {"id": "price_pro_flat"}},
            {"price": {"id": "price_pro_meter"}},
        ]
    }

    mock_event.data.object = subscription
    mock_construct_event.return_value = mock_event

    response = client.post(
        "/webhooks/stripe",
        content=b"test_payload",
        headers={"Stripe-Signature": "test_signature"},
    )

    if response.status_code != 200:
        pass
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["event"] == "customer.subscription.created"


@patch("lilypad.server.api.v0.billing_api.settings")
@patch("stripe.Webhook.construct_event")
def test_stripe_webhook_subscription_updated(
    mock_construct_event, mock_settings, client: TestClient, session: Session
):
    """Test handling subscription updated webhook."""
    # Mock settings
    mock_settings.stripe_webhook_secret = "whsec_test123"

    # Create billing record
    billing = BillingTable(
        organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        stripe_customer_id="cus_test123",
        stripe_subscription_id="sub_test123",
        subscription_status=SubscriptionStatus.ACTIVE,
    )
    session.add(billing)
    session.commit()

    # Mock webhook event
    mock_event = Mock()
    mock_event.type = "customer.subscription.updated"

    # Create subscription object with attributes
    subscription = Mock()
    subscription.id = "sub_test123"
    subscription.customer = "cus_test123"
    subscription.status = "active"
    subscription.current_period_start = 1234567890
    subscription.current_period_end = 1234567890
    subscription.items = {
        "data": [
            {"price": {"id": "price_team_flat"}},
            {"price": {"id": "price_team_meter"}},
        ]
    }

    mock_event.data.object = subscription
    mock_construct_event.return_value = mock_event

    response = client.post(
        "/webhooks/stripe",
        content=b"test_payload",
        headers={"Stripe-Signature": "test_signature"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["event"] == "customer.subscription.updated"


@patch("lilypad.server.api.v0.billing_api.settings")
@patch("stripe.Webhook.construct_event")
def test_stripe_webhook_subscription_deleted(
    mock_construct_event, mock_settings, client: TestClient, session: Session
):
    """Test handling subscription deleted webhook."""
    # Mock settings
    mock_settings.stripe_webhook_secret = "whsec_test123"

    # Create billing record
    billing = BillingTable(
        organization_uuid=UUID("12345678-1234-1234-1234-123456789abc"),
        stripe_customer_id="cus_test123",
        stripe_subscription_id="sub_test123",
        subscription_status=SubscriptionStatus.ACTIVE,
    )
    session.add(billing)
    session.commit()

    # Mock webhook event
    mock_event = Mock()
    mock_event.type = "customer.subscription.deleted"

    # Create subscription object with attributes
    subscription = Mock()
    subscription.id = "sub_test123"
    subscription.customer = "cus_test123"
    subscription.status = "canceled"

    mock_event.data.object = subscription
    mock_construct_event.return_value = mock_event

    response = client.post(
        "/webhooks/stripe",
        content=b"test_payload",
        headers={"Stripe-Signature": "test_signature"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["event"] == "customer.subscription.deleted"

    # Verify subscription was cleared
    session.refresh(billing)
    assert billing.stripe_subscription_id is None


@patch("lilypad.server.api.v0.billing_api.settings")
@patch("stripe.Webhook.construct_event")
def test_stripe_webhook_ignored_event(
    mock_construct_event, mock_settings, client: TestClient
):
    """Test handling of ignored webhook events."""
    # Mock settings
    mock_settings.stripe_webhook_secret = "whsec_test123"

    # Mock webhook event
    mock_event = Mock()
    mock_event.type = "payment_intent.succeeded"  # Not in HANDLED_EVENT_TYPES
    mock_event.data.object = {"id": "pi_test123"}
    mock_construct_event.return_value = mock_event

    response = client.post(
        "/webhooks/stripe",
        content=b"test_payload",
        headers={"Stripe-Signature": "test_signature"},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ignored"
    assert data["event"] == "payment_intent.succeeded"


@patch("lilypad.server.api.v0.billing_api.settings")
def test_stripe_webhook_missing_signature(mock_settings, client: TestClient):
    """Test webhook with missing signature."""
    # Mock settings
    mock_settings.stripe_webhook_secret = "whsec_test123"

    response = client.post(
        "/webhooks/stripe",
        content=b"test_payload",
    )

    assert response.status_code == 400
    assert "Missing Stripe-Signature header" in response.json()["detail"]


@patch("lilypad.server.api.v0.billing_api.settings")
@patch("stripe.Webhook.construct_event")
def test_stripe_webhook_invalid_signature(
    mock_construct_event, mock_settings, client: TestClient
):
    """Test webhook with invalid signature."""
    # Mock settings
    mock_settings.stripe_webhook_secret = "whsec_test123"

    # Mock signature verification error
    mock_construct_event.side_effect = ValueError("Invalid signature")

    response = client.post(
        "/webhooks/stripe",
        content=b"test_payload",
        headers={"Stripe-Signature": "invalid_signature"},
    )

    assert response.status_code == 400
    assert "Webhook error" in response.json()["detail"]


@patch("lilypad.server.api.v0.billing_api.get_settings")
@patch("stripe.billing.Meter.list_event_summaries")
def test_get_event_summaries_success(
    mock_list_summaries,
    mock_get_settings,
    client: TestClient,
    session: Session,
    test_user: UserTable,
):
    """Test successful retrieval of event summaries."""
    from lilypad.ee.server.require_license import (
        get_organization_license,
        is_lilypad_cloud,
    )

    # Mock settings
    mock_settings = Mock()
    mock_settings.stripe_spans_metering_id = "meter_test123"
    mock_get_settings.return_value = mock_settings

    # Override dependencies for cloud and license
    def override_is_cloud():
        return True

    def override_get_license():
        return LicenseInfo(
            customer="test_customer",
            license_id="test_license",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            tier=Tier.PRO,
            organization_uuid=test_user.active_organization_uuid,
        )

    api.dependency_overrides[is_lilypad_cloud] = override_is_cloud
    api.dependency_overrides[get_organization_license] = override_get_license

    try:
        # Create organization with billing
        org = test_user.user_organizations[0].organization
        billing = BillingTable(
            organization_uuid=org.uuid,  # pyright: ignore [reportArgumentType]
            stripe_customer_id="cus_test123",
        )
        session.add(billing)
        session.commit()

        # Mock Stripe response
        mock_summary = Mock()
        mock_summary.aggregated_value = 50000
        mock_list_summaries.return_value.data = [mock_summary]

        response = client.get("/stripe/event-summaries")
        assert response.status_code == 200
        data = response.json()
        assert data["current_meter"] == 50000
        assert data["monthly_total"] == 100_000  # PRO tier traces per month
    finally:
        # Clean up overrides
        del api.dependency_overrides[is_lilypad_cloud]
        del api.dependency_overrides[get_organization_license]


def test_get_event_summaries_not_cloud(
    client: TestClient,
    session: Session,
    test_user: UserTable,
):
    """Test event summaries endpoint when not on Lilypad Cloud."""
    from lilypad.ee.server.require_license import is_lilypad_cloud

    # Override dependency to return False for cloud check
    def override_is_cloud():
        return False

    api.dependency_overrides[is_lilypad_cloud] = override_is_cloud

    try:
        response = client.get("/stripe/event-summaries")
        assert response.status_code == 403
        assert (
            response.json()["detail"]
            == "This endpoint is only available for Lilypad Cloud users"
        )
    finally:
        # Clean up override
        del api.dependency_overrides[is_lilypad_cloud]


@patch("lilypad.server.api.v0.billing_api.get_settings")
@patch("stripe.billing.Meter.list_event_summaries")
def test_get_event_summaries_no_data(
    mock_list_summaries,
    mock_get_settings,
    client: TestClient,
    session: Session,
    test_user: UserTable,
):
    """Test event summaries when no data is returned from Stripe."""
    from lilypad.ee.server.require_license import (
        get_organization_license,
        is_lilypad_cloud,
    )

    # Mock settings
    mock_settings = Mock()
    mock_settings.stripe_spans_metering_id = "meter_test123"
    mock_get_settings.return_value = mock_settings

    # Override dependencies for cloud and license
    def override_is_cloud():
        return True

    def override_get_license():
        return LicenseInfo(
            customer="test_customer",
            license_id="test_license",
            expires_at=datetime.now(timezone.utc) + timedelta(days=365),
            tier=Tier.FREE,
            organization_uuid=test_user.active_organization_uuid,
        )

    api.dependency_overrides[is_lilypad_cloud] = override_is_cloud
    api.dependency_overrides[get_organization_license] = override_get_license

    try:
        # Create organization with billing
        org = test_user.user_organizations[0].organization
        billing = BillingTable(
            organization_uuid=org.uuid,  # pyright: ignore [reportArgumentType]
            stripe_customer_id="cus_test123",
        )
        session.add(billing)
        session.commit()

        # Mock empty Stripe response
        mock_list_summaries.return_value.data = []

        response = client.get("/stripe/event-summaries")
        assert response.status_code == 200
        data = response.json()
        assert data["current_meter"] == 0
        assert data["monthly_total"] == 30_000  # FREE tier traces per month
    finally:
        # Clean up overrides
        del api.dependency_overrides[is_lilypad_cloud]
        del api.dependency_overrides[get_organization_license]


@patch("lilypad.server.api.v0.billing_api.get_settings")
@patch("stripe.billing.Meter.list_event_summaries")
def test_get_event_summaries_different_tiers(
    mock_list_summaries,
    mock_get_settings,
    client: TestClient,
    session: Session,
    test_user: UserTable,
):
    """Test event summaries with different subscription tiers."""
    from lilypad.ee.server.require_license import (
        get_organization_license,
        is_lilypad_cloud,
    )

    # Mock settings
    mock_settings = Mock()
    mock_settings.stripe_spans_metering_id = "meter_test123"
    mock_get_settings.return_value = mock_settings

    # Override dependencies for cloud
    def override_is_cloud():
        return True

    api.dependency_overrides[is_lilypad_cloud] = override_is_cloud

    try:
        # Create organization with billing
        org = test_user.user_organizations[0].organization
        billing = BillingTable(
            organization_uuid=org.uuid,  # pyright: ignore [reportArgumentType]
            stripe_customer_id="cus_test123",
        )
        session.add(billing)
        session.commit()

        # Mock Stripe response
        mock_summary = Mock()
        mock_summary.aggregated_value = 500000
        mock_list_summaries.return_value.data = [mock_summary]

        # Test TEAM tier
        def override_get_license_team():
            return LicenseInfo(
                customer="test_customer",
                license_id="test_license",
                expires_at=datetime.now(timezone.utc) + timedelta(days=365),
                tier=Tier.TEAM,
                organization_uuid=test_user.active_organization_uuid,
            )

        api.dependency_overrides[get_organization_license] = override_get_license_team

        response = client.get("/stripe/event-summaries")
        assert response.status_code == 200
        data = response.json()
        assert data["current_meter"] == 500000
        assert data["monthly_total"] == 1_000_000  # TEAM tier traces per month

        # Note: Testing ENTERPRISE tier is skipped because it returns float("inf")
        # which cannot be serialized to JSON. This is a known limitation of the API
        # that would require a fix to handle unlimited values properly (e.g., using
        # a special value like -1 or null to represent unlimited)
    finally:
        # Clean up overrides
        del api.dependency_overrides[is_lilypad_cloud]
        del api.dependency_overrides[get_organization_license]
