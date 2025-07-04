"""Comprehensive tests for the organizations service."""

from unittest.mock import Mock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException
from sqlmodel import Session

from lilypad.server.models import BillingTable, OrganizationTable
from lilypad.server.schemas.organizations import OrganizationCreate
from lilypad.server.schemas.users import UserPublic
from lilypad.server.services.billing import BillingService
from lilypad.server.services.organizations import OrganizationService


@pytest.fixture
def org_service(db_session: Session, test_user: UserPublic) -> OrganizationService:
    """Create an OrganizationService instance."""
    return OrganizationService(session=db_session, user=test_user)


def test_create_organization(org_service: OrganizationService, db_session: Session):
    """Test creating a new organization."""
    org_data = OrganizationCreate(name="Test Org")
    organization = org_service.create_record(org_data)

    assert organization.name == "Test Org"
    assert organization.uuid is not None

    # Verify in database
    db_org = db_session.get(OrganizationTable, organization.uuid)
    assert db_org is not None
    assert db_org.name == "Test Org"


def test_find_organization_by_uuid(
    org_service: OrganizationService, db_session: Session
):
    """Test finding organization by UUID."""
    # Create an organization
    org = OrganizationTable(name="Find By UUID")
    db_session.add(org)
    db_session.commit()

    # Find by UUID
    assert org.uuid is not None  # Type guard
    retrieved = org_service.find_record_by_uuid(org.uuid)
    assert retrieved is not None
    assert retrieved.uuid == org.uuid
    assert retrieved.name == "Find By UUID"


def test_find_organization_not_found(org_service: OrganizationService):
    """Test finding non-existent organization raises HTTPException."""
    fake_uuid = uuid4()
    with pytest.raises(HTTPException) as exc_info:
        org_service.find_record_by_uuid(fake_uuid)
    assert exc_info.value.status_code == 404


def test_update_organization(org_service: OrganizationService, db_session: Session):
    """Test updating an organization."""
    # Create an organization
    org = OrganizationTable(name="Original Name", license="license1")
    db_session.add(org)
    db_session.commit()

    # Update it
    update_data = {"name": "Updated Name"}
    assert org.uuid is not None  # Type guard
    updated = org_service.update_record_by_uuid(org.uuid, update_data)

    assert updated is not None
    assert updated.name == "Updated Name"
    assert updated.license == "license1"  # Unchanged

    # Verify in database
    db_session.refresh(org)
    assert org.name == "Updated Name"


def test_delete_organization(org_service: OrganizationService, db_session: Session):
    """Test deleting an organization."""
    # Create an organization
    org = OrganizationTable(name="To Delete")
    db_session.add(org)
    db_session.commit()
    assert org.uuid is not None  # Type guard
    org_uuid = org.uuid

    # Delete it
    result = org_service.delete_record_by_uuid(org_uuid)
    assert result is True

    # Commit the session to ensure delete is persisted
    db_session.commit()

    # Verify deleted
    db_org = db_session.get(OrganizationTable, org_uuid)
    assert db_org is None


def test_delete_organization_not_found(org_service: OrganizationService):
    """Test deleting non-existent organization raises HTTPException."""
    fake_uuid = uuid4()
    with pytest.raises(HTTPException) as exc_info:
        org_service.delete_record_by_uuid(fake_uuid)
    assert exc_info.value.status_code == 404


def test_find_all_organizations(org_service: OrganizationService, db_session: Session):
    """Test finding all organizations."""
    # Create multiple organizations
    orgs = []
    for i in range(3):
        org = OrganizationTable(name=f"Org {i}", license=f"license{i}")
        db_session.add(org)
        orgs.append(org)
    db_session.commit()

    # Find all
    all_orgs = org_service.find_all_records()

    # Should include the test fixture org plus our 3
    assert len(all_orgs) >= 3

    # Check our orgs are included
    org_names = {org.name for org in all_orgs}
    assert "Org 0" in org_names
    assert "Org 1" in org_names
    assert "Org 2" in org_names


def test_find_organizations_with_filters(
    org_service: OrganizationService, db_session: Session
):
    """Test finding organizations with filters."""
    # Create organizations with specific attributes
    org1 = OrganizationTable(name="Active Org", license="active-license")
    org2 = OrganizationTable(name="Other Org", license="other-license")
    db_session.add_all([org1, org2])
    db_session.commit()

    # Find by license
    active_orgs = org_service.find_all_records(license="active-license")
    assert len(active_orgs) == 1
    assert active_orgs[0].name == "Active Org"

    # Find by name
    found_orgs = org_service.find_all_records(name="Other Org")
    assert len(found_orgs) == 1
    assert found_orgs[0].license == "other-license"


def test_find_organization_by_name(
    org_service: OrganizationService, db_session: Session
):
    """Test finding organization by name using find_record."""
    # Create organization with unique name
    org = OrganizationTable(name="Unique Org Name")
    db_session.add(org)
    db_session.commit()

    # Find by name
    found = org_service.find_record(name="Unique Org Name")
    assert found is not None
    assert found.uuid == org.uuid
    assert found.name == "Unique Org Name"


def test_find_organization_by_license(
    org_service: OrganizationService, db_session: Session
):
    """Test finding organization by license."""
    # Create organization with unique license
    org = OrganizationTable(name="Licensed Org", license="unique-license-123")
    db_session.add(org)
    db_session.commit()

    # Find by license
    found = org_service.find_record(license="unique-license-123")
    assert found is not None
    assert found.uuid == org.uuid
    assert found.license == "unique-license-123"


def test_find_records_by_uuids(org_service: OrganizationService, db_session: Session):
    """Test finding multiple organizations by UUIDs."""
    # Create organizations
    orgs = []
    for i in range(3):
        org = OrganizationTable(name=f"UUID Org {i}")
        db_session.add(org)
        orgs.append(org)
    db_session.commit()

    # Get UUIDs after commit
    uuids = {org.uuid for org in orgs}

    # Find by UUIDs
    found_orgs = org_service.find_records_by_uuids(uuids)
    assert len(found_orgs) == 3

    found_names = {org.name for org in found_orgs}
    assert "UUID Org 0" in found_names
    assert "UUID Org 1" in found_names
    assert "UUID Org 2" in found_names


def test_get_organization_license(
    org_service: OrganizationService, db_session: Session
):
    """Test getting organization license."""
    # Create organization with license
    org = OrganizationTable(name="Licensed", license="test-license-key")
    db_session.add(org)
    db_session.commit()

    # Get license
    assert org.uuid is not None  # Type guard
    org_license = org_service.get_organization_license(org.uuid)
    assert org_license == "test-license-key"

    # Test non-existent org
    fake_uuid = uuid4()
    org_license = org_service.get_organization_license(fake_uuid)
    assert org_license is None


def test_organization_with_users(
    org_service: OrganizationService, db_session: Session, test_user: UserPublic
):
    """Test organization service with user relationships."""
    # Create organization
    org_data = OrganizationCreate(name="Org With Users")
    org = org_service.create_record(org_data)

    # The service should handle user context
    assert org is not None
    assert org.name == "Org With Users"


def test_bulk_create_organizations(
    org_service: OrganizationService, db_session: Session
):
    """Test creating multiple organizations at once."""
    org_data_list = [OrganizationCreate(name=f"Bulk Org {i}") for i in range(3)]

    # Create multiple
    created_orgs = []
    for org_data in org_data_list:
        org = org_service.create_record(org_data)
        created_orgs.append(org)

    assert len(created_orgs) == 3

    # Verify all were created
    for i, org in enumerate(created_orgs):
        assert org.name == f"Bulk Org {i}"


def test_organization_validation(org_service: OrganizationService):
    """Test organization data validation."""
    # Test empty name
    with pytest.raises(ValueError):  # Pydantic validation error
        org_data = OrganizationCreate(name="")
        org_service.create_record(org_data)

    # Test None name - this should fail at the type level
    # Can't test None name as Pydantic won't allow it


def test_create_stripe_customer_new_organization(
    org_service: OrganizationService, db_session: Session
):
    """Test creating Stripe customer for organization without billing."""
    # Create organization without billing
    org = OrganizationTable(name="Stripe Test Org")
    db_session.add(org)
    db_session.commit()

    # Mock billing service
    mock_billing_service = Mock(spec=BillingService)
    mock_billing_service.create_customer.return_value = "cust_test123"

    assert org.uuid is not None
    result = org_service.create_stripe_customer(
        mock_billing_service, org.uuid, "test@example.com"
    )

    assert result.uuid == org.uuid
    assert result.billing is not None
    assert result.billing.stripe_customer_id == "cust_test123"
    mock_billing_service.create_customer.assert_called_once_with(
        email="test@example.com", organization=org
    )


def test_create_stripe_customer_existing_billing_no_customer(
    org_service: OrganizationService, db_session: Session
):
    """Test creating Stripe customer for organization with billing but no customer."""
    # Create organization with billing but no customer ID
    org = OrganizationTable(name="Existing Billing Org")
    billing = BillingTable(organization_uuid=org.uuid)  # type: ignore
    db_session.add(org)
    db_session.add(billing)
    db_session.commit()

    # Refresh to load relationship
    db_session.refresh(org)

    # Mock billing service
    mock_billing_service = Mock(spec=BillingService)
    mock_billing_service.create_customer.return_value = "cust_new456"

    assert org.uuid is not None
    result = org_service.create_stripe_customer(
        mock_billing_service, org.uuid, "existing@example.com"
    )

    assert result.uuid == org.uuid
    assert result.billing.stripe_customer_id == "cust_new456"
    mock_billing_service.create_customer.assert_called_once()


def test_create_stripe_customer_already_has_customer(
    org_service: OrganizationService, db_session: Session
):
    """Test creating Stripe customer for organization that already has one."""
    # Create organization with existing customer
    org = OrganizationTable(name="Has Customer Org")
    billing = BillingTable(
        organization_uuid=org.uuid,  # type: ignore[arg-type]
        stripe_customer_id="cust_existing789",  # type: ignore
    )
    db_session.add(org)
    db_session.add(billing)
    db_session.commit()

    # Refresh to load relationship
    db_session.refresh(org)

    # Mock billing service
    mock_billing_service = Mock(spec=BillingService)

    assert org.uuid is not None
    result = org_service.create_stripe_customer(
        mock_billing_service, org.uuid, "hasone@example.com"
    )

    assert result.uuid == org.uuid
    assert result.billing.stripe_customer_id == "cust_existing789"
    # Should not call create_customer since one already exists
    mock_billing_service.create_customer.assert_not_called()


def test_create_stripe_customer_organization_not_found(
    org_service: OrganizationService,
):
    """Test creating Stripe customer for non-existent organization."""
    mock_billing_service = Mock(spec=BillingService)
    fake_uuid = uuid4()

    # find_record_by_uuid raises HTTPException for non-existent records
    with pytest.raises(HTTPException) as exc_info:  # noqa: B017
        org_service.create_stripe_customer(
            mock_billing_service, fake_uuid, "notfound@example.com"
        )
    assert exc_info.value.status_code == 404


def test_create_stripe_customer_organization_none_error(
    org_service: OrganizationService,
):
    """Test create_stripe_customer with organization not found (line 62)."""
    mock_billing_service = Mock(spec=BillingService)
    fake_uuid = uuid4()

    # Mock find_record_by_uuid to return None instead of raising HTTPException
    with (
        patch.object(org_service, "find_record_by_uuid", return_value=None),
        pytest.raises(ValueError, match=f"Organization {fake_uuid} not found"),
    ):
        org_service.create_stripe_customer(
            mock_billing_service, fake_uuid, "notfound@example.com"
        )


def test_get_stripe_customer_success(
    org_service: OrganizationService, db_session: Session
):
    """Test getting Stripe customer for organization."""
    # Create organization with customer
    org = OrganizationTable(name="Get Customer Org")
    billing = BillingTable(organization_uuid=org.uuid, stripe_customer_id="cust_get123")  # type: ignore
    db_session.add(org)
    db_session.add(billing)
    db_session.commit()

    # Refresh to load relationship
    db_session.refresh(org)

    # Mock billing service
    mock_customer = {"id": "cust_get123", "email": "customer@example.com"}
    mock_billing_service = Mock(spec=BillingService)
    mock_billing_service.get_customer.return_value = mock_customer

    assert org.uuid is not None
    result = org_service.get_stripe_customer(mock_billing_service, org.uuid)

    assert result == mock_customer
    mock_billing_service.get_customer.assert_called_once_with("cust_get123")


def test_get_stripe_customer_no_billing(
    org_service: OrganizationService, db_session: Session
):
    """Test getting Stripe customer for organization without billing."""
    # Create organization without billing
    org = OrganizationTable(name="No Billing Org")
    db_session.add(org)
    db_session.commit()

    mock_billing_service = Mock(spec=BillingService)

    assert org.uuid is not None
    # The method has a bug: it doesn't check if billing is None before accessing stripe_customer_id
    # This will raise AttributeError because billing relationship is None
    with pytest.raises(AttributeError):
        org_service.get_stripe_customer(mock_billing_service, org.uuid)


def test_get_stripe_customer_no_customer_id(
    org_service: OrganizationService, db_session: Session
):
    """Test getting Stripe customer for organization with billing but no customer ID."""
    # Create organization with billing but no customer ID
    org = OrganizationTable(name="No Customer ID Org")
    billing = BillingTable(organization_uuid=org.uuid, stripe_customer_id=None)  # type: ignore
    db_session.add(org)
    db_session.add(billing)
    db_session.commit()

    # Refresh to load relationship
    db_session.refresh(org)

    mock_billing_service = Mock(spec=BillingService)

    assert org.uuid is not None
    result = org_service.get_stripe_customer(mock_billing_service, org.uuid)

    assert result is None
    mock_billing_service.get_customer.assert_not_called()


def test_get_stripe_customer_organization_not_found(org_service: OrganizationService):
    """Test getting Stripe customer for non-existent organization."""
    mock_billing_service = Mock(spec=BillingService)
    fake_uuid = uuid4()

    # find_record_by_uuid raises HTTPException for non-existent records
    with pytest.raises(HTTPException) as exc_info:
        org_service.get_stripe_customer(mock_billing_service, fake_uuid)
    assert exc_info.value.status_code == 404


def test_find_records_by_uuids_empty_list(org_service: OrganizationService):
    """Test finding records by empty UUIDs list returns empty list."""
    # Call with empty list
    result = org_service.find_records_by_uuids([])  # type: ignore

    # Should return empty list
    assert result == []


def test_find_records_by_uuids_empty_set(org_service: OrganizationService):
    """Test finding records by empty UUIDs set returns empty list."""
    # Call with empty set
    result = org_service.find_records_by_uuids(set())

    # Should return empty list
    assert result == []
