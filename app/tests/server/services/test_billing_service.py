"""Tests for the billing service."""

import uuid
from unittest.mock import Mock, patch

import pytest
import stripe
from fastapi import HTTPException
from sqlmodel import Session

from ee import Tier
from lilypad.server.models import OrganizationTable
from lilypad.server.models.billing import BillingTable, SubscriptionStatus
from lilypad.server.schemas.users import UserPublic
from lilypad.server.services.billing import BillingService, _CustomerNotFound


@pytest.fixture
def mock_user():
    """Create a mock user."""
    return UserPublic(
        uuid=uuid.uuid4(),
        email="test@example.com",
        first_name="Test",
        last_name="User",
        active_organization_uuid=uuid.uuid4(),
    )


@pytest.fixture
def mock_session():
    """Create a mock database session."""
    return Mock(spec=Session)


@pytest.fixture
def billing_service(mock_session, mock_user):
    """Create a billing service instance."""
    return BillingService(session=mock_session, user=mock_user)


@pytest.fixture
def sample_organization():
    """Create a sample organization."""
    org = OrganizationTable(name="Test Organization")
    org.uuid = uuid.uuid4()
    return org


def test_get_tier_from_billing_free(billing_service, mock_session):
    """Test getting FREE tier when no billing record exists."""
    org_uuid = uuid.uuid4()

    # Mock no billing record found
    mock_result = Mock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    tier = billing_service.get_tier_from_billing(org_uuid)
    assert tier == Tier.FREE


def test_get_tier_from_billing_no_price_id(billing_service, mock_session):
    """Test getting FREE tier when billing has no stripe_price_id."""
    org_uuid = uuid.uuid4()

    # Mock billing record without stripe_price_id
    mock_billing = Mock(spec=BillingTable)
    mock_billing.stripe_price_id = None

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    tier = billing_service.get_tier_from_billing(org_uuid)
    assert tier == Tier.FREE


@patch("lilypad.server.services.billing.settings")
def test_get_tier_from_billing_team(mock_settings, billing_service, mock_session):
    """Test getting TEAM tier from billing."""
    org_uuid = uuid.uuid4()
    mock_settings.stripe_cloud_team_flat_price_id = "price_team_123"
    mock_settings.stripe_cloud_pro_flat_price_id = "price_pro_123"

    # Mock billing record with team price ID
    mock_billing = Mock(spec=BillingTable)
    mock_billing.stripe_price_id = "price_team_123"

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    tier = billing_service.get_tier_from_billing(org_uuid)
    assert tier == Tier.TEAM


@patch("lilypad.server.services.billing.settings")
def test_get_tier_from_billing_pro(mock_settings, billing_service, mock_session):
    """Test getting PRO tier from billing."""
    org_uuid = uuid.uuid4()
    mock_settings.stripe_cloud_team_flat_price_id = "price_team_123"
    mock_settings.stripe_cloud_pro_flat_price_id = "price_pro_123"

    # Mock billing record with pro price ID
    mock_billing = Mock(spec=BillingTable)
    mock_billing.stripe_price_id = "price_pro_123"

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    tier = billing_service.get_tier_from_billing(org_uuid)
    assert tier == Tier.PRO


@patch("lilypad.server.services.billing.settings")
def test_get_tier_from_billing_unknown_price(
    mock_settings, billing_service, mock_session
):
    """Test getting FREE tier for unknown price ID."""
    org_uuid = uuid.uuid4()
    mock_settings.stripe_cloud_team_flat_price_id = "price_team_123"
    mock_settings.stripe_cloud_pro_flat_price_id = "price_pro_123"

    # Mock billing record with unknown price ID
    mock_billing = Mock(spec=BillingTable)
    mock_billing.stripe_price_id = "price_unknown_123"

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    tier = billing_service.get_tier_from_billing(org_uuid)
    assert tier == Tier.FREE


@patch("lilypad.server.services.billing.stripe")
def test_create_customer_success(
    mock_stripe,
    billing_service,
    mock_session,
    sample_organization,
):
    """Test successful customer creation."""
    mock_stripe.api_key = "test_key"

    # Mock no existing billing
    mock_result = Mock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    # Mock Stripe customer creation
    mock_customer = Mock()
    mock_customer.id = "cus_test123"
    mock_stripe.Customer.create.return_value = mock_customer

    # Mock billing creation
    mock_session.add = Mock()
    mock_session.commit = Mock()
    mock_session.refresh = Mock()

    # Mock create_record method
    with patch.object(billing_service, "create_record") as mock_create_record:
        mock_create_record.return_value = Mock(uuid=uuid.uuid4())

        customer_id = billing_service.create_customer(
            sample_organization, "test@example.com"
        )

        assert customer_id == "cus_test123"
        mock_stripe.Customer.create.assert_called_once_with(
            email="test@example.com",
            name="Test Organization",
            metadata={"organization_uuid": str(sample_organization.uuid)},
        )


@patch("lilypad.server.services.billing.stripe")
def test_create_customer_no_api_key(
    mock_stripe, billing_service, mock_session, sample_organization
):
    """Test customer creation fails when no API key is configured."""
    mock_stripe.api_key = None

    with pytest.raises(HTTPException) as exc_info:
        billing_service.create_customer(sample_organization, "test@example.com")

    assert exc_info.value.status_code == 500
    assert "Stripe API key not configured" in str(exc_info.value.detail)


@patch("lilypad.server.services.billing.stripe")
def test_create_customer_existing_customer(
    mock_stripe, billing_service, mock_session, sample_organization
):
    """Test create_customer returns existing customer ID."""
    mock_stripe.api_key = "test_key"

    # Mock existing billing with customer ID
    mock_billing = Mock(spec=BillingTable)
    mock_billing.stripe_customer_id = "cus_existing123"

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    customer_id = billing_service.create_customer(
        sample_organization, "test@example.com"
    )

    assert customer_id == "cus_existing123"


@patch("lilypad.server.services.billing.stripe")
def test_create_customer_stripe_error(
    mock_stripe,
    billing_service,
    mock_session,
    sample_organization,
):
    """Test customer creation handles Stripe errors."""
    mock_stripe.api_key = "test_key"

    # Mock no existing billing
    mock_result = Mock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    # Mock Stripe error
    mock_stripe.Customer.create.side_effect = stripe.StripeError("Stripe error")

    with pytest.raises(HTTPException) as exc_info:
        billing_service.create_customer(sample_organization, "test@example.com")

    assert exc_info.value.status_code == 500


@patch("lilypad.server.services.billing.stripe")
def test_create_customer_update_existing_billing(
    mock_stripe,
    billing_service,
    mock_session,
    sample_organization,
):
    """Test updating existing billing record with customer ID."""
    mock_stripe.api_key = "test_key"

    # Mock existing billing without customer ID
    mock_billing = Mock(spec=BillingTable)
    mock_billing.stripe_customer_id = None

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    # Mock Stripe customer creation
    mock_customer = Mock()
    mock_customer.id = "cus_new123"
    mock_stripe.Customer.create.return_value = mock_customer

    customer_id = billing_service.create_customer(
        sample_organization, "test@example.com"
    )

    assert customer_id == "cus_new123"
    assert mock_billing.stripe_customer_id == "cus_new123"
    assert mock_billing.subscription_status == SubscriptionStatus.ACTIVE


@patch("lilypad.server.services.billing.stripe")
def test_get_customer_success(mock_stripe, billing_service):
    """Test successful customer retrieval."""
    mock_stripe.api_key = "test_key"
    customer_id = "cus_test123"

    # Mock Stripe customer
    mock_customer = Mock()
    mock_customer.id = customer_id
    mock_stripe.Customer.retrieve.return_value = mock_customer

    customer = billing_service.get_customer(customer_id)

    assert customer.id == customer_id
    mock_stripe.Customer.retrieve.assert_called_once_with(customer_id)


@patch("lilypad.server.services.billing.stripe")
def test_get_customer_no_api_key(mock_stripe, billing_service):
    """Test get_customer raises exception when no API key."""
    mock_stripe.api_key = None

    with pytest.raises(HTTPException) as exc_info:
        billing_service.get_customer("cus_test123")

    assert exc_info.value.status_code == 500
    assert "Stripe API key not configured" in str(exc_info.value.detail)


@patch("lilypad.server.services.billing.stripe")
def test_get_customer_invalid_customer(mock_stripe, billing_service):
    """Test get_customer handles invalid customer ID."""
    mock_stripe.api_key = "test_key"
    customer_id = "cus_invalid"

    # Mock Stripe error
    mock_stripe.Customer.retrieve.side_effect = stripe.InvalidRequestError(
        "No such customer", param="id"
    )

    result = billing_service.get_customer(customer_id)
    assert result is None


@patch("lilypad.server.services.billing.stripe")
def test_get_customer_stripe_error(mock_stripe, billing_service):
    """Test get_customer handles general Stripe errors."""
    mock_stripe.api_key = "test_key"

    # Mock general Stripe error
    mock_stripe.Customer.retrieve.side_effect = stripe.StripeError("Network error")

    with pytest.raises(HTTPException) as exc_info:
        billing_service.get_customer("cus_test123")

    assert exc_info.value.status_code == 500
    assert "Error retrieving Stripe customer" in str(exc_info.value.detail)


@patch("lilypad.server.services.billing.stripe")
def test_delete_customer_and_billing_success(
    mock_stripe, billing_service, mock_session
):
    """Test successful customer and billing deletion."""
    mock_stripe.api_key = "test_key"
    org_uuid = uuid.uuid4()

    # Mock existing billing
    mock_billing = Mock(spec=BillingTable)
    mock_billing.stripe_customer_id = "cus_test123"

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    billing_service.delete_customer_and_billing(org_uuid)

    mock_stripe.Customer.delete.assert_called_once_with("cus_test123")
    mock_session.delete.assert_called_once_with(mock_billing)
    mock_session.commit.assert_called_once()


@patch("lilypad.server.services.billing.stripe")
def test_delete_customer_and_billing_no_billing(
    mock_stripe, billing_service, mock_session
):
    """Test delete_customer_and_billing when no billing record."""
    mock_stripe.api_key = "test_key"
    org_uuid = uuid.uuid4()

    # Mock no billing record
    mock_result = Mock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    with pytest.raises(_CustomerNotFound):
        billing_service.delete_customer_and_billing(org_uuid)


@patch("lilypad.server.services.billing.stripe")
def test_update_customer_success(mock_stripe, billing_service):
    """Test successful customer update."""
    mock_stripe.api_key = "test_key"
    customer_id = "cus_test123"
    new_name = "Updated Organization"

    # Mock Stripe customer
    mock_customer = Mock()
    mock_customer.id = customer_id
    mock_customer.name = new_name
    mock_stripe.Customer.modify.return_value = mock_customer

    result = billing_service.update_customer(customer_id, new_name)

    assert result.id == customer_id
    assert result.name == new_name
    mock_stripe.Customer.modify.assert_called_once_with(customer_id, name=new_name)


@patch("lilypad.server.services.billing.stripe")
def test_update_customer_invalid_customer(mock_stripe, billing_service):
    """Test update_customer handles invalid customer ID."""
    mock_stripe.api_key = "test_key"

    # Mock Stripe error
    mock_stripe.Customer.modify.side_effect = stripe.InvalidRequestError(
        "No such customer", param="id"
    )

    result = billing_service.update_customer("cus_invalid", "New Name")
    assert result is None


@patch("lilypad.server.services.billing.stripe")
def test_report_span_usage_success(mock_stripe, billing_service, mock_session):
    """Test successful span usage reporting."""
    mock_stripe.api_key = "test_key"
    org_uuid = uuid.uuid4()
    quantity = 5

    # Mock organization with billing
    mock_org = Mock(spec=OrganizationTable)
    mock_org.uuid = org_uuid
    mock_org.billing = Mock()
    mock_org.billing.stripe_customer_id = "cus_test123"

    mock_result = Mock()
    mock_result.first.return_value = mock_org
    mock_session.exec.return_value = mock_result

    # Mock billing record
    mock_billing = Mock(spec=BillingTable)
    mock_billing.uuid = uuid.uuid4()
    mock_billing.usage_quantity = 10

    # Set up mock for second exec call
    mock_session.exec.side_effect = [mock_result, mock_result]
    mock_result.first.side_effect = [mock_org, mock_billing]

    billing_service.report_span_usage(org_uuid, quantity)

    mock_stripe.billing.MeterEvent.create.assert_called_once()
    call_args = mock_stripe.billing.MeterEvent.create.call_args
    assert call_args[1]["event_name"] == "spans"
    assert call_args[1]["payload"]["value"] == str(quantity)


@patch("lilypad.server.services.billing.stripe")
def test_report_span_usage_no_api_key(mock_stripe, billing_service):
    """Test report_span_usage skips when no API key."""
    mock_stripe.api_key = None

    # Should return None without raising exception
    result = billing_service.report_span_usage(uuid.uuid4(), 1)
    assert result is None


@patch("lilypad.server.services.billing.stripe")
def test_report_span_usage_no_organization(mock_stripe, billing_service, mock_session):
    """Test report_span_usage when organization not found."""
    mock_stripe.api_key = "test_key"

    # Mock no organization found
    mock_result = Mock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    with pytest.raises(HTTPException) as exc_info:
        billing_service.report_span_usage(uuid.uuid4(), 1)

    assert exc_info.value.status_code == 404


def test_find_by_subscription_id(mock_session):
    """Test finding billing by subscription ID."""
    subscription_id = "sub_test123"
    mock_billing = Mock(spec=BillingTable)

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    result = BillingService.find_by_subscription_id(mock_session, subscription_id)
    assert result == mock_billing


def test_find_by_customer_id(mock_session):
    """Test finding billing by customer ID."""
    customer_id = "cus_test123"
    mock_billing = Mock(spec=BillingTable)

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    result = BillingService.find_by_customer_id(mock_session, customer_id)
    assert result == mock_billing


def test_find_by_customer_id_none(mock_session):
    """Test finding billing with None customer ID."""
    result = BillingService.find_by_customer_id(mock_session, None)
    assert result is None


def test_update_billing(mock_session):
    """Test updating billing information."""
    subscription = Mock()
    subscription.id = "sub_test123"
    subscription.customer = "cus_test123"

    mock_billing = Mock(spec=BillingTable)
    mock_billing.sqlmodel_update = Mock()

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    data = {"stripe_price_id": "price_test123"}

    result = BillingService.update_billing(mock_session, subscription, data)

    assert result == mock_billing
    mock_billing.sqlmodel_update.assert_called_once_with(data)
    mock_session.add.assert_called_once_with(mock_billing)
    mock_session.flush.assert_called_once()


def test_update_from_subscription(mock_session):
    """Test updating billing from subscription object."""
    # Create subscription mock with proper attributes
    subscription = Mock()
    subscription.id = "sub_test123"
    subscription.customer = "cus_test123"
    subscription.status = "active"
    subscription.current_period_start = 1234567890
    subscription.current_period_end = 1234567890
    subscription.cancel_at_period_end = False

    # Mock items
    items = Mock()
    items.data = [Mock()]
    items.data[0].price = Mock()
    items.data[0].price.id = "price_test123"
    subscription.items = items

    mock_billing = Mock(spec=BillingTable)
    mock_billing.stripe_customer_id = None

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    result = BillingService.update_from_subscription(mock_session, subscription)

    assert result == mock_billing
    assert mock_billing.stripe_subscription_id == "sub_test123"
    assert mock_billing.stripe_customer_id == "cus_test123"
    assert mock_billing.subscription_status == SubscriptionStatus.ACTIVE
    assert mock_billing.stripe_price_id == "price_test123"
    mock_session.add.assert_called_once_with(mock_billing)
    mock_session.commit.assert_called_once()


def test_update_from_subscription_invalid_status(mock_session):
    """Test update_from_subscription with invalid subscription status."""
    subscription = Mock()
    subscription.id = "sub_test123"
    subscription.customer = "cus_test123"
    subscription.status = "invalid_status"
    subscription.current_period_start = 1234567890
    subscription.current_period_end = 1234567890
    subscription.cancel_at_period_end = False
    subscription.items = Mock()
    subscription.items.data = []

    mock_billing = Mock(spec=BillingTable)
    mock_billing.stripe_customer_id = None

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    with patch("lilypad.server.services.billing.logger") as mock_logger:
        result = BillingService.update_from_subscription(mock_session, subscription)

        assert result == mock_billing
        assert mock_billing.subscription_status is None
        mock_logger.warning.assert_called_once()


# Additional tests to achieve 100% coverage for missing lines 107-108, 126, 142-148, 166, 177, 181-182, 235, 310, 334

@patch("lilypad.server.services.billing.stripe")
def test_create_customer_with_organization_billing_update(
    mock_stripe, billing_service, mock_session
):
    """Test create_customer updates organization billing (lines 107-108)."""
    mock_stripe.api_key = "test_key"

    # Create a proper organization mock
    from lilypad.server.models.billing import BillingTable
    mock_org = Mock()
    mock_org.uuid = uuid.uuid4()
    mock_org.name = "Test Organization"
    mock_org.billing = Mock(spec=BillingTable)
    mock_org.billing.stripe_customer_id = None

    # Mock no existing billing in first query
    mock_result = Mock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    # Mock Stripe customer creation
    mock_customer = Mock()
    mock_customer.id = "cus_test123"
    mock_stripe.Customer.create.return_value = mock_customer

    # Mock create_record method
    with patch.object(billing_service, "create_record") as mock_create_record:
        mock_create_record.return_value = Mock(uuid=uuid.uuid4())

        customer_id = billing_service.create_customer(
            mock_org, "test@example.com"
        )

        assert customer_id == "cus_test123"
        # Organization billing should be updated
        assert mock_org.billing.stripe_customer_id == "cus_test123"
        mock_session.add.assert_called()


@patch("lilypad.server.services.billing.stripe")
def test_delete_customer_and_billing_no_api_key(mock_stripe, billing_service):
    """Test delete_customer_and_billing when no API key configured (line 126)."""
    mock_stripe.api_key = None

    with pytest.raises(HTTPException) as exc_info:
        billing_service.delete_customer_and_billing(uuid.uuid4())

    assert exc_info.value.status_code == 500
    assert "Stripe API key not configured" in str(exc_info.value.detail)


@patch("lilypad.server.services.billing.stripe")
def test_delete_customer_and_billing_invalid_request_error(
    mock_stripe, billing_service, mock_session
):
    """Test delete_customer_and_billing handles InvalidRequestError (lines 142-148)."""
    mock_stripe.api_key = "test_key"
    org_uuid = uuid.uuid4()

    # Mock existing billing
    mock_billing = Mock(spec=BillingTable)
    mock_billing.stripe_customer_id = "cus_test123"

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    # Mock Stripe InvalidRequestError
    mock_stripe.Customer.delete.side_effect = stripe.InvalidRequestError(
        "No such customer", param="id"
    )

    with pytest.raises(HTTPException) as exc_info:
        billing_service.delete_customer_and_billing(org_uuid)

    assert exc_info.value.status_code == 404
    assert "Stripe customer not found" in str(exc_info.value.detail)


@patch("lilypad.server.services.billing.stripe")
def test_update_customer_no_api_key(mock_stripe, billing_service):
    """Test update_customer when no API key configured (line 166)."""
    mock_stripe.api_key = None

    with pytest.raises(HTTPException) as exc_info:
        billing_service.update_customer("cus_test123", "New Name")

    assert exc_info.value.status_code == 500
    assert "Stripe API key not configured" in str(exc_info.value.detail)


@patch("lilypad.server.services.billing.stripe")
def test_update_customer_none_result_error(mock_stripe, billing_service):
    """Test update_customer when customer is None (line 177)."""
    mock_stripe.api_key = "test_key"

    # Mock Stripe customer modify returning None
    mock_stripe.Customer.modify.return_value = None

    with pytest.raises(_CustomerNotFound):
        billing_service.update_customer("cus_test123", "New Name")


@patch("lilypad.server.services.billing.stripe")
def test_update_customer_stripe_error(mock_stripe, billing_service):
    """Test update_customer handles general StripeError (lines 181-182)."""
    mock_stripe.api_key = "test_key"

    # Mock general Stripe error
    mock_stripe.Customer.modify.side_effect = stripe.StripeError("Network error")

    with pytest.raises(HTTPException) as exc_info:
        billing_service.update_customer("cus_test123", "New Name")

    assert exc_info.value.status_code == 500
    assert "Error updating Stripe customer" in str(exc_info.value.detail)


@patch("lilypad.server.services.billing.stripe")
def test_report_span_usage_customer_not_found(mock_stripe, billing_service, mock_session):
    """Test report_span_usage when organization has no billing customer (line 235)."""
    mock_stripe.api_key = "test_key"
    org_uuid = uuid.uuid4()

    # Mock organization without billing
    mock_org = Mock(spec=OrganizationTable)
    mock_org.uuid = org_uuid
    mock_org.billing = None

    mock_result = Mock()
    mock_result.first.return_value = mock_org
    mock_session.exec.return_value = mock_result

    with pytest.raises(_CustomerNotFound):
        billing_service.report_span_usage(org_uuid, 5)


@patch("lilypad.server.services.billing.stripe")
def test_delete_customer_and_billing_general_stripe_error(
    mock_stripe, billing_service, mock_session
):
    """Test delete_customer_and_billing handles general StripeError (lines 147-148)."""
    mock_stripe.api_key = "test_key"
    org_uuid = uuid.uuid4()

    # Mock existing billing
    mock_billing = Mock(spec=BillingTable)
    mock_billing.stripe_customer_id = "cus_test123"

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    # Mock general Stripe error (not InvalidRequestError)
    mock_stripe.Customer.delete.side_effect = stripe.StripeError("Network error")

    with pytest.raises(HTTPException) as exc_info:
        billing_service.delete_customer_and_billing(org_uuid)

    assert exc_info.value.status_code == 500
    assert "Error deleting Stripe customer" in str(exc_info.value.detail)


def test_update_billing_no_billing_found(mock_session):
    """Test update_billing when no billing record found (line 310)."""
    subscription = Mock()
    subscription.id = "sub_test123"
    subscription.customer = "cus_test123"

    # Mock no billing record found for both find methods
    mock_result = Mock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    data = {"stripe_price_id": "price_test123"}
    result = BillingService.update_billing(mock_session, subscription, data)

    assert result is None


def test_update_from_subscription_dict_attribute(mock_session):
    """Test update_from_subscription with dict nested objects to trigger _get dict branch (line 327)."""
    # Create a mock subscription object that has nested dict items
    subscription = Mock()
    subscription.id = "sub_test123"
    subscription.customer = "cus_test123"
    subscription.status = "active"
    subscription.current_period_start = 1234567890
    subscription.current_period_end = 1234567999
    subscription.cancel_at_period_end = False
    
    # The key is to make items.data contain dict objects to trigger _get dict branch
    subscription.items = {"data": [{"price": {"id": "price_test123"}}]}  # dict instead of Mock

    mock_billing = Mock(spec=BillingTable)
    mock_billing.stripe_customer_id = None

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    result = BillingService.update_from_subscription(mock_session, subscription)

    assert result == mock_billing
    assert mock_billing.stripe_subscription_id == "sub_test123"
    assert mock_billing.stripe_customer_id == "cus_test123"
    assert mock_billing.stripe_price_id == "price_test123"


def test_update_from_subscription_cancel_at_period_end(mock_session):
    """Test update_from_subscription with cancel_at_period_end True (line 359)."""
    subscription = Mock()
    subscription.id = "sub_test123"
    subscription.customer = "cus_test123"
    subscription.status = "active"
    subscription.current_period_start = 1234567890
    subscription.current_period_end = 1234567999
    subscription.cancel_at_period_end = True  # This should trigger line 359
    subscription.items = Mock()
    subscription.items.data = []

    mock_billing = Mock(spec=BillingTable)
    mock_billing.stripe_customer_id = None

    mock_result = Mock()
    mock_result.first.return_value = mock_billing
    mock_session.exec.return_value = mock_result

    result = BillingService.update_from_subscription(mock_session, subscription)

    assert result == mock_billing
    assert mock_billing.cancel_at_period_end is True


def test_update_from_subscription_no_billing_found(mock_session):
    """Test update_from_subscription when no billing record found (line 334)."""
    subscription = Mock()
    subscription.id = "sub_test123"
    subscription.customer = "cus_test123"

    # Mock no billing record found for both find methods
    mock_result = Mock()
    mock_result.first.return_value = None
    mock_session.exec.return_value = mock_result

    result = BillingService.update_from_subscription(mock_session, subscription)

    assert result is None
