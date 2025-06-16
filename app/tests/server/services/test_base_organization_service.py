"""Tests for base organization service."""

from uuid import uuid4

import pytest
from pydantic import BaseModel
from sqlmodel import Session

from lilypad.server.models.projects import ProjectTable
from lilypad.server.services.base_organization import BaseOrganizationService


class MockCreateModel(BaseModel):
    """Mock create model for testing."""

    name: str


class TestableBaseOrganizationService(
    BaseOrganizationService[ProjectTable, MockCreateModel]
):
    """Testable implementation of BaseOrganizationService."""

    table = ProjectTable
    create_model = MockCreateModel


@pytest.fixture
def org_service(db_session: Session, test_user) -> TestableBaseOrganizationService:
    """Create a testable base organization service instance."""
    return TestableBaseOrganizationService(session=db_session, user=test_user)


# ===== Parameterized Tests for find_record_by_uuid with Organization Filter =====


@pytest.mark.parametrize(
    "use_correct_org,should_succeed",
    [
        (True, True),  # Correct organization
        (False, False),  # Wrong organization
    ],
)
def test_find_record_by_uuid_with_organization_filter(
    org_service, test_project: ProjectTable, use_correct_org, should_succeed
):
    """Test find_record_by_uuid applies organization filter automatically."""
    if use_correct_org:
        # Find existing record (should use user's organization automatically)
        found_project = org_service.find_record_by_uuid(test_project.uuid)
        assert found_project.uuid == test_project.uuid
        assert (
            found_project.organization_uuid == org_service.user.active_organization_uuid
        )

        # Test with explicit organization_uuid filter
        found_project_explicit = org_service.find_record_by_uuid(
            test_project.uuid,
            organization_uuid=org_service.user.active_organization_uuid,
        )
        assert found_project_explicit.uuid == test_project.uuid
    else:
        # Try to find record with wrong organization UUID
        wrong_org_uuid = uuid4()
        with pytest.raises(Exception):  # noqa: B017
            org_service.find_record_by_uuid(
                test_project.uuid, organization_uuid=wrong_org_uuid
            )


# ===== Parameterized Tests for find_all_records with Organization Filter =====


@pytest.mark.parametrize(
    "org_filter,additional_filter,expected_min_count",
    [
        ("user_org", None, 1),  # User's organization, no filter
        ("user_org", "name", 1),  # User's organization with name filter
        ("wrong_org", None, 0),  # Wrong organization
        ("explicit_user_org", None, 1),  # Explicit correct organization
    ],
)
def test_find_all_records_with_organization_filter(
    org_service,
    test_project: ProjectTable,
    org_filter,
    additional_filter,
    expected_min_count,
):
    """Test find_all_records applies organization filter automatically."""
    kwargs = {}

    if org_filter == "wrong_org":
        kwargs["organization_uuid"] = uuid4()
    elif org_filter == "explicit_user_org":
        kwargs["organization_uuid"] = org_service.user.active_organization_uuid

    if additional_filter == "name":
        kwargs["name"] = test_project.name

    # Find records
    projects = org_service.find_all_records(**kwargs)

    assert len(projects) >= expected_min_count

    if expected_min_count > 0:
        # All returned projects should belong to the correct organization
        for project in projects:
            assert (
                project.organization_uuid == org_service.user.active_organization_uuid
            )

        # Check specific filters
        if additional_filter == "name":
            assert all(p.name == test_project.name for p in projects)


# ===== Parameterized Tests for create_record with Organization =====


@pytest.mark.parametrize(
    "explicit_org,project_name",
    [
        (None, "test_project_auto"),  # Automatic organization
        ("user_org", "test_project_explicit"),  # Explicit user organization
        ("custom_org", "test_project_custom"),  # Custom organization UUID
    ],
)
def test_create_record_with_organization(org_service, explicit_org, project_name):
    """Test create_record with various organization settings."""
    create_data = MockCreateModel(name=project_name)
    kwargs = {}

    expected_org_uuid = org_service.user.active_organization_uuid

    if explicit_org == "user_org":
        kwargs["organization_uuid"] = org_service.user.active_organization_uuid
    elif explicit_org == "custom_org":
        custom_uuid = uuid4()
        kwargs["organization_uuid"] = custom_uuid
        expected_org_uuid = custom_uuid

    # Create new record
    new_project = org_service.create_record(create_data, **kwargs)

    assert new_project.name == project_name
    assert new_project.organization_uuid == expected_org_uuid
    assert new_project.uuid is not None


# ===== Tests for Organization Filter Popping Behavior =====


def test_organization_filters_pop_behavior(org_service):
    """Test that organization_uuid is properly popped from filters."""
    # Test find_record_by_uuid - organization_uuid should be popped
    create_data = MockCreateModel(name="test_pop_behavior")
    created_project = org_service.create_record(create_data)

    # The organization_uuid should be popped and not passed to super().find_record_by_uuid
    found_project = org_service.find_record_by_uuid(created_project.uuid)
    assert found_project.uuid == created_project.uuid

    # Test find_all_records - organization_uuid should be popped
    all_projects = org_service.find_all_records()
    assert len(all_projects) >= 1

    # Test create_record - organization_uuid should be popped from kwargs
    another_project = org_service.create_record(MockCreateModel(name="test_pop_create"))
    assert (
        another_project.organization_uuid == org_service.user.active_organization_uuid
    )


# ===== Inheritance Tests =====


@pytest.mark.parametrize(
    "method_name,has_method",
    [
        ("find_record", True),
        ("find_records_by_uuids", True),
        ("delete_record_by_uuid", True),
        ("update_record_by_uuid", True),
        ("find_all_records", True),
        ("create_record", True),
    ],
)
def test_base_organization_service_inheritance(org_service, method_name, has_method):
    """Test that BaseOrganizationService properly inherits from BaseService."""
    # Should have inherited methods
    assert hasattr(org_service, method_name) == has_method

    # Should have all BaseService attributes
    assert hasattr(org_service, "session")
    assert hasattr(org_service, "user")
    assert hasattr(org_service, "table")
    assert hasattr(org_service, "create_model")


def test_inherited_methods_functionality(org_service):
    """Test that inherited methods work correctly with organization filtering."""
    # Create a test project
    create_data = MockCreateModel(name="test_inheritance")
    created_project = org_service.create_record(create_data)

    # Test inherited find_record method (without organization filter)
    found_by_name = org_service.find_record(name="test_inheritance")
    assert found_by_name is not None
    assert found_by_name.uuid == created_project.uuid

    # Test that organization filtering is still applied
    assert found_by_name.organization_uuid == org_service.user.active_organization_uuid


# ===== Edge Cases =====


@pytest.mark.parametrize(
    "scenario,expected_behavior",
    [
        ("empty_uuids_set", "returns_empty_list"),
        ("none_org_uuid", "uses_user_org"),
    ],
)
def test_edge_cases(org_service, scenario, expected_behavior):
    """Test edge cases for organization service."""
    if scenario == "empty_uuids_set":
        # Test find_records_by_uuids with empty set
        results = org_service.find_records_by_uuids(set())
        assert len(results) == 0

    elif scenario == "none_org_uuid":
        # Test that when no organization_uuid is provided, it uses user's organization
        create_data = MockCreateModel(name="test_none_org")
        project = org_service.create_record(create_data)
        assert project.organization_uuid == org_service.user.active_organization_uuid
